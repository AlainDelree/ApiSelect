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
    ModeCreationColonie,
    Reine,
    Ruche,
    Rucher,
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
    """Ajout d'une visite avec observation « reine morte » en doute
    depuis l'administration (issue #45) : plus d'erreur de contrainte
    NOT NULL sur la colonie, rappel créé automatiquement."""

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

    def _donnees_formulaire(self, **observation_overrides):
        donnees = {
            "colonie": self.colonie.id,
            "date": "2026-06-10",
            "observation_reine": "",
            "nb_cadres_couvain": "",
            "nb_cadres_abeilles": "",
            "reserves": "",
            "comportement": "",
            "notes": "",
            "actions-TOTAL_FORMS": "0",
            "actions-INITIAL_FORMS": "0",
            "actions-MIN_NUM_FORMS": "0",
            "actions-MAX_NUM_FORMS": "1000",
            "observations-TOTAL_FORMS": "1",
            "observations-INITIAL_FORMS": "0",
            "observations-MIN_NUM_FORMS": "0",
            "observations-MAX_NUM_FORMS": "1000",
            "observations-0-type_observation": TypeObservationVisite.REINE_MORTE,
            "observations-0-certitude": CertitudeObservation.DOUTE,
            "observations-0-statut": StatutObservation.OUVERTE,
            "observations-0-reponse_cellules_royales": "",
            "_save": "Enregistrer",
        }
        donnees.update(observation_overrides)
        return donnees

    def test_ajout_visite_avec_reine_morte_en_doute_sans_erreur(self):
        reponse = self.client.post(
            reverse("admin:gestion_visite_add"), self._donnees_formulaire(),
        )

        self.assertEqual(reponse.status_code, 302)
        visite = Visite.objects.get(colonie=self.colonie)
        observation = ObservationVisite.objects.get(visite=visite)
        self.assertEqual(observation.colonie_id, self.colonie.id)
        self.assertEqual(
            RappelRevisite.objects.filter(observation=observation).count(), 1,
        )
        rappel = RappelRevisite.objects.get(observation=observation)
        self.assertEqual(
            rappel.date_revisite,
            date(2026, 6, 10) + timedelta(days=DELAI_RAPPEL_REINE_MORTE_JOURS),
        )

    def test_rappel_modifiable_apres_coup_dans_ladmin(self):
        self.client.post(reverse("admin:gestion_visite_add"), self._donnees_formulaire())
        rappel = RappelRevisite.objects.get(observation__visite__colonie=self.colonie)

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
