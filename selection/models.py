from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# ---------------------------------------------------------------------------
# Rucher / Ruche
# ---------------------------------------------------------------------------

class Rucher(models.Model):
    """Emplacement géographique accueillant des ruches."""

    nom = models.CharField(max_length=100, unique=True)
    localisation = models.CharField(
        max_length=255, blank=True,
        help_text="Adresse ou description libre du lieu.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Rucher"
        verbose_name_plural = "Ruchers"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class TypeRuche(models.Model):
    """Table de référence des types de ruche (remplace l'ancien TextChoices).

    `alias` est un habillage d'affichage court (ex. "Ruche" pour Dadant 10) ;
    quand il est vide, l'affichage retombe sur `nom`. Éditable depuis l'admin
    Django sans migration de code (cf. CONTEXTE.md — l'alias n'est jamais un
    identifiant fonctionnel).
    """

    code = models.SlugField(
        max_length=20, unique=True,
        help_text="Code technique stable (ex. DADANT10), utilisé en base et "
                   "par les migrations de données. Ne pas modifier après coup.",
    )
    nom = models.CharField(max_length=100, help_text="Nom complet (ex. Dadant 10).")
    alias = models.CharField(
        max_length=50, blank=True,
        help_text="Libellé court pour l'affichage courant (ex. Ruche). "
                   "Laisser vide pour utiliser le nom complet.",
    )
    numerotation_permanente = models.BooleanField(
        default=False,
        help_text="Coché si Type + numéro forment une identité stable dans "
                   "le temps (une planche physique donnée porte toujours le "
                   "même numéro), comme Dadant 10/Ruchette 6. Décoché pour "
                   "une numérotation réutilisable sans identité permanente "
                   "sur les planches, comme Apidea/DH.",
    )

    class Meta:
        verbose_name = "Type de ruche"
        verbose_name_plural = "Types de ruche"
        ordering = ["nom"]

    def __str__(self):
        return self.libelle_affichage

    @property
    def libelle_affichage(self):
        return self.alias if self.alias else self.nom


class Ruche(models.Model):
    """Boîte physique. Type + numéro forment son identité (cf. Meta.clean)."""

    type_ruche = models.ForeignKey(
        TypeRuche, on_delete=models.PROTECT, related_name="ruches",
    )
    numero = models.PositiveIntegerField()
    rucher = models.ForeignKey(
        Rucher, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ruches",
        help_text="Emplacement physique actuel de la boîte.",
    )
    actif = models.BooleanField(
        default=True,
        help_text="Décoché si la boîte est retirée du service (cassée, "
                   "remplacée...). Permet la réutilisation du numéro pour "
                   "les types Apidea/DH sans supprimer l'historique.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Ruche"
        verbose_name_plural = "Ruches"
        ordering = ["type_ruche__nom", "numero"]

    def __str__(self):
        return f"{self.type_ruche.libelle_affichage} {self.numero}"

    def clean(self):
        if self.type_ruche_id and self.type_ruche.numerotation_permanente:
            doublons = Ruche.objects.filter(
                type_ruche=self.type_ruche, numero=self.numero, actif=True,
            )
            if self.pk:
                doublons = doublons.exclude(pk=self.pk)
            if doublons.exists():
                raise ValidationError(
                    f"Une ruche active {self.type_ruche.libelle_affichage} "
                    f"{self.numero} existe déjà (numérotation permanente "
                    f"pour ce type)."
                )


# ---------------------------------------------------------------------------
# Reine
# ---------------------------------------------------------------------------

class CouleurMarquage(models.TextChoices):
    BLANC = "BLANC", "Blanc (années en 1 ou 6)"
    JAUNE = "JAUNE", "Jaune (années en 2 ou 7)"
    ROUGE = "ROUGE", "Rouge (années en 3 ou 8)"
    VERT = "VERT", "Vert (années en 4 ou 9)"
    BLEU = "BLEU", "Bleu (années en 5 ou 0)"


class StationFecondation(models.Model):
    """Lieu de fécondation des reines (station collective ou site propre)."""

    nom = models.CharField(max_length=100, unique=True)
    lieu = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Station de fécondation"
        verbose_name_plural = "Stations de fécondation"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Reine(models.Model):
    """Identité généalogique d'une reine, indépendante de la boîte."""

    identifiant = models.CharField(
        max_length=50, unique=True,
        help_text="Étiquette libre (ex. R24-03).",
    )
    mere = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="filles",
    )
    lignee_male_probable = models.CharField(
        max_length=255, blank=True,
        help_text="Description libre de la lignée mâle probable "
                   "(fécondation en vol = probabiliste).",
    )
    station_fecondation = models.ForeignKey(
        StationFecondation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reines",
    )
    couleur_marquage = models.CharField(
        max_length=10, choices=CouleurMarquage.choices, blank=True,
    )
    date_naissance = models.DateField(null=True, blank=True)
    date_deces = models.DateField(
        null=True, blank=True,
        help_text="Renseigné si la reine est morte ou a été remplacée.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Reine"
        verbose_name_plural = "Reines"
        ordering = ["-date_naissance", "identifiant"]

    def __str__(self):
        return self.identifiant


# ---------------------------------------------------------------------------
# Colonie
# ---------------------------------------------------------------------------

class ModeCreationColonie(models.TextChoices):
    ACHAT = "ACHAT", "Achat"
    ESSAIMAGE_NATUREL = "ESSAIMAGE_NATUREL", "Essaimage naturel"
    ESSAIM_ARTIFICIEL = "ESSAIM_ARTIFICIEL", "Essaim artificiel"
    ORIGINE_INCONNUE = "ORIGINE_INCONNUE", "Origine inconnue"


class Colonie(models.Model):
    """Population vivante à un instant donné, liée à une ruche."""

    ruche = models.ForeignKey(
        Ruche, on_delete=models.PROTECT, related_name="colonies",
        help_text="Boîte physique actuellement occupée.",
    )
    reine_actuelle = models.ForeignKey(
        Reine, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="colonie_dirigee",
        help_text="Reine actuellement à la tête de la colonie.",
    )
    mode_creation = models.CharField(
        max_length=20, choices=ModeCreationColonie.choices,
    )
    date_creation = models.DateField()
    active = models.BooleanField(
        default=True,
        help_text="Décoché si la colonie n'existe plus (mortalité, "
                   "réunion avec une autre colonie...).",
    )
    date_fin = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Colonie"
        verbose_name_plural = "Colonies"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Colonie #{self.pk} ({self.ruche})"


class ConfigurationColonie(models.Model):
    """Historique de configuration matérielle (corps + hausses) d'une colonie."""

    colonie = models.ForeignKey(
        Colonie, on_delete=models.CASCADE, related_name="configurations",
    )
    date = models.DateField()
    nb_corps = models.PositiveSmallIntegerField(default=1)
    nb_hausses = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Configuration de colonie"
        verbose_name_plural = "Configurations de colonie"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.colonie} — {self.date} ({self.nb_corps}c/{self.nb_hausses}h)"


class TypeEvenementColonie(models.TextChoices):
    CREATION = "CREATION", "Création"
    DEMENAGEMENT = "DEMENAGEMENT", "Déménagement"
    REMERAGE = "REMERAGE", "Remérage"
    DIVISION = "DIVISION", "Division"
    REUNION = "REUNION", "Réunion avec une autre colonie"
    MORTALITE = "MORTALITE", "Mortalité"
    AUTRE = "AUTRE", "Autre"


class EvenementColonie(models.Model):
    """Historique de déménagement/remérage (et autres événements) d'une colonie."""

    colonie = models.ForeignKey(
        Colonie, on_delete=models.CASCADE, related_name="evenements",
    )
    date = models.DateField()
    type_evenement = models.CharField(
        max_length=20, choices=TypeEvenementColonie.choices,
    )
    ruche_destination = models.ForeignKey(
        Ruche, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
        help_text="Nouvelle boîte, pour un déménagement.",
    )
    reine = models.ForeignKey(
        Reine, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
        help_text="Nouvelle reine installée, pour un remérage.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Événement de colonie"
        verbose_name_plural = "Événements de colonie"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.colonie} — {self.get_type_evenement_display()} ({self.date})"


# ---------------------------------------------------------------------------
# Sélection génétique : campagnes, critères, poids, mesures
# ---------------------------------------------------------------------------

class CampagneElevage(models.Model):
    """Campagne d'élevage annuelle (ou multi-lignées/sites en parallèle)."""

    nom = models.CharField(max_length=100, unique=True)
    annee = models.PositiveIntegerField()
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Campagne d'élevage"
        verbose_name_plural = "Campagnes d'élevage"
        ordering = ["-annee", "nom"]

    def __str__(self):
        return self.nom


class TypeMesure(models.TextChoices):
    PASSE_RAPIDE = "PASSE_RAPIDE", "Passe rapide"
    PASSE_APPROFONDIE = "PASSE_APPROFONDIE", "Passe approfondie"


class CritereSelection(models.Model):
    """Un des critères de sélection mesurés (barème détaillé : cours CRISAB)."""

    code = models.SlugField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    type_mesure = models.CharField(max_length=20, choices=TypeMesure.choices)
    unite = models.CharField(
        max_length=20, blank=True,
        help_text="Unité de la valeur brute (kg, dm², min...), si applicable.",
    )
    description = models.TextField(blank=True)
    ordre = models.PositiveSmallIntegerField(
        default=0, help_text="Ordre d'affichage dans les tableaux/fiches.",
    )

    class Meta:
        verbose_name = "Critère de sélection"
        verbose_name_plural = "Critères de sélection"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom


class PoidsCritere(models.Model):
    """Poids (0-10) d'un critère pour une campagne donnée, historisé."""

    campagne = models.ForeignKey(
        CampagneElevage, on_delete=models.CASCADE, related_name="poids_criteres",
    )
    critere = models.ForeignKey(
        CritereSelection, on_delete=models.CASCADE, related_name="poids_par_campagne",
    )
    poids = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    seuil_eliminatoire = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Seuil éliminatoire optionnel, indépendant du poids "
                   "(ex. santé, agressivité).",
    )

    class Meta:
        verbose_name = "Poids de critère"
        verbose_name_plural = "Poids de critères"
        constraints = [
            models.UniqueConstraint(
                fields=["campagne", "critere"], name="unique_poids_par_campagne",
            ),
        ]
        ordering = ["campagne", "critere__ordre"]

    def __str__(self):
        return f"{self.critere} — {self.campagne} (poids {self.poids})"


