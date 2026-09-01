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
    LotCriteres,
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
        self.lot_criteres = LotCriteres.objects.create(nom="Lot 2026")
        self.campagne = CampagneElevage.objects.create(
            nom="Campagne 2026", annee=2026, lot_criteres=self.lot_criteres,
        )
        self.critere_sante = CritereSelection.objects.get(code="SANTE")
        self.critere_proprete = CritereSelection.objects.get(code="PROPRETE")

    def test_tri_par_index_decroissant(self):
        PoidsCritere.objects.filter(
            lot=self.lot_criteres, critere=self.critere_proprete,
        ).update(poids=5)
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
        PoidsCritere.objects.filter(
            lot=self.lot_criteres, critere=self.critere_sante,
        ).update(poids=8, seuil_eliminatoire=Decimal("2"))
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


class LotCriteresReutilisableEntreCampagnesTests(TestCase):
    """Vérifie le découplage des poids (issue #19) : un même LotCriteres
    peut être assigné à plusieurs campagnes simultanément, et l'index se
    calcule correctement (via la jointure SQL par lot_criteres_id, cf.
    0011_vue_mesures_completes_lot_criteres.py) pour chacune, à partir de
    mesures propres à chaque campagne."""

    def _creer_colonie(self, numero):
        type_ruche = TypeRuche.objects.get(code="DADANT10")
        ruche = Ruche.objects.create(type_ruche=type_ruche, numero=numero)
        return Colonie.objects.create(
            ruche=ruche, mode_creation="ACHAT", date_creation="2026-01-01",
            active=True,
        )

    def setUp(self):
        self.lot_criteres = LotCriteres.objects.create(nom="Lot partagé 2026")
        self.critere_proprete = CritereSelection.objects.get(code="PROPRETE")
        PoidsCritere.objects.filter(
            lot=self.lot_criteres, critere=self.critere_proprete,
        ).update(poids=5)
        self.campagne_1 = CampagneElevage.objects.create(
            nom="Vague 1", annee=2026, lot_criteres=self.lot_criteres,
        )
        self.campagne_2 = CampagneElevage.objects.create(
            nom="Vague 2", annee=2026, lot_criteres=self.lot_criteres,
        )

    def test_meme_lot_assignable_a_plusieurs_campagnes(self):
        self.assertEqual(
            set(self.lot_criteres.campagnes.values_list("nom", flat=True)),
            {"Vague 1", "Vague 2"},
        )

    def test_index_correct_pour_chaque_campagne_avec_le_meme_lot(self):
        colonie_1 = self._creer_colonie(1)
        Mesure.objects.create(
            colonie=colonie_1, critere=self.critere_proprete,
            campagne=self.campagne_1, date_mesure="2026-05-01",
            valeur_brute="propre", score=4,
        )
        colonie_2 = self._creer_colonie(2)
        Mesure.objects.create(
            colonie=colonie_2, critere=self.critere_proprete,
            campagne=self.campagne_2, date_mesure="2026-05-01",
            valeur_brute="sale", score=2,
        )

        resultat_1 = calculer_index_colonie(colonie_1.id, self.campagne_1.id)
        resultat_2 = calculer_index_colonie(colonie_2.id, self.campagne_2.id)

        self.assertEqual(resultat_1.index, Decimal(4))
        self.assertEqual(resultat_2.index, Decimal(2))


class AutoPeuplementLotCriteresTests(TestCase):
    """Vérifie le signal post_save sur LotCriteres (issue #20) : à la
    création d'un lot, un PoidsCritere à poids=0 est créé pour chacun des
    CritereSelection existants, sans duplication à un ré-enregistrement."""

    def test_creation_lot_cree_un_poids_zero_par_critere(self):
        lot = LotCriteres.objects.create(nom="Lot auto-peuplé")

        nb_criteres = CritereSelection.objects.count()
        self.assertEqual(nb_criteres, 9)
        self.assertEqual(lot.poids_criteres.count(), nb_criteres)
        self.assertTrue(
            all(pc.poids == 0 for pc in lot.poids_criteres.all())
        )
        self.assertTrue(
            all(pc.seuil_eliminatoire is None for pc in lot.poids_criteres.all())
        )
        self.assertEqual(
            set(lot.poids_criteres.values_list("critere_id", flat=True)),
            set(CritereSelection.objects.values_list("id", flat=True)),
        )

    def test_reenregistrement_du_lot_ne_duplique_rien(self):
        lot = LotCriteres.objects.create(nom="Lot ré-enregistré")
        nb_criteres = CritereSelection.objects.count()

        lot.notes = "RAS"
        lot.save()

        self.assertEqual(lot.poids_criteres.count(), nb_criteres)


