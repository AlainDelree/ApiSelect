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

from django.db import models
from django.utils import timezone

from selection.models import Colonie

DELAI_RAPPEL_REINE_MORTE_JOURS = 9


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
        self.statut = StatutObservation.CONFIRMEE
        self.save(update_fields=["statut"])

    def infirmer(self):
        self.statut = StatutObservation.INFIRMEE
        self.save(update_fields=["statut"])


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
    doute : date de la visite + 9 jours (modifiable à la saisie)."""
    return date_visite + timedelta(days=DELAI_RAPPEL_REINE_MORTE_JOURS)
