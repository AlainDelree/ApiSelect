from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from .calculs import (
    DECALAGES_JOURS_ETAPES,
    MesureIndex,
    calculer_dates_etapes,
    calculer_index,
    calculer_index_colonie,
)
from .gestion_base_test import NOM_RUCHER_TEST
from .models import (
    CampagneElevage,
    Colonie,
    CritereSelection,
    EtapeCalendrier,
    Mesure,
    ModeCreationColonie,
    PoidsCritere,
    Reine,
    Ruche,
    Rucher,
    TypeEtapeCalendrier,
    TypeRuche,
    VueColonieActive,
)


class CalculerIndexTests(TestCase):
    """Tests du calcul de l'index pondéré — données factices, aucune
    dépendance à une base réelle (cf. selection/calculs.py)."""

    def test_index_pondere_simple(self):
        mesures = [
            MesureIndex("Propreté", score=4, poids=5, seuil_eliminatoire=None),
            MesureIndex("Agressivité", score=2, poids=10, seuil_eliminatoire=None),
        ]
        resultat = calculer_index(mesures)
        self.assertFalse(resultat.exclue)
        # (4*5 + 2*10) / (5+10) = 40/15
        self.assertEqual(resultat.index, Decimal(40) / Decimal(15))
        self.assertEqual(resultat.nb_criteres_pris_en_compte, 2)

    def test_seuil_eliminatoire_exclut_la_colonie(self):
        mesures = [
            MesureIndex("Santé", score=1, poids=8, seuil_eliminatoire=Decimal("2")),
            MesureIndex("Propreté", score=4, poids=5, seuil_eliminatoire=None),
        ]
        resultat = calculer_index(mesures)
        self.assertTrue(resultat.exclue)
        self.assertIsNone(resultat.index)
        self.assertIn("Santé", resultat.motif_exclusion)

    def test_score_egal_au_seuil_nest_pas_exclu(self):
        mesures = [
            MesureIndex("Santé", score=2, poids=8, seuil_eliminatoire=Decimal("2")),
        ]
        resultat = calculer_index(mesures)
        self.assertFalse(resultat.exclue)
        self.assertEqual(resultat.index, Decimal(2))

    def test_poids_zero_sans_effet_sur_le_resultat(self):
        avec_poids_zero = calculer_index([
            MesureIndex("Propreté", score=4, poids=5, seuil_eliminatoire=None),
            MesureIndex("Tenue au cadre", score=1, poids=0, seuil_eliminatoire=None),
        ])
        sans_le_critere = calculer_index([
            MesureIndex("Propreté", score=4, poids=5, seuil_eliminatoire=None),
        ])
        self.assertEqual(avec_poids_zero.index, sans_le_critere.index)

    def test_mesure_sans_score_est_ignoree(self):
        resultat = calculer_index([
            MesureIndex("Miel", score=None, poids=5, seuil_eliminatoire=None),
            MesureIndex("Propreté", score=3, poids=5, seuil_eliminatoire=None),
        ])
        self.assertEqual(resultat.index, Decimal(3))
        self.assertEqual(resultat.nb_criteres_pris_en_compte, 1)

    def test_mesure_sans_poids_connu_est_ignoree(self):
        resultat = calculer_index([
            MesureIndex("Critère hors campagne", score=3, poids=None, seuil_eliminatoire=None),
            MesureIndex("Propreté", score=4, poids=5, seuil_eliminatoire=None),
        ])
        self.assertEqual(resultat.index, Decimal(4))
        self.assertEqual(resultat.nb_criteres_pris_en_compte, 1)

    def test_aucune_mesure_exploitable_donne_index_none(self):
        resultat = calculer_index([])
        self.assertFalse(resultat.exclue)
        self.assertIsNone(resultat.index)
        self.assertEqual(resultat.nb_criteres_pris_en_compte, 0)