class AjoutLotCriteresAdminAffichePoidsPreremplisTests(TestCase):
    """Vérifie que la page d'ajout d'un LotCriteres affiche directement
    les 9 lignes d'inline pré-remplies (critère + poids=0), sans passer
    par le détour "enregistrer une première fois" qu'imposait le seul
    signal post_save (issue #20 -> issue #21)."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="motdepasse",
        )
        self.client.force_login(self.superuser)

    def test_page_ajout_affiche_9_lignes_prereplies(self):
        response = self.client.get(reverse("admin:selection_lotcriteres_add"))

        self.assertEqual(response.status_code, 200)
        formset = response.context["inline_admin_formsets"][0].formset
        self.assertEqual(formset.extra_forms.__len__(), CritereSelection.objects.count())
        criteres_prereplis = {
            form.initial["critere"] for form in formset.extra_forms
        }
        self.assertEqual(
            criteres_prereplis,
            set(CritereSelection.objects.values_list("id", flat=True)),
        )
        self.assertTrue(
            all(form.initial["poids"] == 0 for form in formset.extra_forms)
        )

    def test_enregistrement_depuis_la_page_dajout_ne_cree_pas_de_doublons(self):
        criteres = list(CritereSelection.objects.all())
        nb_criteres = len(criteres)

        data = {
            "nom": "Lot créé depuis la page d'ajout",
            "notes": "",
            "poids_criteres-TOTAL_FORMS": str(nb_criteres),
            "poids_criteres-INITIAL_FORMS": "0",
            "poids_criteres-MIN_NUM_FORMS": "0",
            "poids_criteres-MAX_NUM_FORMS": "1000",
        }
        for i, critere in enumerate(criteres):
            data[f"poids_criteres-{i}-critere"] = str(critere.id)
            data[f"poids_criteres-{i}-poids"] = "0"
            data[f"poids_criteres-{i}-seuil_eliminatoire"] = ""
            data[f"poids_criteres-{i}-id"] = ""

        response = self.client.post(
            reverse("admin:selection_lotcriteres_add"), data, follow=True,
        )

        self.assertEqual(response.status_code, 200)
        lot = LotCriteres.objects.get(nom="Lot créé depuis la page d'ajout")
        self.assertEqual(lot.poids_criteres.count(), nb_criteres)
        self.assertEqual(
            set(lot.poids_criteres.values_list("critere_id", flat=True)),
            set(c.id for c in criteres),
        )


class PoidsCritereInlineRepereDesambiguisationTests(TestCase):
    """Vérifie que le formulaire d'ajout d'un LotCriteres affiche, dans
    la liste déroulante du champ `critere`, un repère de désambiguïsation
    entre parenthèses pour les paires de noms proches (issue #23) :
    "Miel" / "Récolte" et "Propreté" / "Nettoyage des rayons"."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="motdepasse",
        )
        self.client.force_login(self.superuser)

    def _labels_champ_critere(self, response):
        formset = response.context["inline_admin_formsets"][0].formset
        champ_critere = formset.forms[0].fields["critere"]
        return {
            critere: champ_critere.label_from_instance(critere)
            for critere in CritereSelection.objects.all()
        }

    def test_libelles_distinguent_miel_et_recolte(self):
        response = self.client.get(reverse("admin:selection_lotcriteres_add"))
        labels = {
            critere.code: label
            for critere, label in self._labels_champ_critere(response).items()
        }

        self.assertNotEqual(labels["MIEL"], labels["RECOLTE"])
        self.assertIn("Miel", labels["MIEL"])
        self.assertIn("Récolte", labels["RECOLTE"])
        self.assertGreater(len(labels["MIEL"]), len("Miel"))
        self.assertGreater(len(labels["RECOLTE"]), len("Récolte"))

    def test_libelles_distinguent_proprete_et_nettoyage(self):
        response = self.client.get(reverse("admin:selection_lotcriteres_add"))
        labels = {
            critere.code: label
            for critere, label in self._labels_champ_critere(response).items()
        }

        self.assertNotEqual(labels["PROPRETE"], labels["NETTOYAGE"])
        self.assertIn("Propreté", labels["PROPRETE"])
        self.assertIn("Nettoyage des rayons", labels["NETTOYAGE"])
        self.assertGreater(len(labels["PROPRETE"]), len("Propreté"))
        self.assertGreater(len(labels["NETTOYAGE"]), len("Nettoyage des rayons"))

    def test_nom_stocke_en_base_reste_inchange(self):
        self.client.get(reverse("admin:selection_lotcriteres_add"))

        self.assertEqual(CritereSelection.objects.get(code="MIEL").nom, "Miel")
        self.assertEqual(
            CritereSelection.objects.get(code="RECOLTE").nom, "Récolte",
        )
        self.assertEqual(
            CritereSelection.objects.get(code="PROPRETE").nom, "Propreté",
        )
        self.assertEqual(
            CritereSelection.objects.get(code="NETTOYAGE").nom,
            "Nettoyage des rayons",
        )

    def test_titre_html_de_loption_contient_la_description_complete(self):
        response = self.client.get(reverse("admin:selection_lotcriteres_add"))
        formset = response.context["inline_admin_formsets"][0].formset
        champ_critere = formset.forms[0].fields["critere"]
        miel = CritereSelection.objects.get(code="MIEL")

        html = champ_critere.widget.render("critere", str(miel.pk))

        self.assertIn(miel.description, html)


