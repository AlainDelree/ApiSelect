from datetime import date, timedelta

from django import forms
from django.contrib import admin, messages

from .calculs import suggerer_identifiant_fille
from .models import (
    CampagneElevage,
    CelluleRoyale,
    Colonie,
    ConfigurationColonie,
    CritereSelection,
    EtapeCalendrier,
    EvenementColonie,
    LotCriteres,
    Mesure,
    ModeAcquisitionReine,
    PoidsCritere,
    Reine,
    Ruche,
    Rucher,
    StationFecondation,
    StatutCelluleRoyale,
    StatutReine,
    TypeRuche,
)


@admin.register(Rucher)
class RucherAdmin(admin.ModelAdmin):
    list_display = ["nom", "localisation"]
    search_fields = ["nom", "localisation"]


@admin.register(TypeRuche)
class TypeRucheAdmin(admin.ModelAdmin):
    list_display = ["nom", "code", "alias", "numerotation_permanente"]
    list_editable = ["alias"]
    search_fields = ["nom", "code", "alias"]


@admin.register(Ruche)
class RucheAdmin(admin.ModelAdmin):
    list_display = ["__str__", "type_ruche", "numero", "rucher", "actif"]
    list_filter = ["type_ruche", "rucher", "actif"]
    list_editable = ["actif"]
    search_fields = ["numero"]
    autocomplete_fields = ["type_ruche"]


@admin.register(StationFecondation)
class StationFecondationAdmin(admin.ModelAdmin):
    list_display = ["nom", "lieu"]
    search_fields = ["nom", "lieu"]


@admin.register(Reine)
class ReineAdmin(admin.ModelAdmin):
    list_display = [
        "identifiant", "mere", "statut", "mode_acquisition",
        "couleur_marquage", "date_naissance", "date_fecondation",
        "station_fecondation", "date_deces",
    ]
    list_filter = [
        "statut", "mode_acquisition", "couleur_marquage", "station_fecondation",
    ]
    search_fields = ["identifiant", "lignee_male_probable"]
    autocomplete_fields = ["mere", "station_fecondation"]

    class Media:
        js = ["selection/admin/reine_date_naissance.js"]


class ConfigurationColonieInline(admin.TabularInline):
    model = ConfigurationColonie
    extra = 0


class EvenementColonieInline(admin.TabularInline):
    model = EvenementColonie
    extra = 0


@admin.register(Colonie)
class ColonieAdmin(admin.ModelAdmin):
    """`date_creation` est optionnelle (issue #29 : parfois inconnue pour
    une colonie déjà existante avant la reprise de l'élevage). Rien
    n'empêche pour autant une valeur incohérente avec la naissance de la
    reine actuelle (ex. date_creation saisie comme si elle correspondait
    à l'introduction de la reine plutôt qu'à la création réelle,
    potentiellement bien antérieure, de la colonie) : `save_model` pose
    alors un avertissement non bloquant (cf. docstring de la méthode)."""

    list_display = [
        "__str__", "ruche", "reine_actuelle", "mode_creation",
        "date_creation", "active",
    ]
    list_filter = ["mode_creation", "active", "ruche__type_ruche"]
    search_fields = ["ruche__numero", "reine_actuelle__identifiant"]
    autocomplete_fields = ["ruche", "reine_actuelle"]
    inlines = [ConfigurationColonieInline, EvenementColonieInline]

    DELAI_MINIMUM_AVANT_NAISSANCE_REINE = timedelta(days=30)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        reine = obj.reine_actuelle
        if (
            reine is None
            or reine.date_naissance is None
            or obj.date_creation is None
        ):
            return

        delai = reine.date_naissance - obj.date_creation
        if delai < self.DELAI_MINIMUM_AVANT_NAISSANCE_REINE:
            messages.warning(
                request,
                f"Date de création ({obj.date_creation}) incohérente avec "
                f"la naissance de la reine actuelle {reine.identifiant} "
                f"({reine.date_naissance}) : moins d'un mois d'écart (voire "
                "postérieure). Si la colonie existait déjà avant cette "
                "reine (remérage), corrigez la date de création — sinon "
                "ignorez cet avertissement. L'enregistrement a bien eu lieu.",
            )


class EtapeCalendrierInline(admin.TabularInline):
    """Étapes calculées automatiquement (cf. selection/signals.py) : la
    date prévue et le type d'étape sont en lecture seule ici.
    `ruche_origine`/`ruche_destination` (issue #25, remplace le champ
    unique `ruche` de l'issue #16) se saisissent à la main, leur usage
    dépendant de l'étape (cf. docstring EtapeCalendrier). Le suivi
    individuel des cellules royales (nombre, statut, Apidea) vit
    désormais dans CelluleRoyaleAdmin, plus dans cet inline."""

    model = EtapeCalendrier
    extra = 0
    fields = [
        "type_etape", "date_prevue", "realisee", "date_reelle",
        "ruche_origine", "ruche_destination", "notes",
    ]
    readonly_fields = ["type_etape", "date_prevue"]
    autocomplete_fields = ["ruche_origine", "ruche_destination"]
    can_delete = False
    ordering = ["date_prevue"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CampagneElevage)