class VueColonieActiveLibelleTypeRucheTests(TestCase):
    """Vérifie que `ruche_identifiant`, exposé par la vue SQL
    `vue_colonies_actives` (selection/migrations/0004_typeruche_table_alias.py),
    utilise bien l'alias de TypeRuche (ou son nom complet à défaut) — et pas
    seulement côté Python, la jointure étant faite en SQL."""

    def _libelle_pour(self, code_type_ruche, numero):
        type_ruche = TypeRuche.objects.get(code=code_type_ruche)
        ruche = Ruche.objects.create(type_ruche=type_ruche, numero=numero)
        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation="ACHAT", date_creation="2026-01-01",
            active=True,
        )
        return VueColonieActive.objects.get(colonie_id=colonie.id).ruche_identifiant

    def test_libelle_dadant10(self):
        self.assertEqual(self._libelle_pour("DADANT10", 3), "Ruche 3")

    def test_libelle_ruchette6(self):
        self.assertEqual(self._libelle_pour("RUCHETTE6", 7), "Ruchette 7")

    def test_libelle_apidea(self):
        self.assertEqual(self._libelle_pour("APIDEA", 1), "Apidea 1")

    def test_libelle_dh(self):
        self.assertEqual(self._libelle_pour("DH", 2), "DH 2")


