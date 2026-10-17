"""Visite d'une colonie et observations associées (issue #43).

Lié à `Colonie` par clé étrangère. `Colonie` est pour l'instant défini
dans `selection` (cf. gestion/apps.py : « définis dans selection pour
l'instant »), donc ce module en dépend en lecture — c'est la même
exception, déjà en place dans `gestion.views`, à la règle de
dépendance à sens unique (CONTEXTE.md), en attendant que les modèles
de colonie soient déplacés dans `gestion`.

Portabilité : uniquement des types de champs standard de l'ORM
Django, aucun SQL propre à PostgreSQL (cf. CONTEXTE.md).
"""

from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date

from selection.models import Colonie

DELAI_RAPPEL_REINE_MORTE_JOURS = 9


class Vendeur(models.Model):
    """Vendeur d'une reine achetée (issue #51). Défini ici (gestion)
    plutôt que dans `selection`, pour que ce soit `Reine` (dans
    `selection`) qui référence `Vendeur` par une clé étrangère
    différée ("gestion.Vendeur") — jamais l'inverse : ce module reste
    sans import de `selection` au-delà de l'exception `Colonie`
    ci-dessus, déjà documentée, et aucune dépendance circulaire n'est
    créée entre les migrations des deux applications."""

    nom = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Vendeur"
        verbose_name_plural = "Vendeurs"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class ObservationReine(models.TextChoices):
    VUE = "VUE", "Vue"
    OEUFS_VUS = "OEUFS_VUS", "Œufs vus"
    RIEN_VU = "RIEN_VU", "Rien vu"


class NiveauReserves(models.TextChoices):
    FAIBLES = "FAIBLES", "Faibles"
    CORRECTES = "CORRECTES", "Correctes"
    BONNES = "BONNES", "Bonnes"


class Comportement(models.IntegerChoices):
    CALME = 1, "Calme"
    NORMAL = 2, "Normale"
    NERVEUSE = 3, "Nerveuse"
    AGRESSIVE = 4, "Agressive"


class Visite(models.Model):
    """Visite (inspection) d'une colonie, saisie depuis sa fiche. Tous
    les champs sont facultatifs sauf la colonie et la date."""

    colonie = models.ForeignKey(
        Colonie, on_delete=models.CASCADE, related_name="visites",
    )
    date = models.DateField(default=timezone.localdate)
    observation_reine = models.CharField(
        max_length=20, choices=ObservationReine.choices, blank=True,
    )
    nb_cadres_couvain = models.PositiveSmallIntegerField(null=True, blank=True)
    nb_cadres_abeilles = models.PositiveSmallIntegerField(null=True, blank=True)
    reserves = models.CharField(
        max_length=20, choices=NiveauReserves.choices, blank=True,
    )
    comportement = models.PositiveSmallIntegerField(
        choices=Comportement.choices, null=True, blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Visite"
        verbose_name_plural = "Visites"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.colonie} — visite du {self.date}"

    def details_affichage(self):
        """Segments renseignés à afficher dans l'historique des
        visites : seuls les champs effectivement remplis apparaissent,
        une visite sans aucun ne montre que sa date (issue #45)."""
        segments = []
        if self.observation_reine:
            segments.append(f"Reine : {self.get_observation_reine_display()}")
        if self.nb_cadres_couvain is not None:
            pluriel = "s" if self.nb_cadres_couvain != 1 else ""
            segments.append(f"Couvain : {self.nb_cadres_couvain} cadre{pluriel}")
        if self.nb_cadres_abeilles is not None:
            pluriel = "s" if self.nb_cadres_abeilles != 1 else ""
            segments.append(f"Abeilles : {self.nb_cadres_abeilles} cadre{pluriel}")
        if self.reserves:
            segments.append(f"Réserves : {self.get_reserves_display()}")
        if self.comportement is not None:
            segments.append(f"Comportement : {self.get_comportement_display()}")
        return segments


class TypeActionVisite(models.TextChoices):
    HAUSSE_AJOUTEE = "HAUSSE_AJOUTEE", "Hausse ajoutée"
    HAUSSE_RETIREE = "HAUSSE_RETIREE", "Hausse retirée"
    NOURRISSEMENT = "NOURRISSEMENT", "Nourrissement"
    TRAITEMENT = "TRAITEMENT", "Traitement"
    SUPPRESSION_CR = "SUPPRESSION_CR", "Suppression des cellules royales"


class ActionVisite(models.Model):
    """Une action faite pendant une visite (plusieurs possibles)."""

    visite = models.ForeignKey(
        Visite, on_delete=models.CASCADE, related_name="actions",
    )
    type_action = models.CharField(max_length=20, choices=TypeActionVisite.choices)

    class Meta:
        verbose_name = "Action de visite"
        verbose_name_plural = "Actions de visite"

    def __str__(self):
        return self.get_type_action_display()