class Mesure(models.Model):
    """Mesure brute d'un critère sur une colonie + score calculé (1-4)."""

    colonie = models.ForeignKey(
        Colonie, on_delete=models.CASCADE, related_name="mesures",
    )
    critere = models.ForeignKey(
        CritereSelection, on_delete=models.PROTECT, related_name="mesures",
    )
    campagne = models.ForeignKey(
        CampagneElevage, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mesures",
    )
    date_mesure = models.DateField()
    valeur_brute = models.CharField(
        max_length=100,
        help_text="Valeur brute relevée sur le terrain (numérique ou "
                   "descriptive selon le critère).",
    )
    score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Score 1-4 calculé selon le barème du cours "
                   "(non calculé automatiquement pour l'instant).",
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Mesure"
        verbose_name_plural = "Mesures"
        ordering = ["-date_mesure"]

    def __str__(self):
        return f"{self.colonie} — {self.critere} ({self.date_mesure})"


# ---------------------------------------------------------------------------
# Vues PostgreSQL en lecture seule (créées par migration RunSQL, cf.
# selection/migrations/0002_vues_sql.py). Ces modèles ne créent ni ne
# modifient de table (managed = False) : ce sont des vues, à faire évoluer
# uniquement via migration, jamais à la main dans pgAdmin.
# ---------------------------------------------------------------------------