class CampagneElevageAdmin(admin.ModelAdmin):
    list_display = [
        "nom", "annee", "lot_criteres", "date_reference", "date_debut",
        "date_fin", "elevage_males_actif", "taux_reussite_affichage",
    ]
    list_filter = ["annee", "elevage_males_actif", "lot_criteres"]
    search_fields = ["nom"]
    readonly_fields = ["taux_reussite_affichage"]
    autocomplete_fields = ["lot_criteres"]
    inlines = [EtapeCalendrierInline]

    @admin.display(description="Taux de réussite CR")
    def taux_reussite_affichage(self, obj):
        """CelluleRoyale devenues reine ÷ total des CelluleRoyale de la
        campagne (issue #25) — cf. CampagneElevage.taux_reussite."""
        taux = obj.taux_reussite
        if taux is None:
            return "non calculable"
        return f"{taux:.0%}"


@admin.register(EtapeCalendrier)
class EtapeCalendrierAdmin(admin.ModelAdmin):
    list_display = [
        "campagne", "type_etape", "date_prevue", "realisee", "date_reelle",
        "ruche_origine", "ruche_destination",
    ]
    list_filter = ["type_etape", "realisee", "campagne"]
    list_editable = ["realisee", "date_reelle"]
    search_fields = ["campagne__nom"]
    autocomplete_fields = ["campagne", "ruche_origine", "ruche_destination"]


@admin.register(CelluleRoyale)
class CelluleRoyaleAdmin(admin.ModelAdmin):
    """Suivi individuel de chaque cellule royale (issue #25). L'action
    `confirmer_eclosion` couvre le seul cas qui a besoin d'un traitement
    spécial (créer la Reine liée) ; les statuts MORTE_AVANT_ECLOSION et
    PERDUE se marquent simplement en modifiant le champ `statut`
    directement, sans action dédiée."""

    list_display = [
        "campagne", "mere", "statut", "ruche_orpheline", "apidea", "reine",
    ]
    list_filter = ["campagne", "statut", "ruche_orpheline", "apidea"]
    search_fields = ["mere__identifiant", "reine__identifiant"]
    autocomplete_fields = ["campagne", "mere", "ruche_orpheline", "apidea", "reine"]
    actions = ["confirmer_eclosion"]

    @admin.action(description="Confirmer éclosion → créer la Reine")
    def confirmer_eclosion(self, request, queryset):
        a_traiter = queryset.filter(statut=StatutCelluleRoyale.EN_DEVELOPPEMENT)
        nb_ignorees = queryset.exclude(statut=StatutCelluleRoyale.EN_DEVELOPPEMENT).count()

        identifiants_crees = []
        for cellule in a_traiter:
            identifiant = suggerer_identifiant_fille(cellule.mere, date.today().year)
            reine = Reine.objects.create(
                identifiant=identifiant,
                mere=cellule.mere,
                statut=StatutReine.VIERGE,
                mode_acquisition=ModeAcquisitionReine.ELEVEE,
            )
            cellule.reine = reine
            cellule.statut = StatutCelluleRoyale.DEVENUE_REINE
            cellule.save(update_fields=["reine", "statut"])
            identifiants_crees.append(identifiant)

        if identifiants_crees:
            self.message_user(
                request,
                f"{len(identifiants_crees)} reine(s) créée(s) : "
                f"{', '.join(identifiants_crees)}. Finalisez ensuite "
                "manuellement chaque fiche (date de naissance exacte, "
                "marquage couleur...).",
                level=messages.SUCCESS,
            )
        if nb_ignorees:
            self.message_user(
                request,
                f"{nb_ignorees} cellule(s) ignorée(s) : statut différent "
                "de « En développement ».",
                level=messages.WARNING,
            )


@admin.register(CritereSelection)
class CritereSelectionAdmin(admin.ModelAdmin):
    list_display = ["nom", "code", "type_mesure", "unite", "ordre"]
    list_filter = ["type_mesure"]
    list_editable = ["ordre"]
    search_fields = ["nom", "code"]


class SelectCritereAvecTitre(forms.Select):
    """Ajoute un attribut HTML `title` (description complète du critère,
    issue #23) sur chaque <option>, consultable au survol pour qui veut
    plus de détail que le repère court du label."""

    def __init__(self, *args, descriptions=None, **kwargs):
        self.descriptions = descriptions or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        description = self.descriptions.get(str(value))
        if description:
            option["attrs"]["title"] = description
        return option


