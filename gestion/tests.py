from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from selection.models import (
    Colonie,
    ConfigurationColonie,
    CouleurMarquage,
    EvenementColonie,
    ModeAcquisitionReine,
    ModeCreationColonie,
    Reine,
    Ruche,
    Rucher,
    StatutReine,
    TypeEvenementColonie,
    TypeRuche,
)

from .affichage import COULEUR_GRISE_PAR_DEFAUT, bande_ruche
from .models import (
    DELAI_RAPPEL_REINE_MORTE_JOURS,
    ActionVisite,
    CertitudeObservation,
    ObservationVisite,
    RappelRevisite,
    ReponseCellulesRoyales,
    StatutObservation,
    TypeActionVisite,
    TypeObservationVisite,
    Vendeur,
    Visite,
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


class BandeRucheTests(TestCase):
    """Bande de couleur des tuiles et de la fiche colonie (issue #47) :
    largeur proportionnelle au nombre de cadres du type de ruche,
    centrée entre deux bandes blanches égales, gris par défaut sans
    couleur renseignée, pleine largeur si le nombre de cadres est
    inconnu ou atteint 10."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher bandes")
        self.type_dadant = TypeRuche.objects.get(code="DADANT10")
        self.type_ruchette = TypeRuche.objects.get(code="RUCHETTE6")

    def test_dix_cadres_bande_pleine_largeur(self):
        self.type_dadant.nombre_cadres = 10
        self.type_dadant.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=101, rucher=self.rucher,
            couleur="#3f8f3f",
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["largeur_pourcent"], 100)
        self.assertEqual(bande["marge_pourcent"], 0)

    def test_ruchette_six_cadres_proportion_centree(self):
        self.type_ruchette.nombre_cadres = 6
        self.type_ruchette.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruchette, numero=102, rucher=self.rucher,
            couleur="#1e88e5",
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["largeur_pourcent"], 60)
        self.assertEqual(bande["marge_pourcent"], 20)
        # Les deux bandes blanches (une de chaque côté) sont égales.
        self.assertEqual(bande["marge_pourcent"] * 2 + bande["largeur_pourcent"], 100)

    def test_nombre_de_cadres_inconnu_bande_pleine_largeur(self):
        # self.type_dadant.nombre_cadres reste vide : comportement par
        # défaut juste après la migration additive, avant saisie
        # manuelle dans l'admin.
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=103, rucher=self.rucher,
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["largeur_pourcent"], 100)
        self.assertEqual(bande["marge_pourcent"], 0)

    def test_ruche_sans_couleur_gris_par_defaut(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=104, rucher=self.rucher,
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["couleur"], COULEUR_GRISE_PAR_DEFAUT)

    def test_couleur_videe_retombe_sur_le_gris_par_defaut(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=105, rucher=self.rucher,
            couleur="#3f8f3f",
        )
        ruche.couleur = ""
        ruche.save()

        bande = bande_ruche(ruche)

        self.assertEqual(bande["couleur"], COULEUR_GRISE_PAR_DEFAUT)

    def test_libelle_accessible_mentionne_type_cadres_et_couleur(self):
        self.type_ruchette.nombre_cadres = 6
        self.type_ruchette.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruchette, numero=106, rucher=self.rucher,
            couleur="#1e88e5",
        )

        bande = bande_ruche(ruche)

        self.assertIn("Ruchette", bande["libelle"])
        self.assertIn("6 cadre", bande["libelle"])
        self.assertIn("bleue", bande["libelle"])

    def test_bande_ruchette_affichee_sur_la_tuile_accueil(self):
        self.type_ruchette.nombre_cadres = 6
        self.type_ruchette.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruchette, numero=107, rucher=self.rucher,
            couleur="#1e88e5",
        )
        Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "width: 60%")
        self.assertContains(reponse, "left: 20%")

    def test_ruche_sans_colonie_active_toujours_marquee_vide(self):
        self.type_dadant.nombre_cadres = 10
        self.type_dadant.save()
        Ruche.objects.create(
            type_ruche=self.type_dadant, numero=108, rucher=self.rucher,
            couleur="#3f8f3f",
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "Vide")
        self.assertContains(reponse, "tuile-vide")

    def test_fiche_colonie_affiche_la_meme_bande(self):
        self.type_ruchette.nombre_cadres = 6
        self.type_ruchette.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruchette, numero=109, rucher=self.rucher,
            couleur="#1e88e5",
        )
        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(
            reverse("gestion:fiche_colonie", args=[colonie.id])
        )

        self.assertContains(reponse, "fiche-bande")
        self.assertContains(reponse, "width: 60%")
        self.assertContains(reponse, "left: 20%")


class BandeRucheHauteurTests(TestCase):
    """Hauteur relative de la bande (issue #49) : zone colorée centrée
    verticalement, bandes blanches hautes/basses égales — pour les
    boîtes visuellement plus petites (ex. Apidea). Comportement
    inchangé si la hauteur relative est vide ou à 100."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher bandes hauteur")
        self.type_dadant = TypeRuche.objects.get(code="DADANT10")
        self.type_ruchette = TypeRuche.objects.get(code="RUCHETTE6")

    def test_hauteur_vide_bande_pleine_hauteur(self):
        # hauteur_relative_pourcent reste vide : comportement par défaut
        # juste après la migration additive.
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=201, rucher=self.rucher,
            couleur="#3f8f3f",
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["hauteur_pourcent"], 100)
        self.assertEqual(bande["marge_verticale_pourcent"], 0)

    def test_hauteur_cent_bande_pleine_hauteur(self):
        self.type_dadant.hauteur_relative_pourcent = 100
        self.type_dadant.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=202, rucher=self.rucher,
            couleur="#3f8f3f",
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["hauteur_pourcent"], 100)
        self.assertEqual(bande["marge_verticale_pourcent"], 0)

    def test_hauteur_cinquante_centree(self):
        self.type_dadant.hauteur_relative_pourcent = 50
        self.type_dadant.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=203, rucher=self.rucher,
            couleur="#3f8f3f",
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["hauteur_pourcent"], 50)
        self.assertEqual(bande["marge_verticale_pourcent"], 25)
        # Les deux bandes blanches (haut et bas) sont égales.
        self.assertEqual(
            bande["marge_verticale_pourcent"] * 2 + bande["hauteur_pourcent"], 100
        )

    def test_largeur_et_hauteur_combinees(self):
        self.type_ruchette.nombre_cadres = 5
        self.type_ruchette.hauteur_relative_pourcent = 50
        self.type_ruchette.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruchette, numero=204, rucher=self.rucher,
            couleur="#1e88e5",
        )

        bande = bande_ruche(ruche)

        self.assertEqual(bande["largeur_pourcent"], 50)
        self.assertEqual(bande["marge_pourcent"], 25)
        self.assertEqual(bande["hauteur_pourcent"], 50)
        self.assertEqual(bande["marge_verticale_pourcent"], 25)

    def test_bande_hauteur_affichee_sur_la_tuile_accueil(self):
        self.type_dadant.hauteur_relative_pourcent = 50
        self.type_dadant.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=205, rucher=self.rucher,
            couleur="#3f8f3f",
        )
        Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "top: 25%")
        self.assertContains(reponse, "bottom: 25%")

    def test_fiche_colonie_affiche_la_meme_hauteur(self):
        self.type_dadant.hauteur_relative_pourcent = 50
        self.type_dadant.save()
        ruche = Ruche.objects.create(
            type_ruche=self.type_dadant, numero=206, rucher=self.rucher,
            couleur="#3f8f3f",
        )
        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(
            reverse("gestion:fiche_colonie", args=[colonie.id])
        )

        self.assertContains(reponse, "fiche-bande")
        self.assertContains(reponse, "top: 25%")
        self.assertContains(reponse, "bottom: 25%")

    def test_ruche_sans_colonie_active_toujours_marquee_vide(self):
        self.type_dadant.hauteur_relative_pourcent = 50
        self.type_dadant.save()
        Ruche.objects.create(
            type_ruche=self.type_dadant, numero=207, rucher=self.rucher,
            couleur="#3f8f3f",
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "Vide")
        self.assertContains(reponse, "tuile-vide")


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


