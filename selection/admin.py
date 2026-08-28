from django.contrib import admin

from .models import (
    CampagneElevage,
    Colonie,
    ConfigurationColonie,
    CritereSelection,
    EtapeCalendrier,
    EvenementColonie,
    Mesure,
    PoidsCritere,
    Reine,
    Ruche,
    Rucher,
    StationFecondation,
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
        "identifiant", "mere", "couleur_marquage", "date_naissance",
        "station_fecondation", "date_deces",
    ]
    list_filter = ["couleur_marquage", "station_fecondation"]
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
    list_display = [
        "__str__", "ruche", "reine_actuelle", "mode_creation",
        "date_creation", "active",
    ]
    list_filter = ["mode_creation", "active", "ruche__type_ruche"]
    search_fields = ["ruche__numero", "reine_actuelle__identifiant"]
    autocomplete_fields = ["ruche", "reine_actuelle"]
    inlines = [ConfigurationColonieInline, EvenementColonieInline]


class EtapeCalendrierInline(admin.TabularInline):
    """Étapes calculées automatiquement (cf. selection/signals.py) : la
    date prévue et le type d'étape sont en lecture seule ici, seuls
    `realisee`/`date_reelle`/`notes` se saisissent à la main."""

    model = EtapeCalendrier
    extra = 0
    fields = ["type_etape", "date_prevue", "realisee", "date_reelle", "notes"]
    readonly_fields = ["type_etape", "date_prevue"]
    can_delete = False
    ordering = ["date_prevue"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CampagneElevage)
class CampagneElevageAdmin(admin.ModelAdmin):
    list_display = ["nom", "annee", "date_reference", "date_debut", "date_fin"]
    list_filter = ["annee"]
    search_fields = ["nom"]
    inlines = [EtapeCalendrierInline]


@admin.register(EtapeCalendrier)
class EtapeCalendrierAdmin(admin.ModelAdmin):
    list_display = ["campagne", "type_etape", "date_prevue", "realisee", "date_reelle"]
    list_filter = ["type_etape", "realisee", "campagne"]
    list_editable = ["realisee", "date_reelle"]
    search_fields = ["campagne__nom"]
    autocomplete_fields = ["campagne"]


@admin.register(CritereSelection)
class CritereSelectionAdmin(admin.ModelAdmin):
    list_display = ["nom", "code", "type_mesure", "unite", "ordre"]
    list_filter = ["type_mesure"]
    list_editable = ["ordre"]
    search_fields = ["nom", "code"]


@admin.register(PoidsCritere)
class PoidsCritereAdmin(admin.ModelAdmin):
    list_display = ["campagne", "critere", "poids", "seuil_eliminatoire"]
    list_filter = ["campagne", "critere"]
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