class ChampCritereAvecRepere(forms.ModelChoiceField):
    """ModelChoiceField pour `critere` avec un court repère de
    désambiguïsation entre parenthèses à côté du nom (issue #23) :
    certains noms de CritereSelection se ressemblent de trop près dans
    la liste déroulante ("Miel" / "Récolte", "Propreté" / "Nettoyage
    des rayons"). Local à PoidsCritereInline : ne modifie pas
    CritereSelection.nom, qui reste le libellé officiel affiché ailleurs
    (CritereSelectionAdmin, tableau de résultats, fiches PDF, calendrier)."""

    REPERES_PAR_CODE = {
        "PROPRETE": "état du plateau",
        "NETTOYAGE": "test, temps de nettoyage",
        "RECOLTE": "comparée à la moyenne du rucher",
        "MIEL": "provision stockée",
    }

    def label_from_instance(self, obj):
        repere = self.REPERES_PAR_CODE.get(obj.code)
        if repere:
            return f"{obj.nom} ({repere})"
        return obj.nom


class PoidsCritereForm(forms.ModelForm):
    """Bornes HTML min/max sur le champ poids (issue #24) : la validation
    serveur (MinValueValidator/MaxValueValidator, selection/models.py) reste
    le garde-fou réel, cet ajout n'est qu'un signal immédiat côté navigateur
    avant tout enregistrement."""

    class Meta:
        model = PoidsCritere
        fields = "__all__"
        widgets = {
            "poids": forms.NumberInput(attrs={"min": 0, "max": 10, "step": 1}),
        }


class PoidsCritereInline(admin.TabularInline):
    """Poids/seuils du lot, sur le modèle de EtapeCalendrierInline
    (issue #19).

    Sur la page d'ajout (obj is None), le formset est pré-rempli avec
    une ligne par CritereSelection existant (poids=0), pour éviter
    l'aller-retour "enregistrer une première fois" nécessaire au
    signal post_save (issue #21). Sur la page de modification, ce
    pré-remplissage est désactivé (extra=0) : le signal a déjà créé
    les PoidsCritere réels, get_or_create empêchant tout doublon entre
    les deux mécanismes."""

    model = PoidsCritere
    form = PoidsCritereForm
    extra = 0
    fields = ["critere", "poids", "seuil_eliminatoire"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "critere":
            descriptions = {
                str(pk): description
                for pk, description in CritereSelection.objects.values_list(
                    "pk", "description"
                )
                if description
            }
            kwargs["form_class"] = ChampCritereAvecRepere
            kwargs["widget"] = SelectCritereAvecTitre(descriptions=descriptions)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return CritereSelection.objects.count()
        return 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj is None:
            initial = [
                {"critere": critere.pk, "poids": 0}
                for critere in CritereSelection.objects.all()
            ]

            class FormSetAvecCriteresPreremplis(formset):
                def __init__(self, *args, **kwargs):
                    kwargs.setdefault("initial", initial)
                    super().__init__(*args, **kwargs)

            return FormSetAvecCriteresPreremplis
        return formset


@admin.register(LotCriteres)
class LotCriteresAdmin(admin.ModelAdmin):
    """Sur la page d'ajout, le formset inline (PoidsCritereInline)
    pré-rempli avec les 9 critères fait déjà tout le travail de
    création des PoidsCritere avec les valeurs saisies (issue #21).
    Le signal creer_poids_criteres_lot (selection/signals.py) se
    déclenche pourtant aussi, dès save_model(), avant que save_related()
    n'ait traité le formset : les deux mécanismes entrent en conflit sur
    la contrainte unique_poids_par_lot dès que les poids saisis diffèrent
    de 0 (issue #22). On désactive donc le signal, uniquement pour ce
    passage précis par le formulaire d'ajout, via un attribut temporaire
    sur l'instance ; le signal reste le filet de sécurité pour toute
    autre voie de création (shell, script, API future)."""

    list_display = ["nom"]
    search_fields = ["nom"]
    inlines = [PoidsCritereInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj._creation_via_admin_formulaire = True
        super().save_model(request, obj, form, change)


@admin.register(PoidsCritere)
class PoidsCritereAdmin(admin.ModelAdmin):
    form = PoidsCritereForm
    list_display = ["lot", "critere", "poids", "seuil_eliminatoire"]
    list_filter = ["lot", "critere"]
    list_editable = ["poids", "seuil_eliminatoire"]


@admin.register(Mesure)
class MesureAdmin(admin.ModelAdmin):
    list_display = [
        "colonie", "critere", "campagne", "date_mesure", "valeur_brute",
        "score",
    ]
    list_filter = ["critere", "campagne"]
    search_fields = ["colonie__ruche__numero", "valeur_brute"]
    autocomplete_fields = ["colonie", "critere", "campagne"]
