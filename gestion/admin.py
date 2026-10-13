"""Administration des visites et observations (issue #43). Ne doit
jamais importer le moindre modèle ou la moindre vue d'admin propre à
la sélection génétique.

Depuis l'issue #48, la saisie courante d'une visite passe uniquement
par le formulaire à boutons de la fiche colonie (création et
modification) : l'admin ne permet plus d'en créer, ni d'en créer les
observations ou rappels, pour éviter un second formulaire de saisie
qui n'offrirait pas les mêmes champs. Modification et suppression y
restent possibles, à titre exceptionnel."""

from django.contrib import admin

from .models import (
    ActionVisite,
    Article,
    FamilleMateriel,
    MouvementStock,
    ObservationVisite,
    RappelRevisite,
    Vendeur,
    Visite,
)


@admin.register(Vendeur)
class VendeurAdmin(admin.ModelAdmin):
    """Un vendeur se crée normalement depuis le formulaire de
    remplacement de reine (fiche colonie, issue #51) ; cet écran reste
    disponible pour les corrections exceptionnelles."""

    list_display = ["nom", "telephone", "adresse"]
    search_fields = ["nom"]


class ActionVisiteInline(admin.TabularInline):
    model = ActionVisite
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


class ObservationVisiteInline(admin.TabularInline):
    model = ObservationVisite
    extra = 0
    fields = ["type_observation", "certitude", "statut", "reponse_cellules_royales"]

    def has_add_permission(self, request, obj=None):
        return False


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

    def has_add_permission(self, request):
        return False


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

    def has_add_permission(self, request):
        return False


@admin.register(RappelRevisite)
class RappelRevisiteAdmin(admin.ModelAdmin):
    list_display = ["observation", "date_revisite", "traite"]
    list_filter = ["traite"]
    list_editable = ["traite"]
    autocomplete_fields = ["observation"]
    ordering = ["date_revisite"]

    def has_add_permission(self, request):
        return False


@admin.register(FamilleMateriel)
class FamilleMaterielAdmin(admin.ModelAdmin):
    """Petit référentiel modifiable (issue #55) : contrairement aux
    articles et aux mouvements, l'ajout y reste permis."""

    list_display = ["nom"]
    search_fields = ["nom"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """La saisie d'un article se fait par le formulaire de la page
    « Stocks » (issue #55) ; cet écran reste disponible pour la
    consultation et les corrections exceptionnelles, sans ajout."""

    list_display = ["nom", "rubrique", "nature", "unite", "seuil_alerte", "actif"]
    list_filter = ["rubrique", "nature", "actif"]
    search_fields = ["nom"]
    filter_horizontal = ["familles_compatibles"]

    def has_add_permission(self, request):
        return False


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    """La saisie d'un mouvement se fait par le panneau « − » / « + »
    de la page « Stocks » (issue #55) ; cet écran reste disponible pour
    la consultation et les corrections exceptionnelles, sans ajout."""

    list_display = ["article", "date", "quantite", "motif"]
    list_filter = ["motif", "date"]
    search_fields = ["article__nom", "note"]
    autocomplete_fields = ["article"]

    def has_add_permission(self, request):
        return False