class VueMesureComplete(models.Model):
    """Une ligne par mesure, jointure Colonie→Ruche→Rucher/Reine/Critère/
    PoidsCritere/Campagne aplatie (vue SQL `vue_mesures_completes`)."""

    mesure_id = models.BigIntegerField(primary_key=True)
    date_mesure = models.DateField()
    valeur_brute = models.CharField(max_length=100)
    score = models.PositiveSmallIntegerField(null=True)
    colonie_id = models.BigIntegerField()
    rucher_id = models.BigIntegerField(null=True)
    rucher_nom = models.CharField(max_length=100, null=True)
    ruche_id = models.BigIntegerField()
    ruche_identifiant = models.CharField(max_length=140)
    reine_id = models.BigIntegerField(null=True)
    reine_identifiant = models.CharField(max_length=50, null=True)
    critere_id = models.BigIntegerField()
    critere_code = models.SlugField(max_length=50)
    critere_nom = models.CharField(max_length=100)
    campagne_id = models.BigIntegerField(null=True)
    campagne_nom = models.CharField(max_length=100, null=True)
    poids = models.PositiveSmallIntegerField(null=True)
    seuil_eliminatoire = models.DecimalField(
        max_digits=6, decimal_places=2, null=True,
    )

    class Meta:
        managed = False
        db_table = "vue_mesures_completes"
        verbose_name = "Mesure complète (vue)"
        verbose_name_plural = "Mesures complètes (vue)"

    def __str__(self):
        return f"{self.critere_nom} — colonie #{self.colonie_id} ({self.date_mesure})"


class VueColonieActive(models.Model):
    """Colonies actives + Ruche/Rucher/Reine actuelle, un état courant par
    ligne (vue SQL `vue_colonies_actives`)."""

    colonie_id = models.BigIntegerField(primary_key=True)
    mode_creation = models.CharField(max_length=20)
    date_creation = models.DateField()
    ruche_id = models.BigIntegerField()
    ruche_identifiant = models.CharField(max_length=140)
    rucher_id = models.BigIntegerField(null=True)
    rucher_nom = models.CharField(max_length=100, null=True)
    reine_id = models.BigIntegerField(null=True)
    reine_identifiant = models.CharField(max_length=50, null=True)

    class Meta:
        managed = False
        db_table = "vue_colonies_actives"
        verbose_name = "Colonie active (vue)"
        verbose_name_plural = "Colonies actives (vue)"

    def __str__(self):
        return f"Colonie #{self.colonie_id} ({self.ruche_identifiant})"


class VueGenealogieReine(models.Model):
    """Chaîne mère → grand-mère → ... pour chaque reine, avec le niveau de
    génération (0 = la reine elle-même). Requête récursive WITH RECURSIVE
    (vue SQL `vue_genealogie_reines`)."""

    id = models.BigIntegerField(primary_key=True)
    reine_id = models.BigIntegerField()
    reine_identifiant = models.CharField(max_length=50)
    ancetre_id = models.BigIntegerField()
    ancetre_identifiant = models.CharField(max_length=50)
    generation = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = "vue_genealogie_reines"
        verbose_name = "Généalogie de reine (vue)"
        verbose_name_plural = "Généalogies de reines (vue)"

    def __str__(self):
        return f"{self.reine_identifiant} <- {self.ancetre_identifiant} (gen {self.generation})"
