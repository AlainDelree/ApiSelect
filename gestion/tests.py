from django.test import TestCase
from django.urls import reverse

from selection.models import (
    Colonie,
    ConfigurationColonie,
    CouleurMarquage,
    EvenementColonie,
    ModeCreationColonie,
    Reine,
    Ruche,
    Rucher,
    TypeEvenementColonie,
    TypeRuche,
)


class AccueilVisuelTests(TestCase):
    """Écran d'accueil (issue #41) : une section par rucher, une tuile par
    ruche avec sa couleur et sa reine, ruches sans colonie active
    affichées « vide »."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher des tests")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")

    def test_tuile_affiche_couleur_et_reine(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=1, rucher=self.rucher,
            couleur="#3f8f3f",
        )
        reine = Reine.objects.create(
            identifiant="R-ACCUEIL-1", couleur_marquage=CouleurMarquage.BLEU,
        )
        Colonie.objects.create(
            ruche=ruche, reine_actuelle=reine,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Rucher des tests")
        self.assertContains(reponse, "Ruche 1")
        self.assertContains(reponse, "#3f8f3f")
        self.assertContains(reponse, "R-ACCUEIL-1")

    def test_ruche_sans_colonie_active_affichee_vide(self):
        Ruche.objects.create(
            type_ruche=self.type_ruche, numero=2, rucher=self.rucher,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "Vide")

    def test_ruche_sans_couleur_ne_plante_pas(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=3, rucher=self.rucher,
        )
        Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertEqual(reponse.status_code, 200)

    def test_compteurs_colonies_actives_et_ruchers(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=4, rucher=self.rucher,
        )
        Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertEqual(reponse.context["nb_colonies_actives"], 1)
        self.assertEqual(reponse.context["nb_ruchers"], 1)

    def test_ruche_retiree_du_service_absente_de_laccueil(self):
        Ruche.objects.create(
            type_ruche=self.type_ruche, numero=5, rucher=self.rucher,
            actif=False,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertNotContains(reponse, "Ruche 5")


class FicheColonieTests(TestCase):
    """Fiche colonie en lecture seule (issue #41) : ruche, rucher, reine,
    configuration actuelle, historique des événements."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher fiche")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=10, rucher=self.rucher,
            couleur="#ff0000",
        )
        self.reine = Reine.objects.create(
            identifiant="R-FICHE-1", couleur_marquage=CouleurMarquage.ROUGE,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, reine_actuelle=self.reine,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        ConfigurationColonie.objects.create(
            colonie=self.colonie, date="2026-01-01", nb_corps=2, nb_hausses=1,
        )
        EvenementColonie.objects.create(
            colonie=self.colonie, date="2026-01-01",
            type_evenement=TypeEvenementColonie.CREATION,
        )

    def test_fiche_colonie_saffiche(self):
        reponse = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Ruche 10")
        self.assertContains(reponse, "Rucher fiche")
        self.assertContains(reponse, "R-FICHE-1")
        self.assertContains(reponse, "Création")

    def test_lien_modification_admin_present(self):
        reponse = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertContains(
            reponse, reverse("admin:selection_colonie_change", args=[self.colonie.id])
        )

    def test_colonie_inexistante_404(self):
        reponse = self.client.get(reverse("gestion:fiche_colonie", args=[999999]))
        self.assertEqual(reponse.status_code, 404)