class NouvelleVisiteTests(TestCase):
    """Saisie d'une visite depuis la fiche colonie (issue #43)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher visite")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=20, rucher=self.rucher,
            couleur="#2255aa",
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

    def test_formulaire_affiche_couleur_et_numero_ruche(self):
        reponse = self.client.get(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id])
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Ruche 20")
        self.assertContains(reponse, "#2255aa")

    def test_visite_complete(self):
        reponse = self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-01",
                "observation_reine": "OEUFS_VUS",
                "nb_cadres_couvain": "6",
                "nb_cadres_abeilles": "8",
                "reserves": "CORRECTES",
                "comportement": "1",
                "notes": "RAS, belle colonie.",
                "actions": [
                    TypeActionVisite.HAUSSE_AJOUTEE,
                    TypeActionVisite.NOURRISSEMENT,
                ],
                "observation_essaimage": "",
                "reponse_cellules_royales": "",
                "observation_reine_morte": "",
                "observation_pillage": "",
                "observation_frelons": "",
            },
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )
        visite = Visite.objects.get(colonie=self.colonie)
        self.assertEqual(visite.observation_reine, "OEUFS_VUS")
        self.assertEqual(visite.nb_cadres_couvain, 6)
        self.assertEqual(visite.nb_cadres_abeilles, 8)
        self.assertEqual(visite.reserves, "CORRECTES")
        self.assertEqual(visite.comportement, 1)
        self.assertEqual(
            set(visite.actions.values_list("type_action", flat=True)),
            {TypeActionVisite.HAUSSE_AJOUTEE, TypeActionVisite.NOURRISSEMENT},
        )

    def test_visite_minimale_date_seule(self):
        reponse = self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {"date": "2026-05-02"},
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )
        visite = Visite.objects.get(colonie=self.colonie)
        self.assertEqual(str(visite.date), "2026-05-02")
        self.assertEqual(visite.actions.count(), 0)
        self.assertEqual(visite.observations.count(), 0)

    def test_observation_en_doute_reste_ouverte(self):
        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-03",
                "observation_pillage": CertitudeObservation.DOUTE,
            },
        )

        observation = ObservationVisite.objects.get(
            colonie=self.colonie, type_observation=TypeObservationVisite.PILLAGE,
        )
        self.assertEqual(observation.certitude, CertitudeObservation.DOUTE)
        self.assertEqual(observation.statut, StatutObservation.OUVERTE)

    def test_observation_constatee_reste_aussi_ouverte(self):
        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-03",
                "observation_frelons": CertitudeObservation.CONSTATE,
            },
        )

        observation = ObservationVisite.objects.get(
            colonie=self.colonie, type_observation=TypeObservationVisite.FRELONS,
        )
        self.assertEqual(observation.certitude, CertitudeObservation.CONSTATE)
        self.assertEqual(observation.statut, StatutObservation.OUVERTE)

    def test_rappel_reine_morte_en_doute_cree_a_9_jours(self):
        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-04",
                "observation_reine_morte": CertitudeObservation.DOUTE,
            },
        )

        observation = ObservationVisite.objects.get(
            colonie=self.colonie, type_observation=TypeObservationVisite.REINE_MORTE,
        )
        rappel = RappelRevisite.objects.get(observation=observation)
        self.assertEqual(
            rappel.date_revisite,
            date(2026, 5, 4) + timedelta(days=DELAI_RAPPEL_REINE_MORTE_JOURS),
        )
        self.assertFalse(rappel.traite)

    def test_pas_de_rappel_pour_reine_morte_constatee(self):
        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-04",
                "observation_reine_morte": CertitudeObservation.CONSTATE,
            },
        )

        observation = ObservationVisite.objects.get(
            colonie=self.colonie, type_observation=TypeObservationVisite.REINE_MORTE,
        )
        self.assertFalse(RappelRevisite.objects.filter(observation=observation).exists())

    def test_cellules_royales_enregistree_pour_essaimage(self):
        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-05",
                "observation_essaimage": CertitudeObservation.CONSTATE,
                "reponse_cellules_royales": ReponseCellulesRoyales.TOUTES_SAUF_UNE,
            },
        )

        observation = ObservationVisite.objects.get(
            colonie=self.colonie, type_observation=TypeObservationVisite.ESSAIMAGE,
        )
        self.assertEqual(
            observation.reponse_cellules_royales, ReponseCellulesRoyales.TOUTES_SAUF_UNE,
        )

    def test_confirmation_depuis_fiche_colonie(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-05-06")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.PILLAGE,
            certitude=CertitudeObservation.DOUTE,
        )

        reponse = self.client.post(
            reverse("gestion:confirmer_observation", args=[observation.id])
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )
        observation.refresh_from_db()
        self.assertEqual(observation.statut, StatutObservation.CONFIRMEE)

    def test_infirmation_depuis_fiche_colonie(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-05-06")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.FRELONS,
            certitude=CertitudeObservation.DOUTE,
        )

        reponse = self.client.post(
            reverse("gestion:infirmer_observation", args=[observation.id])
        )

        observation.refresh_from_db()
        self.assertEqual(observation.statut, StatutObservation.INFIRMEE)

    def test_visite_suivante_confirme_reine_morte_si_pas_de_couvain_ouvert(self):
        premiere_visite = Visite.objects.create(colonie=self.colonie, date="2026-05-01")
        observation = ObservationVisite.objects.create(
            visite=premiere_visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        # Le rappel à 9 jours est déjà créé automatiquement par le modèle
        # à la création de l'observation ci-dessus (issue #45) : il tombe
        # justement le 2026-05-10 (2026-05-01 + 9 jours).
        rappel = observation.rappel

        reponse = self.client.get(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id])
        )
        self.assertContains(reponse, "Couvain ouvert présent")

        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-10",
                "couvain_ouvert_present": "non",
            },
        )

        observation.refresh_from_db()
        rappel.refresh_from_db()
        self.assertEqual(observation.statut, StatutObservation.CONFIRMEE)
        self.assertTrue(rappel.traite)

    def test_visite_suivante_infirme_reine_morte_si_couvain_ouvert_present(self):
        premiere_visite = Visite.objects.create(colonie=self.colonie, date="2026-05-01")
        observation = ObservationVisite.objects.create(
            visite=premiere_visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        # Rappel à 9 jours déjà créé automatiquement (2026-05-01 + 9
        # jours = 2026-05-10, cf. issue #45).
        rappel = observation.rappel

        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-05-10",
                "couvain_ouvert_present": "oui",
            },
        )

        observation.refresh_from_db()
        rappel.refresh_from_db()
        self.assertEqual(observation.statut, StatutObservation.INFIRMEE)
        self.assertTrue(rappel.traite)


class AccueilVisitesTests(TestCase):
    """Dernière visite et pastilles d'observations ouvertes sur
    l'accueil (issue #43)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher accueil visites")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")

    def test_derniere_visite_affichee(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=30, rucher=self.rucher,
        )
        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        Visite.objects.create(
            colonie=colonie, date=timezone.localdate() - timedelta(days=3),
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "il y a 3 jour")

    def test_ruche_sans_visite_sans_erreur(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=31, rucher=self.rucher,
        )
        Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Aucune visite")

    def test_pastille_observation_ouverte_affichee(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=32, rucher=self.rucher,
        )
        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        visite = Visite.objects.create(colonie=colonie, date=timezone.localdate())
        ObservationVisite.objects.create(
            visite=visite, colonie=colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "Reine morte ?")

    def test_observation_confirmee_naffiche_plus_de_pastille(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=33, rucher=self.rucher,
        )
        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        visite = Visite.objects.create(colonie=colonie, date=timezone.localdate())
        ObservationVisite.objects.create(
            visite=visite, colonie=colonie,
            type_observation=TypeObservationVisite.PILLAGE,
            certitude=CertitudeObservation.CONSTATE,
            statut=StatutObservation.CONFIRMEE,
        )

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertNotContains(reponse, "pastille-observation")

    def test_rappel_a_revisiter_affiche_sur_accueil(self):
        ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=34, rucher=self.rucher,
        )
        colonie = Colonie.objects.create(
            ruche=ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        visite = Visite.objects.create(colonie=colonie, date=timezone.localdate())
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        # Rappel par défaut déjà créé automatiquement (issue #45) ; on le
        # force dans le passé pour tester le marquage « en retard ».
        rappel = observation.rappel
        rappel.date_revisite = timezone.localdate() - timedelta(days=1)
        rappel.save(update_fields=["date_revisite"])

        reponse = self.client.get(reverse("gestion:accueil"))

        self.assertContains(reponse, "À revérifier")
        self.assertContains(reponse, "rappel-en-retard")


class ModeleObservationVisiteTests(TestCase):
    """Colonie dénormalisée et rappel automatique au niveau du modèle,
    quelle que soit l'origine de l'observation (issue #45)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher modèle")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=40, rucher=self.rucher,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        self.visite = Visite.objects.create(colonie=self.colonie, date="2026-06-01")

    def test_colonie_renseignee_automatiquement_meme_sans_la_fournir(self):
        observation = ObservationVisite(
            visite=self.visite,
            type_observation=TypeObservationVisite.PILLAGE,
            certitude=CertitudeObservation.DOUTE,
        )
        observation.save()

        observation.refresh_from_db()
        self.assertEqual(observation.colonie_id, self.colonie.id)

    def test_reenregistrement_observation_ne_duplique_pas_le_rappel(self):
        observation = ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        self.assertEqual(
            RappelRevisite.objects.filter(observation=observation).count(), 1,
        )

        # Ré-enregistrement (ex. ré-ouverture dans l'admin sans rien
        # changer) : pas de second rappel.
        observation.save()
        observation.save()

        self.assertEqual(
            RappelRevisite.objects.filter(observation=observation).count(), 1,
        )


class AdminVisiteTests(TestCase):
    """Administration des visites, observations et rappels (issues #45
    et #48) : plus aucun ajout possible (saisie réservée à l'interface
    visuelle), mais consultation, correction et suppression encore
    possibles à titre exceptionnel."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="admin-visite", email="admin-visite@example.com",
            password="motdepasse",
        )
        self.client.force_login(self.superuser)
        self.rucher = Rucher.objects.create(nom="Rucher admin")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=50, rucher=self.rucher,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

    def test_ajout_de_visite_refuse_dans_ladmin(self):
        self.assertEqual(
            self.client.get(reverse("admin:gestion_visite_add")).status_code, 403,
        )

        reponse = self.client.post(reverse("admin:gestion_visite_add"), {
            "colonie": self.colonie.id, "date": "2026-06-10",
            "actions-TOTAL_FORMS": "0", "actions-INITIAL_FORMS": "0",
            "actions-MIN_NUM_FORMS": "0", "actions-MAX_NUM_FORMS": "1000",
            "observations-TOTAL_FORMS": "0", "observations-INITIAL_FORMS": "0",
            "observations-MIN_NUM_FORMS": "0", "observations-MAX_NUM_FORMS": "1000",
        })

        self.assertEqual(reponse.status_code, 403)
        self.assertFalse(Visite.objects.filter(colonie=self.colonie).exists())

    def test_ajout_dobservation_et_de_rappel_refuses_dans_ladmin(self):
        self.assertEqual(
            self.client.get(reverse("admin:gestion_observationvisite_add")).status_code, 403,
        )
        self.assertEqual(
            self.client.get(reverse("admin:gestion_rappelrevisite_add")).status_code, 403,
        )

    def test_aucun_lien_ajouter_de_visite_sur_laccueil_admin(self):
        reponse = self.client.get(reverse("admin:index"))

        self.assertNotContains(reponse, reverse("admin:gestion_visite_add"))
        self.assertNotContains(reponse, reverse("admin:gestion_observationvisite_add"))
        self.assertNotContains(reponse, reverse("admin:gestion_rappelrevisite_add"))

    def test_consultation_et_liste_toujours_disponibles(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-06-10")

        self.assertEqual(
            self.client.get(reverse("admin:gestion_visite_changelist")).status_code, 200,
        )
        self.assertEqual(
            self.client.get(
                reverse("admin:gestion_visite_change", args=[visite.id]),
            ).status_code, 200,
        )

    def test_rappel_modifiable_apres_coup_dans_ladmin(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-06-10")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        rappel = observation.rappel

        reponse = self.client.post(
            reverse("admin:gestion_rappelrevisite_change", args=[rappel.id]),
            {"observation": rappel.observation_id, "date_revisite": "2026-07-01", "traite": "on"},
        )

        self.assertEqual(reponse.status_code, 302)
        rappel.refresh_from_db()
        self.assertEqual(str(rappel.date_revisite), "2026-07-01")
        self.assertTrue(rappel.traite)


class RevisiteFormulaireBoutonsTests(TestCase):
    """Date de revérification proposée et modifiable dans le formulaire
    à boutons (issue #45)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher revérif")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=60, rucher=self.rucher,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

    def test_date_choisie_dans_le_formulaire_utilisee_pour_le_rappel(self):
        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-06-15",
                "observation_reine_morte": CertitudeObservation.DOUTE,
                "date_reverification_reine_morte": "2026-06-20",
            },
        )

        observation = ObservationVisite.objects.get(
            colonie=self.colonie, type_observation=TypeObservationVisite.REINE_MORTE,
        )
        rappel = RappelRevisite.objects.get(observation=observation)
        self.assertEqual(str(rappel.date_revisite), "2026-06-20")
        self.assertEqual(
            RappelRevisite.objects.filter(observation=observation).count(), 1,
        )

    def test_date_de_reverification_anterieure_a_la_visite_refusee(self):
        reponse = self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {
                "date": "2026-06-15",
                "observation_reine_morte": CertitudeObservation.DOUTE,
                "date_reverification_reine_morte": "2026-06-10",
            },
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(
            reponse,
            "La date de revérification ne peut pas être antérieure",
        )
        self.assertFalse(Visite.objects.filter(colonie=self.colonie).exists())


class HistoriqueVisitesAffichageTests(TestCase):
    """L'historique des visites n'affiche que les éléments renseignés
    (issue #45)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher historique")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=70, rucher=self.rucher,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

    def test_visite_sans_rien_renseigne_naffiche_que_la_date(self):
        Visite.objects.create(colonie=self.colonie, date=date(2026, 6, 25))

        reponse = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertContains(reponse, date_format(date(2026, 6, 25)))
        self.assertNotContains(reponse, "visite-detail")
        self.assertNotContains(reponse, "Couvain :")
        self.assertNotContains(reponse, "Abeilles :")

    def test_visite_partielle_naffiche_que_les_champs_renseignes(self):
        Visite.objects.create(
            colonie=self.colonie, date=date(2026, 6, 26), nb_cadres_couvain=5,
        )

        reponse = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertContains(reponse, "Couvain : 5 cadre")
        self.assertNotContains(reponse, "Abeilles :")
        self.assertNotContains(reponse, "Réserves :")
        self.assertNotContains(reponse, "Comportement :")


class ModifierVisiteTests(TestCase):
    """Modification d'une visite existante, par le même formulaire à
    boutons que la création — même gabarit, même classe de formulaire,
    mêmes champs (issue #48)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher modification")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=80, rucher=self.rucher,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

    def _donnees_minimales(self, **extra):
        donnees = {
            "date": "2026-07-01",
            "observation_reine": "",
            "nb_cadres_couvain": "",
            "nb_cadres_abeilles": "",
            "reserves": "",
            "comportement": "",
            "notes": "",
            "observation_essaimage": "",
            "reponse_cellules_royales": "",
            "observation_reine_morte": "",
            "date_reverification_reine_morte": "",
            "observation_pillage": "",
            "observation_frelons": "",
        }
        donnees.update(extra)
        return donnees

    def test_formulaire_de_modification_prerempli(self):
        visite = Visite.objects.create(
            colonie=self.colonie, date="2026-07-01", observation_reine="OEUFS_VUS",
            nb_cadres_couvain=6, notes="Belle colonie.",
        )
        ActionVisite.objects.create(visite=visite, type_action=TypeActionVisite.NOURRISSEMENT)

        reponse = self.client.get(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id])
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Modifier la visite")
        self.assertContains(reponse, "Belle colonie.")
        self.assertContains(reponse, 'value="6"')

    def test_formulaires_de_creation_et_de_modification_memes_champs(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")

        reponse_creation = self.client.get(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id])
        )
        reponse_modification = self.client.get(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id])
        )

        self.assertEqual(
            set(reponse_creation.context["form"].fields),
            set(reponse_modification.context["form"].fields),
        )

    def test_modification_avec_les_memes_champs_que_la_creation(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")

        reponse = self.client.post(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id]),
            self._donnees_minimales(
                date="2026-07-02", observation_reine="OEUFS_VUS",
                nb_cadres_couvain="7", nb_cadres_abeilles="9",
                reserves="BONNES", comportement="2", notes="RAS.",
            ),
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )
        visite.refresh_from_db()
        self.assertEqual(str(visite.date), "2026-07-02")
        self.assertEqual(visite.observation_reine, "OEUFS_VUS")
        self.assertEqual(visite.nb_cadres_couvain, 7)
        self.assertEqual(visite.nb_cadres_abeilles, 9)
        self.assertEqual(visite.reserves, "BONNES")
        self.assertEqual(visite.comportement, 2)
        self.assertEqual(visite.notes, "RAS.")

    def test_observation_inchangee_garde_son_statut(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.PILLAGE,
            certitude=CertitudeObservation.CONSTATE,
            statut=StatutObservation.CONFIRMEE,
        )

        self.client.post(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id]),
            self._donnees_minimales(observation_pillage=CertitudeObservation.CONSTATE),
        )

        observation.refresh_from_db()
        self.assertEqual(observation.statut, StatutObservation.CONFIRMEE)

    def test_observation_ajoutee_est_ouverte(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")

        self.client.post(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id]),
            self._donnees_minimales(observation_frelons=CertitudeObservation.DOUTE),
        )

        observation = ObservationVisite.objects.get(
            visite=visite, type_observation=TypeObservationVisite.FRELONS,
        )
        self.assertEqual(observation.statut, StatutObservation.OUVERTE)

    def test_observation_retiree_supprime_aussi_son_rappel(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        rappel_id = observation.rappel.id

        self.client.post(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id]),
            self._donnees_minimales(),
        )

        self.assertFalse(ObservationVisite.objects.filter(id=observation.id).exists())
        self.assertFalse(RappelRevisite.objects.filter(id=rappel_id).exists())

    def test_modification_de_la_date_de_reverification_sans_doublon(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )

        self.client.post(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id]),
            self._donnees_minimales(
                observation_reine_morte=CertitudeObservation.DOUTE,
                date_reverification_reine_morte="2026-07-15",
            ),
        )

        self.assertEqual(
            RappelRevisite.objects.filter(observation=observation).count(), 1,
        )
        rappel = RappelRevisite.objects.get(observation=observation)
        self.assertEqual(str(rappel.date_revisite), "2026-07-15")

    def test_actions_remplacees_a_la_modification(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")
        ActionVisite.objects.create(visite=visite, type_action=TypeActionVisite.NOURRISSEMENT)

        self.client.post(
            reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id]),
            self._donnees_minimales(actions=[TypeActionVisite.HAUSSE_AJOUTEE]),
        )

        self.assertEqual(
            set(visite.actions.values_list("type_action", flat=True)),
            {TypeActionVisite.HAUSSE_AJOUTEE},
        )

    def test_bouton_modifier_affiche_dans_lhistorique(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-07-01")

        reponse = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertContains(
            reponse, reverse("gestion:modifier_visite", args=[self.colonie.id, visite.id]),
        )


class SupprimerVisiteTests(TestCase):
    """Suppression d'une visite derrière une page de confirmation
    explicite : rien n'est supprimé sans cette confirmation (issue
    #48)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher suppression")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=90, rucher=self.rucher,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        self.visite = Visite.objects.create(colonie=self.colonie, date="2026-07-05")
        self.observation = ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        self.rappel_id = self.observation.rappel.id

    def test_page_de_confirmation_naffiche_pas_de_suppression(self):
        reponse = self.client.get(
            reverse("gestion:supprimer_visite", args=[self.colonie.id, self.visite.id])
        )

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Supprimer")
        self.assertTrue(Visite.objects.filter(id=self.visite.id).exists())

    def test_sans_confirmation_rien_nest_supprime(self):
        self.client.get(
            reverse("gestion:supprimer_visite", args=[self.colonie.id, self.visite.id])
        )

        self.assertTrue(Visite.objects.filter(id=self.visite.id).exists())
        self.assertTrue(ObservationVisite.objects.filter(id=self.observation.id).exists())
        self.assertTrue(RappelRevisite.objects.filter(id=self.rappel_id).exists())

    def test_confirmation_supprime_visite_actions_observations_et_rappels(self):
        ActionVisite.objects.create(visite=self.visite, type_action=TypeActionVisite.TRAITEMENT)

        reponse = self.client.post(
            reverse("gestion:supprimer_visite", args=[self.colonie.id, self.visite.id])
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )
        self.assertFalse(Visite.objects.filter(id=self.visite.id).exists())
        self.assertFalse(ObservationVisite.objects.filter(id=self.observation.id).exists())
        self.assertFalse(RappelRevisite.objects.filter(id=self.rappel_id).exists())
        self.assertFalse(ActionVisite.objects.filter(visite_id=self.visite.id).exists())


class AffichageObservationsTests(TestCase):
    """Affichage des observations dans l'historique des visites : la
    certitude (constaté/doute) n'a de sens que pour une observation
    encore ouverte — confirmée ou infirmée, c'est le statut qui prime,
    pas la certitude d'origine (issue #50)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher affichage observations")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=100, rucher=self.rucher,
        )
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        self.visite = Visite.objects.create(colonie=self.colonie, date="2026-08-01")

    def _historique(self):
        return self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

    def test_observation_ouverte_affichee_avec_sa_certitude(self):
        ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.PILLAGE,
            certitude=CertitudeObservation.DOUTE,
        )

        reponse = self._historique()

        self.assertContains(reponse, "Pillage")
        self.assertContains(reponse, "(doute)")

    def test_observation_confirmee_affichee_sans_doute(self):
        observation = ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        observation.confirmer()

        reponse = self._historique()

        self.assertContains(reponse, "(confirmée)")
        self.assertNotContains(reponse, "doute")

    def test_observation_infirmee_attenuee_et_sans_mention_de_certitude(self):
        observation = ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.FRELONS,
            certitude=CertitudeObservation.CONSTATE,
        )
        observation.infirmer()

        reponse = self._historique()

        self.assertContains(reponse, "(infirmée)")
        self.assertContains(reponse, "statut-infirmee")
        self.assertNotContains(reponse, "constaté")

    def test_confirmation_depuis_la_fiche_fixe_la_certitude_a_constate(self):
        observation = ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.PILLAGE,
            certitude=CertitudeObservation.DOUTE,
        )

        self.client.post(
            reverse("gestion:confirmer_observation", args=[observation.id])
        )

        observation.refresh_from_db()
        self.assertEqual(observation.certitude, CertitudeObservation.CONSTATE)

    def test_confirmation_par_visite_suivante_fixe_aussi_la_certitude(self):
        observation = ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )

        self.client.post(
            reverse("gestion:nouvelle_visite", args=[self.colonie.id]),
            {"date": "2026-08-10", "couvain_ouvert_present": "non"},
        )

        observation.refresh_from_db()
        self.assertEqual(observation.statut, StatutObservation.CONFIRMEE)
        self.assertEqual(observation.certitude, CertitudeObservation.CONSTATE)

    def test_infirmation_garde_la_certitude_telle_quelle(self):
        observation = ObservationVisite.objects.create(
            visite=self.visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.ESSAIMAGE,
            certitude=CertitudeObservation.DOUTE,
        )

        self.client.post(
            reverse("gestion:infirmer_observation", args=[observation.id])
        )

        observation.refresh_from_db()
        self.assertEqual(observation.certitude, CertitudeObservation.DOUTE)


class SignalReineMorteTests(TestCase):
    """Couronne barrée sur la tuile et mention sur la fiche colonie pour
    une reine morte confirmée sans remplaçante enregistrée depuis
    (issue #50)."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher signal reine morte")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=110, rucher=self.rucher,
        )
        self.reine = Reine.objects.create(identifiant="R-SIGNAL-1")
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, reine_actuelle=self.reine,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

    def _confirmer_reine_morte(self, date_visite):
        visite = Visite.objects.create(colonie=self.colonie, date=date_visite)
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        observation.confirmer()
        return observation

    def test_signal_affiche_sur_la_tuile_et_la_fiche(self):
        self._confirmer_reine_morte("2026-09-01")

        accueil = self.client.get(reverse("gestion:accueil"))
        fiche = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertContains(accueil, "icone-reine-morte", count=1)
        self.assertContains(accueil, "Reine morte confirmée")
        self.assertNotContains(accueil, "(morte)")
        self.assertNotContains(accueil, "tuile-signal-reine-morte")
        self.assertNotContains(accueil, "pastille-marquage")
        self.assertContains(fiche, "Reine morte confirmée le")

    def test_pas_de_signal_pour_observation_ouverte(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-09-02")
        ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )

        accueil = self.client.get(reverse("gestion:accueil"))

        self.assertNotContains(accueil, "icone-reine-morte")

    def test_pas_de_signal_pour_observation_infirmee(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-09-03")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        observation.infirmer()

        accueil = self.client.get(reverse("gestion:accueil"))

        self.assertNotContains(accueil, "icone-reine-morte")

    def test_signal_absent_apres_remerage_a_la_meme_date(self):
        self._confirmer_reine_morte("2026-09-04")
        EvenementColonie.objects.create(
            colonie=self.colonie, date="2026-09-04",
            type_evenement=TypeEvenementColonie.REMERAGE,
        )

        fiche = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertNotContains(fiche, "Reine morte confirmée le")

    def test_signal_absent_apres_remerage_posterieur(self):
        self._confirmer_reine_morte("2026-09-05")
        EvenementColonie.objects.create(
            colonie=self.colonie, date="2026-09-10",
            type_evenement=TypeEvenementColonie.REMERAGE,
        )

        fiche = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertNotContains(fiche, "Reine morte confirmée le")

    def test_signal_present_si_remerage_anterieur(self):
        self._confirmer_reine_morte("2026-09-15")
        EvenementColonie.objects.create(
            colonie=self.colonie, date="2026-09-10",
            type_evenement=TypeEvenementColonie.REMERAGE,
        )

        fiche = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertContains(fiche, "Reine morte confirmée le")

    def test_colonie_sans_observation_sans_erreur(self):
        accueil = self.client.get(reverse("gestion:accueil"))
        fiche = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertEqual(accueil.status_code, 200)
        self.assertEqual(fiche.status_code, 200)
        self.assertNotContains(fiche, "Reine morte confirmée le")


class NouvelleReineFormulaireTests(TestCase):
    """Remplacement de reine depuis la fiche colonie (issue #51) : la
    reine actuelle est mise à jour, un événement de remérage est créé,
    l'ancienne reine est conservée telle quelle et le signal « reine
    morte » disparaît."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher remplacement")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=200, rucher=self.rucher,
        )
        self.ancienne_reine = Reine.objects.create(identifiant="R-REMPLACE-1")
        self.colonie = Colonie.objects.create(
            ruche=self.ruche, reine_actuelle=self.ancienne_reine,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

    def test_nouvelle_reine_achetee_avec_nouveau_vendeur(self):
        reponse = self.client.post(
            reverse("gestion:nouvelle_reine", args=[self.colonie.id]),
            {
                "date_remplacement": "2026-06-01",
                "origine": "NOUVELLE",
                "identifiant": "R-NOUVELLE-1",
                "mode_acquisition": ModeAcquisitionReine.ACHETEE_FECONDEE,
                "nouveau_vendeur_nom": "Rucher du Bois",
                "nouveau_vendeur_telephone": "0470 00 00 00",
                "statut": StatutReine.FECONDEE,
                "marquage_effectue": "non",
            },
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id]),
        )
        self.colonie.refresh_from_db()
        nouvelle_reine = self.colonie.reine_actuelle
        self.assertEqual(nouvelle_reine.identifiant, "R-NOUVELLE-1")
        self.assertEqual(
            nouvelle_reine.mode_acquisition, ModeAcquisitionReine.ACHETEE_FECONDEE,
        )
        self.assertIsNotNone(nouvelle_reine.vendeur)
        self.assertEqual(nouvelle_reine.vendeur.nom, "Rucher du Bois")
        self.assertEqual(nouvelle_reine.vendeur.telephone, "0470 00 00 00")
        self.assertEqual(Vendeur.objects.count(), 1)

        evenement = EvenementColonie.objects.get(
            colonie=self.colonie, type_evenement=TypeEvenementColonie.REMERAGE,
        )
        self.assertEqual(str(evenement.date), "2026-06-01")
        self.assertEqual(evenement.reine_id, nouvelle_reine.id)
        self.assertEqual(evenement.ancienne_reine_id, self.ancienne_reine.id)

        self.ancienne_reine.refresh_from_db()
        self.assertEqual(self.ancienne_reine.identifiant, "R-REMPLACE-1")

    def test_vendeur_deja_enregistre_reutilise_sans_doublon(self):
        vendeur = Vendeur.objects.create(nom="Vendeur existant")

        self.client.post(
            reverse("gestion:nouvelle_reine", args=[self.colonie.id]),
            {
                "date_remplacement": "2026-06-02",
                "origine": "NOUVELLE",
                "identifiant": "R-NOUVELLE-2",
                "mode_acquisition": ModeAcquisitionReine.ACHETEE_CR,
                "vendeur": vendeur.id,
                "marquage_effectue": "non",
            },
        )

        self.assertEqual(Vendeur.objects.count(), 1)
        self.colonie.refresh_from_db()
        self.assertEqual(self.colonie.reine_actuelle.vendeur_id, vendeur.id)

    def test_reine_existante_non_affectee_devient_reine_actuelle(self):
        reine_libre = Reine.objects.create(identifiant="R-LIBRE-1")

        reponse = self.client.post(
            reverse("gestion:nouvelle_reine", args=[self.colonie.id]),
            {
                "date_remplacement": "2026-06-03",
                "origine": "EXISTANTE",
                "reine_existante": reine_libre.id,
                "marquage_effectue": "non",
            },
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id]),
        )
        self.colonie.refresh_from_db()
        self.assertEqual(self.colonie.reine_actuelle_id, reine_libre.id)
        self.assertEqual(Reine.objects.count(), 2)

    def test_reine_deja_affectee_a_une_colonie_active_non_proposee(self):
        autre_ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=201, rucher=self.rucher,
        )
        reine_active_ailleurs = Reine.objects.create(identifiant="R-AILLEURS-1")
        Colonie.objects.create(
            ruche=autre_ruche, reine_actuelle=reine_active_ailleurs,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        reine_libre = Reine.objects.create(identifiant="R-LIBRE-PROPOSEE")

        reponse = self.client.get(
            reverse("gestion:nouvelle_reine", args=[self.colonie.id]),
        )

        queryset_proposee = reponse.context["form"].fields["reine_existante"].queryset
        self.assertNotIn(reine_active_ailleurs, queryset_proposee)
        self.assertIn(reine_libre, queryset_proposee)

    def test_mode_acquisition_sans_achat_naccepte_pas_de_vendeur_requis(self):
        reponse = self.client.post(
            reverse("gestion:nouvelle_reine", args=[self.colonie.id]),
            {
                "date_remplacement": "2026-06-04",
                "origine": "NOUVELLE",
                "identifiant": "R-NOUVELLE-3",
                "mode_acquisition": ModeAcquisitionReine.ELEVEE,
                "marquage_effectue": "non",
            },
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[self.colonie.id]),
        )
        self.colonie.refresh_from_db()
        self.assertEqual(self.colonie.reine_actuelle.identifiant, "R-NOUVELLE-3")
        self.assertIsNone(self.colonie.reine_actuelle.vendeur)

    def test_achat_sans_vendeur_refuse(self):
        reponse = self.client.post(
            reverse("gestion:nouvelle_reine", args=[self.colonie.id]),
            {
                "date_remplacement": "2026-06-05",
                "origine": "NOUVELLE",
                "identifiant": "R-NOUVELLE-4",
                "mode_acquisition": ModeAcquisitionReine.ACHETEE_VIERGE,
                "marquage_effectue": "non",
            },
        )

        self.assertEqual(reponse.status_code, 200)
        self.colonie.refresh_from_db()
        self.assertEqual(self.colonie.reine_actuelle_id, self.ancienne_reine.id)

    def test_remplacement_fait_disparaitre_le_signal_reine_morte(self):
        visite = Visite.objects.create(colonie=self.colonie, date="2026-05-01")
        observation = ObservationVisite.objects.create(
            visite=visite, colonie=self.colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            certitude=CertitudeObservation.DOUTE,
        )
        observation.confirmer()
        fiche_avant = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )
        self.assertContains(fiche_avant, "Reine morte confirmée le")

        self.client.post(
            reverse("gestion:nouvelle_reine", args=[self.colonie.id]),
            {
                "date_remplacement": "2026-05-10",
                "origine": "NOUVELLE",
                "identifiant": "R-NOUVELLE-5",
                "mode_acquisition": ModeAcquisitionReine.ELEVEE,
                "marquage_effectue": "non",
            },
        )

        fiche_apres = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )
        self.assertNotContains(fiche_apres, "Reine morte confirmée le")

    def test_vendeur_affiche_dans_le_bloc_reine_de_la_fiche_colonie(self):
        vendeur = Vendeur.objects.create(nom="Apiculture du Nord")
        self.ancienne_reine.vendeur = vendeur
        self.ancienne_reine.save(update_fields=["vendeur"])

        fiche = self.client.get(
            reverse("gestion:fiche_colonie", args=[self.colonie.id])
        )

        self.assertContains(fiche, "Apiculture du Nord")


class MarquageReineTests(TestCase):
    """Marquage effectué sur une reine (issue #51) : pastille pleine ou
    vide selon le marquage, bouton « Marquer la reine », compteur et
    page « Reines à marquer »."""

    def setUp(self):
        self.rucher = Rucher.objects.create(nom="Rucher marquage")
        self.type_ruche = TypeRuche.objects.get(code="DADANT10")
        self.ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=210, rucher=self.rucher,
        )

    def test_pastille_vide_pour_reine_non_marquee(self):
        reine = Reine.objects.create(
            identifiant="R-NON-MARQUEE", couleur_marquage=CouleurMarquage.ROUGE,
        )
        Colonie.objects.create(
            ruche=self.ruche, reine_actuelle=reine,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        accueil = self.client.get(reverse("gestion:accueil"))

        self.assertContains(accueil, "pastille-marquage-vide")
        self.assertContains(accueil, "Non marquée")

    def test_pastille_pleine_pour_reine_marquee(self):
        reine = Reine.objects.create(
            identifiant="R-MARQUEE", couleur_marquage=CouleurMarquage.ROUGE,
            marquage_effectue=True, date_marquage="2026-04-01",
        )
        Colonie.objects.create(
            ruche=self.ruche, reine_actuelle=reine,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        accueil = self.client.get(reverse("gestion:accueil"))

        self.assertNotContains(accueil, "pastille-marquage-vide")
        self.assertContains(accueil, "Marquée")

    def test_bouton_marquer_la_reine_enregistre_marquage_et_date(self):
        reine = Reine.objects.create(identifiant="R-A-MARQUER-1")
        colonie = Colonie.objects.create(
            ruche=self.ruche, reine_actuelle=reine,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )

        reponse = self.client.post(
            reverse("gestion:marquer_reine", args=[reine.id]),
            {"date_marquage": "2026-07-14", "retour": f"colonie:{colonie.id}"},
        )

        self.assertRedirects(
            reponse, reverse("gestion:fiche_colonie", args=[colonie.id]),
        )
        reine.refresh_from_db()
        self.assertTrue(reine.marquage_effectue)
        self.assertEqual(str(reine.date_marquage), "2026-07-14")

    def test_compteur_et_page_reines_a_marquer_ne_listent_que_les_actives_non_marquees(self):
        reine_active_non_marquee = Reine.objects.create(identifiant="R-COMPTE-1")
        Colonie.objects.create(
            ruche=self.ruche, reine_actuelle=reine_active_non_marquee,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        autre_ruche = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=211, rucher=self.rucher,
        )
        reine_marquee = Reine.objects.create(
            identifiant="R-COMPTE-2", marquage_effectue=True,
        )
        Colonie.objects.create(
            ruche=autre_ruche, reine_actuelle=reine_marquee,
            mode_creation=ModeCreationColonie.ACHAT, active=True,
        )
        ruche_inactive = Ruche.objects.create(
            type_ruche=self.type_ruche, numero=212, rucher=self.rucher,
        )
        reine_colonie_inactive = Reine.objects.create(identifiant="R-COMPTE-3")
        Colonie.objects.create(
            ruche=ruche_inactive, reine_actuelle=reine_colonie_inactive,
            mode_creation=ModeCreationColonie.ACHAT, active=False,
        )

        accueil = self.client.get(reverse("gestion:accueil"))
        self.assertContains(accueil, "1 reine non marquée")

        page = self.client.get(reverse("gestion:reines_a_marquer"))
        self.assertContains(page, "R-COMPTE-1")
        self.assertNotContains(page, "R-COMPTE-2")
        self.assertNotContains(page, "R-COMPTE-3")
