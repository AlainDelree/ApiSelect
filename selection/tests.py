from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .calculs import MesureIndex, calculer_index
from .models import (
    CampagneElevage,
    Colonie,
    CritereSelection,
    Mesure,
    PoidsCritere,
    Ruche,
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