class CalculerDatesEtapesTests(TestCase):
    """Vérifie la cascade de dates contre la méthode réelle d'Alain
    (issue #14) : pas de starter/finisseur/couveuse séparés (fusionnés en
    "ruche orpheline"), pas de ruchettes/libération/contrôle des
    naissances (distribution directe des CR dans les Apidea), pas de
    début de ponte séparé (fusionné avec le contrôle de ponte et la pose
    de la grille anti-essaimage). Ponte le 5/06/2022 -> picking le
    9/06/2022, reste de la cascade documentée en commentaire dans
    calculs.py."""

    def setUp(self):
        self.date_ponte = date(2022, 6, 5)
        self.dates = calculer_dates_etapes(self.date_ponte)

    def test_toutes_les_etapes_du_modele_sont_calculees(self):
        self.assertEqual(set(self.dates), {code for code, _ in TypeEtapeCalendrier.choices})

    def test_orphelinage_cinq_jours_avant_la_ponte(self):
        # Loi des 9 jours (issue #16) : PICKING (+4j) - 9j = -5j, pour que
        # la colonie orpheline n'ait plus de couvain ouvrable à J-picking.
        self.assertEqual(self.dates["ORPHELINAGE"], self.date_ponte - timedelta(days=5))

    def test_picking_quatre_jours_apres_la_ponte(self):
        self.assertEqual(self.dates["PICKING"], date(2022, 6, 9))

    def test_ruche_orpheline_le_meme_jour_que_le_picking(self):
        # Pas de starter séparé : greffage direct dans la ruche orpheline
        # qui élève les cellules royales jusqu'à operculation et au-delà.
        self.assertEqual(self.dates["RUCHE_ORPHELINE"], self.dates["PICKING"])

    def test_garnir_apidea(self):
        # Distribution directe des cellules royales dans les Apidea (pas
        # de couveuse ni de ruchettes intermédiaires).
        self.assertEqual(self.dates["GARNIR_APIDEA"], date(2022, 6, 19))

    def test_controle_ponte_et_grille(self):
        self.assertEqual(self.dates["CONTROLE_PONTE_GRILLE"], date(2022, 6, 30))

    def test_elevage_males_seize_jours_avant_la_ponte(self):
        # Décalage -16j : principe de saturation du cours (CONTEXTE.md),
        # inchangé par l'issue #14 — cf. calculs.py.
        self.assertEqual(self.dates["ELEVAGE_MALES"], self.date_ponte - timedelta(days=16))

    def test_decalages_geles_contre_regression_silencieuse(self):
        # Verrouille les valeurs exactes de la méthode réelle d'Alain
        # (issue #14) : toute modification de DECALAGES_JOURS_ETAPES doit
        # être volontaire.
        self.assertEqual(DECALAGES_JOURS_ETAPES, {
            "ELEVAGE_MALES": -16,
            "ORPHELINAGE": -5,
            "PICKING": 4,
            "RUCHE_ORPHELINE": 4,
            "GARNIR_APIDEA": 14,
            "CONTROLE_PONTE_GRILLE": 25,
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
        # elevage_males_actif=False par défaut (issue #14) : une étape de
        # moins que le nombre total de types.
        self.assertEqual(campagne.etapes.count(), len(TypeEtapeCalendrier.choices) - 1)
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
        self.assertEqual(campagne.etapes.count(), len(TypeEtapeCalendrier.choices) - 1)

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
        # elevage_males_actif=False par défaut (issue #14) : une étape de
        # moins que le nombre total de types (6 depuis l'issue #16).
        self.assertEqual(EtapeCalendrier.objects.filter(campagne=campagne_1).count(), 5)
        self.assertEqual(EtapeCalendrier.objects.filter(campagne=campagne_2).count(), 5)

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


class ElevageMalesFacultatifTests(TestCase):
    """Vérifie le caractère facultatif de l'étape ELEVAGE_MALES (issue
    #14) : non créée par défaut (elevage_males_actif=False), créée si le
    champ est coché, supprimée si le champ repasse à décoché plutôt que
    laissée orpheline avec une date obsolète."""

    def test_etape_non_creee_par_defaut(self):
        campagne = CampagneElevage.objects.create(
            nom="Campagne sans mâles", annee=2022, date_reference=date(2022, 6, 5),
        )
        self.assertFalse(
            campagne.etapes.filter(type_etape=TypeEtapeCalendrier.ELEVAGE_MALES).exists()
        )

    def test_etape_creee_si_champ_coche(self):
        campagne = CampagneElevage.objects.create(
            nom="Campagne avec mâles", annee=2022, date_reference=date(2022, 6, 5),
            elevage_males_actif=True,
        )
        etape = campagne.etapes.get(type_etape=TypeEtapeCalendrier.ELEVAGE_MALES)
        self.assertEqual(etape.date_prevue, date(2022, 6, 5) - timedelta(days=16))

    def test_etape_supprimee_si_champ_decoche_apres_coup(self):
        campagne = CampagneElevage.objects.create(
            nom="Campagne C", annee=2022, date_reference=date(2022, 6, 5),
            elevage_males_actif=True,
        )
        self.assertTrue(
            campagne.etapes.filter(type_etape=TypeEtapeCalendrier.ELEVAGE_MALES).exists()
        )

        campagne.elevage_males_actif = False
        campagne.save()

        self.assertFalse(
            campagne.etapes.filter(type_etape=TypeEtapeCalendrier.ELEVAGE_MALES).exists()
        )


class TauxReussiteCrTests(TestCase):
    """Vérifie CampagneElevage.taux_reussite (issue #16) : CR introduites
    dans les Apidea (étape GARNIR_APIDEA.nombre_cr) divisé par CR obtenues
    sur la ruche orpheline (étape RUCHE_ORPHELINE.nombre_cr), avec gestion
    propre des cas où le calcul est impossible (pas de division par
    zéro)."""

    def setUp(self):
        self.campagne = CampagneElevage.objects.create(
            nom="Campagne E", annee=2022, date_reference=date(2022, 6, 5),
        )

    def test_taux_reussite_cas_normal(self):
        etape_obtenues = self.campagne.etapes.get(
            type_etape=TypeEtapeCalendrier.RUCHE_ORPHELINE,
        )
        etape_obtenues.nombre_cr = 10
        etape_obtenues.save()
        etape_introduites = self.campagne.etapes.get(
            type_etape=TypeEtapeCalendrier.GARNIR_APIDEA,
        )
        etape_introduites.nombre_cr = 8
        etape_introduites.save()

        self.assertEqual(self.campagne.taux_reussite, 0.8)

    def test_taux_reussite_non_calculable_si_donnees_manquantes(self):
        # Aucun nombre_cr renseigné sur aucune des deux étapes.
        self.assertIsNone(self.campagne.taux_reussite)

    def test_taux_reussite_non_calculable_si_une_seule_valeur_renseignee(self):
        etape_obtenues = self.campagne.etapes.get(
            type_etape=TypeEtapeCalendrier.RUCHE_ORPHELINE,
        )
        etape_obtenues.nombre_cr = 10
        etape_obtenues.save()
        # GARNIR_APIDEA.nombre_cr non renseigné.

        self.assertIsNone(self.campagne.taux_reussite)

    def test_taux_reussite_non_calculable_si_zero_cr_obtenues(self):
        etape_obtenues = self.campagne.etapes.get(
            type_etape=TypeEtapeCalendrier.RUCHE_ORPHELINE,
        )
        etape_obtenues.nombre_cr = 0
        etape_obtenues.save()
        etape_introduites = self.campagne.etapes.get(
            type_etape=TypeEtapeCalendrier.GARNIR_APIDEA,
        )
        etape_introduites.nombre_cr = 0
        etape_introduites.save()

        self.assertIsNone(self.campagne.taux_reussite)

    def test_champ_ruche_associable_a_une_etape(self):
        type_ruche = TypeRuche.objects.get(code="DADANT10")
        ruche = Ruche.objects.create(type_ruche=type_ruche, numero=42)
        etape = self.campagne.etapes.get(type_etape=TypeEtapeCalendrier.RUCHE_ORPHELINE)
        etape.ruche = ruche
        etape.nombre_cr = 5
        etape.full_clean()
        etape.save()

        etape.refresh_from_db()
        self.assertEqual(etape.ruche, ruche)
        self.assertEqual(etape.nombre_cr, 5)


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
        # elevage_males_actif=False par défaut (issue #14) : une étape de
        # moins que le nombre total de types.
        self.assertEqual(len(etapes), len(TypeEtapeCalendrier.choices) - 1)
        dates = [etape.date_prevue for etape in etapes]
        self.assertEqual(dates, sorted(dates))

    def test_taches_exclut_les_etapes_marquees_realisees(self):
        picking = self.campagne.etapes.get(type_etape=TypeEtapeCalendrier.PICKING)
        picking.realisee = True
        picking.save()

        response = self.client.get(reverse("selection:taches"))

        etapes = list(response.context["etapes"])
        self.assertNotIn(picking, etapes)
        self.assertEqual(len(etapes), len(TypeEtapeCalendrier.choices) - 2)

    def test_calendrier_expose_une_couleur_distincte_par_etape(self):
        """Palette fixe par type d'étape (issue #15) : chaque étape du
        contexte porte une couleur, et PICKING/GARNIR_APIDEA se
        distinguent des 3 autres étapes."""
        response = self.client.get(reverse("selection:calendrier"), {"annee": 2022, "mois": 6})

        etapes = [
            etape
            for semaine in response.context["semaines"]
            for jour in semaine
            for etape in jour["etapes"]
        ]
        self.assertTrue(etapes)
        for etape in etapes:
            self.assertTrue(etape.couleur["fond"].startswith("#"))
            self.assertTrue(etape.couleur["texte"].startswith("#"))

        couleurs = {etape.type_etape: etape.couleur["fond"] for etape in etapes}
        self.assertEqual(len(set(couleurs.values())), len(couleurs))

    def test_taches_expose_une_couleur_par_etape(self):
        response = self.client.get(reverse("selection:taches"))

        etapes = list(response.context["etapes"])
        self.assertTrue(etapes)
        for etape in etapes:
            self.assertTrue(etape.couleur["fond"].startswith("#"))


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


class ReinitialiserDonneesTestCommandTests(TestCase):
    """Vérifie que `reinitialiser_donnees_test` enchaîne purge puis
    peuplement (issue #17) : refuse de s'exécuter sur la vraie base
    'apiselect', et produit un jeu de données fictif propre même si un
    jeu précédent existait déjà."""

    def test_refuse_de_sexecuter_sur_la_vraie_base(self):
        nom_original = connection.settings_dict["NAME"]
        connection.settings_dict["NAME"] = "apiselect"
        try:
            with self.assertRaises(CommandError):
                call_command("reinitialiser_donnees_test")
        finally:
            connection.settings_dict["NAME"] = nom_original
        self.assertFalse(Rucher.objects.filter(nom=NOM_RUCHER_TEST).exists())

    def test_reinitialise_le_jeu_de_donnees_fictif(self):
        call_command("reinitialiser_donnees_test")

        rucher = Rucher.objects.get(nom=NOM_RUCHER_TEST)
        self.assertEqual(Colonie.objects.filter(ruche__rucher=rucher).count(), 3)
        self.assertEqual(Reine.objects.filter(identifiant__startswith="TEST-").count(), 3)
        self.assertTrue(CampagneElevage.objects.filter(nom__startswith="TEST-").exists())

    def test_purge_lancien_jeu_avant_de_repeupler(self):
        call_command("peupler_donnees_test")
        ancienne_reine_pk = Reine.objects.get(identifiant="TEST-R1").pk

        call_command("reinitialiser_donnees_test")

        self.assertEqual(Rucher.objects.filter(nom=NOM_RUCHER_TEST).count(), 1)
        self.assertFalse(Reine.objects.filter(pk=ancienne_reine_pk).exists())
        self.assertEqual(Reine.objects.filter(identifiant__startswith="TEST-").count(), 3)
