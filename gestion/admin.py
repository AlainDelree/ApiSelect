"""Administration des visites et observations (issue #43). Ne doit
jamais importer le moindre modèle ou la moindre vue d'admin propre à
la sélection génétique."""

from django.contrib import admin

from .models import ActionVisite, ObservationVisite, RappelRevisite, Visite


class ActionVisiteInline(admin.TabularInline):
    model = ActionVisite
    extra = 0


class ObservationVisiteInline(admin.TabularInline):
    model = ObservationVisite
    extra = 0
    fields = ["type_observation", "certitude", "statut", "reponse_cellules_royales"]


@admin.register(Visite)
class VisiteAdmin(admin.ModelAdmin):
    list_display = [
        "colonie", "date", "observation_reine", "nb_cadres_couvain",
        "nb_cadres_abeilles", "reserves", "comportement",
    ]
    list_filter = ["date", "observation_reine", "reserves", "comportement"]
    search_fields = ["colonie__ruche__numero", "notes"]
    autocomplete_fields = ["colonie"]
    inlines = [ActionVisiteInline, ObservationVisiteInline]


@admin.register(ObservationVisite)
class ObservationVisiteAdmin(admin.ModelAdmin):
    list_display = [
        "colonie", "visite", "type_observation", "certitude", "statut",
        "reponse_cellules_royales",
    ]
    list_filter = ["type_observation", "certitude", "statut"]
    search_fields = ["colonie__ruche__numero"]
    autocomplete_fields = ["colonie", "visite"]
    list_editable = ["statut"]


@admin.register(RappelRevisite)
class RappelRevisiteAdmin(admin.ModelAdmin):
    list_display = ["observation", "date_revisite", "traite"]
    list_filter = ["traite"]
    list_editable = ["traite"]
    autocomplete_fields = ["observation"]
    ordering = ["date_revisite"]