class TypeObservationVisite(models.TextChoices):
    ESSAIMAGE = "ESSAIMAGE", "Colonie essaimée"
    REINE_MORTE = "REINE_MORTE", "Reine morte"
    PILLAGE = "PILLAGE", "Pillage"
    FRELONS = "FRELONS", "Frelons"


class CertitudeObservation(models.TextChoices):
    CONSTATE = "CONSTATE", "Constaté"
    DOUTE = "DOUTE", "Doute"


class StatutObservation(models.TextChoices):
    OUVERTE = "OUVERTE", "Ouverte"
    CONFIRMEE = "CONFIRMEE", "Confirmée"
    INFIRMEE = "INFIRMEE", "Infirmée"


class ReponseCellulesRoyales(models.TextChoices):
    TOUTES_SAUF_UNE = "TOUTES_SAUF_UNE", "Toutes supprimées sauf une"
    TOUTES = "TOUTES", "Toutes supprimées"
    PAS_ENCORE = "PAS_ENCORE", "Pas encore supprimées"


class ObservationVisite(models.Model):
    """Observation rattachée à une visite (plusieurs possibles par
    visite). Une observation en doute reste « ouverte » jusqu'à
    confirmation ou infirmation — à la main depuis la fiche colonie
    pour toutes, ou automatiquement pour « reine morte » via le
    rappel de revérification (cf. RappelRevisite)."""

    visite = models.ForeignKey(
        Visite, on_delete=models.CASCADE, related_name="observations",
    )
    colonie = models.ForeignKey(
        Colonie, on_delete=models.CASCADE, related_name="observations_visite",
        help_text="Dénormalisé depuis la visite, pour retrouver "
                   "directement les observations ouvertes d'une colonie.",
    )
    type_observation = models.CharField(
        max_length=20, choices=TypeObservationVisite.choices,
    )
    certitude = models.CharField(max_length=20, choices=CertitudeObservation.choices)
    statut = models.CharField(
        max_length=20, choices=StatutObservation.choices,
        default=StatutObservation.OUVERTE,
    )
    reponse_cellules_royales = models.CharField(
        max_length=20, choices=ReponseCellulesRoyales.choices, blank=True,
        help_text="Pour une observation d'essaimage uniquement.",
    )

    class Meta:
        verbose_name = "Observation de visite"
        verbose_name_plural = "Observations de visite"
        ordering = ["-visite__date", "-id"]

    def __str__(self):
        return (
            f"{self.get_type_observation_display()} "
            f"({self.get_certitude_display()}) — {self.colonie}"
        )

    def confirmer(self):
        """Une fois confirmée, le doute initial est levé : la
        certitude passe à « constaté » pour garder des données
        cohérentes (une observation confirmée ne peut plus être « en
        doute », issue #50)."""
        self.statut = StatutObservation.CONFIRMEE
        self.certitude = CertitudeObservation.CONSTATE
        self.save(update_fields=["statut", "certitude"])

    def infirmer(self):
        self.statut = StatutObservation.INFIRMEE
        self.save(update_fields=["statut"])

    def libelle_statut_affichage(self):
        """Partie affichée après le type d'observation, dans
        l'historique des visites et la fiche colonie (issue #50) : la
        certitude au moment de l'observation (constaté/doute) n'a de
        sens que tant qu'elle reste ouverte — une fois confirmée ou
        infirmée, c'est le statut qui prime, pas la certitude
        d'origine."""
        if self.statut == StatutObservation.OUVERTE:
            return self.get_certitude_display().lower()
        return self.get_statut_display().lower()

    def save(self, *args, **kwargs):
        """La colonie d'une observation est toujours celle de sa
        visite : jamais demandée au formulaire (admin ou autre), pour
        éviter l'erreur de contrainte NOT NULL constatée depuis
        l'administration (issue #45)."""
        self.colonie_id = self.visite.colonie_id
        super().save(*args, **kwargs)
        self._creer_rappel_si_necessaire()

    def _creer_rappel_si_necessaire(self):
        """Une « reine morte » en doute et ouverte reçoit son rappel de
        revérification dès sa création, quelle que soit l'origine
        (formulaire à boutons, administration...). `get_or_create` sur
        la relation un-à-un évite tout doublon si l'observation est
        ré-enregistrée (issue #45)."""
        if (
            self.type_observation == TypeObservationVisite.REINE_MORTE
            and self.certitude == CertitudeObservation.DOUTE
            and self.statut == StatutObservation.OUVERTE
        ):
            RappelRevisite.objects.get_or_create(
                observation=self,
                defaults={"date_revisite": date_revisite_par_defaut(self.visite.date)},
            )


class RappelRevisite(models.Model):
    """Rappel de revérification automatique pour une observation
    « reine morte » en doute : date de la visite + 9 jours par défaut
    (modifiable à la saisie). Marqué traité à la confirmation ou à
    l'infirmation de l'observation d'origine."""

    observation = models.OneToOneField(
        ObservationVisite, on_delete=models.CASCADE, related_name="rappel",
    )
    date_revisite = models.DateField()
    traite = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Rappel de revérification"
        verbose_name_plural = "Rappels de revérification"
        ordering = ["date_revisite"]

    def __str__(self):
        return f"Revérifier {self.observation} le {self.date_revisite}"