class ResultatsSelectionViewTests(TestCase):
    """Tests de la vue `selection:resultats` (issue #6) : tri par index,
    colonies exclues signalées avec leur motif, colonies sans mesure
    gérées proprement, cas sans campagne."""

    def _creer_colonie(self, numero):
        type_ruche = TypeRuche.objects.get(code="DADANT10")
        ruche = Ruche.objects.create(type_ruche=type_ruche, numero=numero)
        return Colonie.objects.create(
            ruche=ruche, mode_creation="ACHAT", date_creation="2026-01-01",
            active=True,
        )

    def setUp(self):
        self.campagne = CampagneElevage.objects.create(nom="Campagne 2026", annee=2026)
        self.critere_sante = CritereSelection.objects.get(code="SANTE")
        self.critere_proprete = CritereSelection.objects.get(code="PROPRETE")

    def test_tri_par_index_decroissant(self):
        PoidsCritere.objects.create(
            campagne=self.campagne, critere=self.critere_proprete, poids=5,
        )
        colonie_haute = self._creer_colonie(1)
        Mesure.objects.create(
            colonie=colonie_haute, critere=self.critere_proprete,
            campagne=self.campagne, date_mesure="2026-05-01",
            valeur_brute="propre", score=4,
        )
        colonie_basse = self._creer_colonie(2)
        Mesure.objects.create(
            colonie=colonie_basse, critere=self.critere_proprete,
            campagne=self.campagne, date_mesure="2026-05-01",
            valeur_brute="sale", score=1,
        )

        response = self.client.get(reverse("selection:resultats"))

        self.assertEqual(response.status_code, 200)
        colonie_ids = [ligne["colonie"].colonie_id for ligne in response.context["lignes"]]
        self.assertEqual(colonie_ids, [colonie_haute.id, colonie_basse.id])
        indices = [ligne["resultat"].index for ligne in response.context["lignes"]]
        self.assertEqual(indices, [Decimal(4), Decimal(1)])

    def test_colonie_exclue_affichee_avec_motif(self):
        PoidsCritere.objects.create(
            campagne=self.campagne, critere=self.critere_sante, poids=8,
            seuil_eliminatoire=Decimal("2"),
        )
        colonie = self._creer_colonie(3)
        Mesure.objects.create(
            colonie=colonie, critere=self.critere_sante,
            campagne=self.campagne, date_mesure="2026-05-01",
            valeur_brute="maladie", score=1,
        )

        response = self.client.get(reverse("selection:resultats"))

        self.assertEqual(response.status_code, 200)
        lignes = response.context["lignes"]
        self.assertEqual(len(lignes), 1)
        self.assertTrue(lignes[0]["resultat"].exclue)
        self.assertIsNone(lignes[0]["resultat"].index)
        self.assertIn("Santé", lignes[0]["resultat"].motif_exclusion)
        self.assertContains(response, "Exclue")
        # Le motif complet contient un "<" (comparaison de seuil), échappé en
        # HTML : on vérifie la partie textuelle qui identifie le critère.
        self.assertContains(response, "Critère « Santé » sous le seuil éliminatoire")

    def test_colonie_sans_mesure_geree_proprement(self):
        colonie = self._creer_colonie(4)

        response = self.client.get(reverse("selection:resultats"))

        self.assertEqual(response.status_code, 200)
        lignes = response.context["lignes"]
        self.assertEqual(len(lignes), 1)
        self.assertFalse(lignes[0]["a_des_mesures"])
        self.assertIsNone(lignes[0]["resultat"].index)
        self.assertContains(response, "Aucune mesure pour cette campagne")
        # Colonnes de critères vides affichées avec un tiret plutôt qu'absentes.
        self.assertTrue(all(score is None for score in lignes[0]["scores_par_critere"]))

    def test_aucune_campagne_message_clair(self):
        CampagneElevage.objects.all().delete()

        response = self.client.get(reverse("selection:resultats"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucune campagne")
        self.assertEqual(list(response.context["campagnes"]), [])


class CalculerDatesEtapesTests(TestCase):
    """Vérifie la cascade de dates contre l'exemple réel du fichier ODS
    source (Cours_Apiculture/calendrier élevage de reine.ods, non
    versionné — cf. rapport de clôture de l'issue #7 pour le détail des
    cellules relevées). Ponte le 5/06/2022 -> picking le 9/06/2022,
    reste de la cascade documentée en commentaire dans calculs.py."""

    def setUp(self):
        self.date_ponte = date(2022, 6, 5)
        self.dates = calculer_dates_etapes(self.date_ponte)

    def test_toutes_les_etapes_du_modele_sont_calculees(self):
        self.assertEqual(set(self.dates), {code for code, _ in TypeEtapeCalendrier.choices})

    def test_picking_quatre_jours_apres_la_ponte(self):
        self.assertEqual(self.dates["PICKING"], date(2022, 6, 9))

    def test_starter_le_meme_jour_que_le_picking(self):
        self.assertEqual(self.dates["STARTER"], self.dates["PICKING"])

    def test_finisseur_un_jour_apres_le_picking(self):
        self.assertEqual(self.dates["FINISSEUR"], date(2022, 6, 10))

    def test_couveuse(self):
        self.assertEqual(self.dates["COUVEUSE"], date(2022, 6, 14))

    def test_peuplement_ruchettes(self):
        self.assertEqual(self.dates["RUCHETTES"], date(2022, 6, 19))

    def test_liberation(self):
        self.assertEqual(self.dates["LIBERATION"], date(2022, 6, 22))

    def test_controle_naissance(self):
        self.assertEqual(self.dates["CONTROLE_NAISSANCE"], date(2022, 6, 24))

    def test_debut_ponte(self):
        self.assertEqual(self.dates["DEBUT_PONTE"], date(2022, 6, 30))

    def test_controle_ponte(self):
        self.assertEqual(self.dates["CONTROLE_PONTE"], date(2022, 7, 1))

    def test_elevage_males_seize_jours_avant_la_ponte(self):
        # Décalage -16j : principe de saturation du cours (CONTEXTE.md),
        # pas une cellule calculée de l'ODS — cf. calculs.py.
        self.assertEqual(self.dates["ELEVAGE_MALES"], self.date_ponte - timedelta(days=16))

    def test_decalages_geles_contre_regression_silencieuse(self):
        # Verrouille les valeurs exactes relevées dans l'ODS : toute
        # modification de DECALAGES_JOURS_ETAPES doit être volontaire.
        self.assertEqual(DECALAGES_JOURS_ETAPES, {
            "ELEVAGE_MALES": -16,
            "PICKING": 4,
            "STARTER": 4,
            "FINISSEUR": 5,
            "COUVEUSE": 9,
            "RUCHETTES": 14,
            "LIBERATION": 17,
            "CONTROLE_NAISSANCE": 19,
            "DEBUT_PONTE": 25,
            "CONTROLE_PONTE": 26,
        })


class RecalculAutomatiqueEtapesTests(TestCase):
    """Vérifie le signal post_save (cf. selection/signals.py) : création
    des étapes à la saisie de date_reference, recalcul si elle change,
    aucune interférence entre campagnes en parallèle, et préservation du
    marquage "réalisée" au recalcul."""

    def test_creation_campagne_avec_date_reference_cree_les_etapes(self):
        campagne = CampagneElevage.objects.create(
            nom="Campagne A", annee=2022, date_reference=date(2022, 6, 5),
        )
        self.assertEqual(campagne.etapes.count(), len(TypeEtapeCalendrier.choices))
        picking = campagne.etapes.get(type_etape=TypeEtapeCalendrier.PICKING)
        self.assertEqual(picking.date_prevue, date(2022, 6, 9))

    def test_campagne_sans_date_reference_ne_cree_aucune_etape(self):
        campagne = CampagneElevage.objects.create(nom="Campagne B", annee=2022)
        self.assertEqual(campagne.etapes.count(), 0)

    def test_modification_date_reference_recalcule_les_etapes(self):
        campagne = CampagneElevage.objects.create(
            nom="Campagne C", annee=2022, date_reference=date(2022, 6, 5),
        )
        campagne.date_reference = date(2022, 7, 5)
        campagne.save()

        picking = campagne.etapes.get(type_etape=TypeEtapeCalendrier.PICKING)
        self.assertEqual(picking.date_prevue, date(2022, 7, 9))
        # Toujours une seule ligne par (campagne, étape), pas de doublon.
        self.assertEqual(campagne.etapes.count(), len(TypeEtapeCalendrier.choices))

    def test_plusieurs_campagnes_en_parallele_sans_interference(self):
        campagne_1 = CampagneElevage.objects.create(
            nom="Lignée 1", annee=2022, date_reference=date(2022, 6, 5),
        )
        campagne_2 = CampagneElevage.objects.create(
            nom="Lignée 2", annee=2022, date_reference=date(2022, 6, 20),
        )

        picking_1 = campagne_1.etapes.get(type_etape=TypeEtapeCalendrier.PICKING)
        picking_2 = campagne_2.etapes.get(type_etape=TypeEtapeCalendrier.PICKING)

        self.assertEqual(picking_1.date_prevue, date(2022, 6, 9))
        self.assertEqual(picking_2.date_prevue, date(2022, 6, 24))
        self.assertEqual(EtapeCalendrier.objects.filter(campagne=campagne_1).count(), 10)
        self.assertEqual(EtapeCalendrier.objects.filter(campagne=campagne_2).count(), 10)

    def test_marquage_realisee_preserve_par_un_recalcul_ulterieur(self):
        campagne = CampagneElevage.objects.create(
            nom="Campagne D", annee=2022, date_reference=date(2022, 6, 5),
        )
        picking = campagne.etapes.get(type_etape=TypeEtapeCalendrier.PICKING)
        picking.realisee = True
        picking.date_reelle = date(2022, 6, 10)
        picking.save()

        # Une sauvegarde ultérieure de la campagne (ex. modif des notes,
        # date_reference inchangée) ne doit pas effacer le marquage.
        campagne.notes = "RAS"
        campagne.save()

        picking.refresh_from_db()
        self.assertTrue(picking.realisee)
        self.assertEqual(picking.date_reelle, date(2022, 6, 10))
        self.assertEqual(picking.date_prevue, date(2022, 6, 9))


class CalendrierEtTachesViewsTests(TestCase):
    """Tests des vues `selection:calendrier` et `selection:taches`
    (issue #7)."""

    def setUp(self):
        self.campagne = CampagneElevage.objects.create(
            nom="Campagne 2022", annee=2022, date_reference=date(2022, 6, 5),
        )

    def test_calendrier_affiche_les_etapes_du_mois(self):
        response = self.client.get(reverse("selection:calendrier"), {"annee": 2022, "mois": 6})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campagne 2022")
        self.assertContains(response, "Picking")

    def test_calendrier_mois_sans_etape_naffiche_rien_de_special(self):
        response = self.client.get(reverse("selection:calendrier"), {"annee": 2023, "mois": 1})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Campagne 2022")

    def test_taches_liste_les_etapes_non_realisees_par_ordre_chronologique(self):
        response = self.client.get(reverse("selection:taches"))

        self.assertEqual(response.status_code, 200)
        etapes = list(response.context["etapes"])
        self.assertEqual(len(etapes), len(TypeEtapeCalendrier.choices))
        dates = [etape.date_prevue for etape in etapes]
        self.assertEqual(dates, sorted(dates))

    def test_taches_exclut_les_etapes_marquees_realisees(self):
        picking = self.campagne.etapes.get(type_etape=TypeEtapeCalendrier.PICKING)
        picking.realisee = True
        picking.save()

        response = self.client.get(reverse("selection:taches"))

        etapes = list(response.context["etapes"])
        self.assertNotIn(picking, etapes)
        self.assertEqual(len(etapes), len(TypeEtapeCalendrier.choices) - 1)


class FichesTerrainPdfTests(TestCase):
    """Tests des fiches de terrain PDF (issue #8) : génération réussie
    (statut 200, content-type PDF), contenu correct de la fiche rapide
    (toutes les colonies actives) et de la fiche approfondie (uniquement
    les colonies sélectionnées dans le formulaire)."""

    def _creer_colonie(self, numero, reine=None, active=True):
        type_ruche = TypeRuche.objects.get(code="DADANT10")
        ruche = Ruche.objects.create(type_ruche=type_ruche, numero=numero)
        return Colonie.objects.create(
            ruche=ruche, mode_creation="ACHAT", date_creation="2026-01-01",
            active=active, reine_actuelle=reine,
        )

    def setUp(self):
        self.campagne = CampagneElevage.objects.create(nom="Campagne 2026", annee=2026)

    def test_fiche_rapide_statut_200_et_content_type_pdf(self):
        self._creer_colonie(1)

        response = self.client.get(reverse("selection:fiche_rapide"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_fiche_rapide_contient_toutes_les_colonies_actives(self):
        colonie_active_1 = self._creer_colonie(1)
        colonie_active_2 = self._creer_colonie(2)
        self._creer_colonie(3, active=False)  # ne doit pas apparaître

        response = self.client.get(reverse("selection:fiche_rapide"))

        colonie_ids = [ligne["colonie"].colonie_id for ligne in response.context["lignes"]]
        self.assertCountEqual(colonie_ids, [colonie_active_1.id, colonie_active_2.id])

    def test_fiche_rapide_utilise_les_criteres_de_la_passe_rapide(self):
        self._creer_colonie(1)

        response = self.client.get(reverse("selection:fiche_rapide"))

        codes = {critere.code for critere in response.context["criteres"]}
        codes_attendus = set(
            CritereSelection.objects.filter(type_mesure="PASSE_RAPIDE")
            .values_list("code", flat=True)
        )
        self.assertEqual(codes, codes_attendus)
        self.assertEqual(len(codes_attendus), 4)

    def test_fiche_rapide_associe_la_lignee_de_la_reine_a_la_bonne_colonie(self):
        reine = Reine.objects.create(
            identifiant="R26-01", lignee_male_probable="Lignée Buckfast",
        )
        colonie_avec_reine = self._creer_colonie(1, reine=reine)
        colonie_sans_reine = self._creer_colonie(2)

        response = self.client.get(reverse("selection:fiche_rapide"))

        lignees = {
            ligne["colonie"].colonie_id: ligne["lignee"]
            for ligne in response.context["lignes"]
        }
        self.assertEqual(lignees[colonie_avec_reine.id], "Lignée Buckfast")
        self.assertEqual(lignees[colonie_sans_reine.id], "")

    def test_formulaire_approfondie_liste_les_colonies_actives(self):
        self._creer_colonie(1)
        self._creer_colonie(2, active=False)

        response = self.client.get(reverse("selection:fiche_approfondie_formulaire"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ruche 1")
        self.assertNotContains(response, "Ruche 2")

    def test_fiche_approfondie_statut_200_et_content_type_pdf(self):
        colonie = self._creer_colonie(1)

        response = self.client.post(
            reverse("selection:fiche_approfondie_pdf"),
            {"campagne": self.campagne.id, "colonies": [colonie.id]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_fiche_approfondie_ne_contient_que_les_colonies_selectionnees(self):
        colonie_incluse = self._creer_colonie(1)
        self._creer_colonie(2)  # active, mais non cochée dans le formulaire

        response = self.client.post(
            reverse("selection:fiche_approfondie_pdf"),
            {"campagne": self.campagne.id, "colonies": [colonie_incluse.id]},
        )

        colonie_ids = [ligne["colonie"].colonie_id for ligne in response.context["lignes"]]
        self.assertEqual(colonie_ids, [colonie_incluse.id])

    def test_fiche_approfondie_utilise_les_criteres_de_la_passe_approfondie(self):
        colonie = self._creer_colonie(1)

        response = self.client.post(
            reverse("selection:fiche_approfondie_pdf"),
            {"campagne": self.campagne.id, "colonies": [colonie.id]},
        )

        codes = {critere.code for critere in response.context["criteres"]}
        codes_attendus = set(
            CritereSelection.objects.filter(type_mesure="PASSE_APPROFONDIE")
            .values_list("code", flat=True)
        )
        self.assertEqual(codes, codes_attendus)
        self.assertEqual(len(codes_attendus), 5)


class ReineAdminAutocompletionAnneeTests(TestCase):
    """Le formulaire admin de Reine charge le script JS d'auto-complétion
    de date_naissance (année seule -> 01/04/AAAA, issue #10). Le
    comportement JS lui-même (évènement blur) n'est pas exécuté par les
    tests Django ; il se vérifie manuellement dans le navigateur (voir
    rapport de l'issue #10)."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="motdepasse",
        )
        self.client.force_login(self.superuser)

    def test_page_ajout_reine_charge_le_script_autocompletion(self):
        response = self.client.get(reverse("admin:selection_reine_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "selection/admin/reine_date_naissance.js")

    def test_page_modification_reine_charge_le_script_autocompletion(self):
        reine = Reine.objects.create(identifiant="R1")

        response = self.client.get(
            reverse("admin:selection_reine_change", args=[reine.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "selection/admin/reine_date_naissance.js")
class ModeCreationColonieFusionTests(TestCase):
    """Vérifie que la colonie accepte "FUSION" comme mode_creation
    (issue #11) : cas d'une colonie née de la fusion de deux colonies
    existantes, indépendamment de l'origine de sa reine actuelle."""

    def test_colonie_acceptee_avec_mode_creation_fusion(self):
        type_ruche = TypeRuche.objects.get(code="DADANT10")
        ruche = Ruche.objects.create(type_ruche=type_ruche, numero=1)

        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.FUSION,
            date_creation="2026-01-01", active=True,
        )
        colonie.full_clean()

        self.assertEqual(colonie.mode_creation, ModeCreationColonie.FUSION)


class BandeauBaseTestTests(TestCase):
    """Le bandeau d'avertissement « BASE DE TEST » (issue #12) ne doit
    jamais apparaître quand la base active n'est pas 'apiselect_dev'
    (comportement par défaut des tests), et doit apparaître dès que
    settings.BASE_DE_TEST_ACTIVE est vrai — sur l'admin ET sur les vues
    personnalisées du projet."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="motdepasse",
        )
        self.client.force_login(self.superuser)

    def test_bandeau_absent_de_ladmin_par_defaut(self):
        response = self.client.get(reverse("admin:index"))

        self.assertNotContains(response, "BASE DE TEST")

    def test_bandeau_absent_des_resultats_par_defaut(self):
        response = self.client.get(reverse("selection:resultats"))

        self.assertNotContains(response, "BASE DE TEST")

    @override_settings(BASE_DE_TEST_ACTIVE=True)
    def test_bandeau_present_sur_ladmin_si_base_de_test_active(self):
        response = self.client.get(reverse("admin:index"))

        self.assertContains(response, "BASE DE TEST")

    @override_settings(BASE_DE_TEST_ACTIVE=True)
    def test_bandeau_present_sur_les_resultats_si_base_de_test_active(self):
        response = self.client.get(reverse("selection:resultats"))

        self.assertContains(response, "BASE DE TEST")

    @override_settings(BASE_DE_TEST_ACTIVE=True)
    def test_bandeau_present_sur_le_calendrier_si_base_de_test_active(self):
        response = self.client.get(reverse("selection:calendrier"))

        self.assertContains(response, "BASE DE TEST")

    @override_settings(BASE_DE_TEST_ACTIVE=True)
    def test_bandeau_present_sur_les_taches_si_base_de_test_active(self):
        response = self.client.get(reverse("selection:taches"))

        self.assertContains(response, "BASE DE TEST")

    @override_settings(BASE_DE_TEST_ACTIVE=True)
    def test_bandeau_present_sur_la_fiche_rapide_pdf_si_base_de_test_active(self):
        # xhtml2pdf transforme le HTML en PDF binaire : on intercepte le
        # HTML juste avant conversion plutôt que de tenter de parser le
        # PDF généré.
        with mock.patch("selection.views.pisa.CreatePDF") as creer_pdf_mock:
            creer_pdf_mock.return_value = mock.Mock(err=False)
            self.client.get(reverse("selection:fiche_rapide"))

        html_genere = creer_pdf_mock.call_args.args[0]
        self.assertIn("BASE DE TEST", html_genere)


class PeuplerDonneesTestCommandTests(TestCase):
    """Vérifie que `peupler_donnees_test` crée bien le jeu de données
    fictif attendu (issue #12) : rucher/reines/colonies préfixées TEST-,
    une colonie exclue par seuil, une colonie sans mesure — et refuse de
    s'exécuter sur la vraie base 'apiselect'."""

    def test_refuse_de_sexecuter_sur_la_vraie_base(self):
        nom_original = connection.settings_dict["NAME"]
        connection.settings_dict["NAME"] = "apiselect"
        try:
            with self.assertRaises(CommandError):
                call_command("peupler_donnees_test")
        finally:
            connection.settings_dict["NAME"] = nom_original
        self.assertFalse(Rucher.objects.filter(nom=NOM_RUCHER_TEST).exists())

    def test_cree_le_rucher_et_les_colonies_fictives(self):
        call_command("peupler_donnees_test")

        rucher = Rucher.objects.get(nom=NOM_RUCHER_TEST)
        self.assertEqual(Colonie.objects.filter(ruche__rucher=rucher).count(), 3)
        self.assertEqual(Reine.objects.filter(identifiant__startswith="TEST-").count(), 3)
        self.assertTrue(CampagneElevage.objects.filter(nom__startswith="TEST-").exists())

    def test_cree_une_colonie_exclue_par_seuil(self):
        call_command("peupler_donnees_test")

        campagne = CampagneElevage.objects.get(nom__startswith="TEST-")
        colonie_exclue = Colonie.objects.get(reine_actuelle__identifiant="TEST-R2")
        resultat = calculer_index_colonie(colonie_exclue.id, campagne.id)

        self.assertTrue(resultat.exclue)
        self.assertIsNone(resultat.index)

    def test_cree_une_colonie_sans_mesure(self):
        call_command("peupler_donnees_test")

        colonie_sans_mesure = Colonie.objects.get(reine_actuelle__identifiant="TEST-R3")

        self.assertFalse(Mesure.objects.filter(colonie=colonie_sans_mesure).exists())

    def test_relance_sans_purge_ne_duplique_pas(self):
        call_command("peupler_donnees_test")
        call_command("peupler_donnees_test")

        self.assertEqual(Rucher.objects.filter(nom=NOM_RUCHER_TEST).count(), 1)


class PurgerDonneesTestCommandTests(TestCase):
    """Vérifie que `purger_donnees_test` supprime uniquement les données
    créées par `peupler_donnees_test`, sans toucher au reste de la base,
    et refuse de s'exécuter sur la vraie base 'apiselect' (issue #12)."""

    def test_refuse_de_sexecuter_sur_la_vraie_base(self):
        call_command("peupler_donnees_test")

        nom_original = connection.settings_dict["NAME"]
        connection.settings_dict["NAME"] = "apiselect"
        try:
            with self.assertRaises(CommandError):
                call_command("purger_donnees_test")
        finally:
            connection.settings_dict["NAME"] = nom_original
        self.assertTrue(Rucher.objects.filter(nom=NOM_RUCHER_TEST).exists())

    def test_supprime_uniquement_les_donnees_de_test(self):
        type_ruche = TypeRuche.objects.get(code="DADANT10")
        ruche_reelle = Ruche.objects.create(type_ruche=type_ruche, numero=1)
        Colonie.objects.create(
            ruche=ruche_reelle, mode_creation=ModeCreationColonie.ACHAT,
            date_creation="2026-01-01", active=True,
        )
        reine_reelle = Reine.objects.create(identifiant="R26-01")
        campagne_reelle = CampagneElevage.objects.create(nom="Campagne réelle", annee=2026)

        call_command("peupler_donnees_test")
        call_command("purger_donnees_test")

        self.assertFalse(Rucher.objects.filter(nom=NOM_RUCHER_TEST).exists())
        self.assertFalse(Reine.objects.filter(identifiant__startswith="TEST-").exists())
        self.assertFalse(CampagneElevage.objects.filter(nom__startswith="TEST-").exists())
        # Les données réelles préexistantes ne sont pas touchées.
        self.assertTrue(Ruche.objects.filter(pk=ruche_reelle.pk).exists())
        self.assertTrue(Reine.objects.filter(pk=reine_reelle.pk).exists())
        self.assertTrue(CampagneElevage.objects.filter(pk=campagne_reelle.pk).exists())
