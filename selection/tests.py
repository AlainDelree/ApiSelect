from decimal import Decimal

from django.test import TestCase

from .calculs import MesureIndex, calculer_index


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