def date_revisite_par_defaut(date_visite):
    """Date de revérification par défaut pour une « reine morte » en
    doute : date de la visite + 9 jours (modifiable à la saisie).
    Accepte aussi une date au format ISO (ex. `Visite.date` assignée
    comme chaîne avant tout rechargement depuis la base)."""
    if isinstance(date_visite, str):
        date_visite = parse_date(date_visite)
    return date_visite + timedelta(days=DELAI_RAPPEL_REINE_MORTE_JOURS)


# --- Stocks : matériel et consommables (issue #55) ---
#
# Étape 1 du suivi des stocks (matériel et consommables). Le modèle
# prévoit sans les exploiter encore un numéro de lot et une date de
# péremption sur le mouvement, pour l'étape 2 (produits de
# traitement). Le stock d'un article n'est jamais stocké : toujours
# recalculé comme la somme de ses mouvements (cf. `Article.stock`),
# pour qu'aucune correction manuelle du total ne puisse diverger de
# son historique.


class FamilleMateriel(models.Model):
    """Petit référentiel modifiable (ex. Ruche 10 cadres, Ruchette 6
    cadres, Miniplus, Apidea), pour filtrer les articles compatibles
    avec un type de boîte donné."""

    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Famille de matériel"
        verbose_name_plural = "Familles de matériel"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class RubriqueArticle(models.TextChoices):
    RUCHE = "RUCHE", "Ruche et ruchette"
    ELEVAGE = "ELEVAGE", "Élevage"
    VISITE = "VISITE", "Visite"
    ATELIER = "ATELIER", "Atelier"
    RECOLTE = "RECOLTE", "Récolte"
    AUTRE = "AUTRE", "Autre"


class NatureArticle(models.TextChoices):
    DURABLE = "DURABLE", "Matériel durable"
    CONSOMMABLE = "CONSOMMABLE", "Consommable"


class MotifMouvement(models.TextChoices):
    STOCK_INITIAL = "STOCK_INITIAL", "Stock initial"
    ACHAT = "ACHAT", "Achat"
    UTILISATION = "UTILISATION", "Utilisation"
    PERTE = "PERTE", "Perte ou casse"
    DON_VENTE = "DON_VENTE", "Don ou vente"
    CORRECTION = "CORRECTION", "Correction d'inventaire"


class Article(models.Model):
    """Article de matériel ou de consommable suivi en stock. Reconnu,
    pour le chargement du catalogue de départ, par son nom et sa
    rubrique. Une pièce commune à plusieurs types de boîtes n'existe
    qu'une fois, compatible avec chacune des familles concernées
    (`familles_compatibles`) — une pièce sans famille compatible
    n'est simplement pas filtrable par famille (ex. matériel de
    visite)."""

    nom = models.CharField(max_length=150)
    rubrique = models.CharField(max_length=20, choices=RubriqueArticle.choices)
    nature = models.CharField(max_length=20, choices=NatureArticle.choices)
    unite = models.CharField(max_length=30, help_text="Pièce, bobine, feuille, flacon, kg, litre…")
    seuil_alerte = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Badge « Stock bas » si le stock descend sous ce seuil.",
    )
    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    familles_compatibles = models.ManyToManyField(
        FamilleMateriel, related_name="articles", blank=True,
    )

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["rubrique", "nom"]
        unique_together = [["nom", "rubrique"]]

    def __str__(self):
        return self.nom

    @property
    def stock(self):
        total = self.mouvements.aggregate(total=Sum("quantite"))["total"]
        return total if total is not None else Decimal("0")

    @property
    def stock_bas(self):
        return self.seuil_alerte is not None and self.stock < self.seuil_alerte

    @property
    def stock_negatif(self):
        return self.stock < 0


class MouvementStock(models.Model):
    """Mouvement de stock d'un article : quantité signée (entrée
    positive, sortie négative). Le stock affiché n'est jamais qu'une
    somme de mouvements — on ne modifie jamais directement un total
    (cf. `Article.stock`). `numero_lot` et `date_peremption` sont
    prévus pour l'étape 2 (produits de traitement) sans être exploités
    pour l'instant."""

    article = models.ForeignKey(
        Article, on_delete=models.PROTECT, related_name="mouvements",
    )
    date = models.DateField(default=timezone.localdate)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    motif = models.CharField(max_length=20, choices=MotifMouvement.choices)
    note = models.CharField(max_length=255, blank=True)
    numero_lot = models.CharField(max_length=100, blank=True)
    date_peremption = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ["-date", "-id"]

    def __str__(self):
        signe = "+" if self.quantite >= 0 else ""
        return f"{self.article} : {signe}{self.quantite} ({self.get_motif_display()})"
