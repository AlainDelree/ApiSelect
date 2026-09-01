from django import forms
from django.contrib import admin

from .models import (
    CampagneElevage,
    Colonie,
    ConfigurationColonie,
    CritereSelection,
    EtapeCalendrier,
    EvenementColonie,
    LotCriteres,
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
    date prévue et le type d'étape sont en lecture seule ici. `ruche` et
    `nombre_cr` (issue #16) se saisissent à la main, surtout sur les
    étapes Ruche orpheline (CR obtenues) et Garnir les Apidea (CR
    introduites) — cf. CampagneElevage.taux_reussite."""

    model = EtapeCalendrier
    extra = 0
    fields = [
        "type_etape", "date_prevue", "realisee", "date_reelle", "ruche",
        "nombre_cr", "notes",
    ]
    readonly_fields = ["type_etape", "date_prevue"]
    autocomplete_fields = ["ruche"]
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
        """CR introduites dans les Apidea ÷ CR obtenues sur la ruche
        orpheline (issue #16) — cf. CampagneElevage.taux_reussite."""
        taux = obj.taux_reussite
        if taux is None:
            return "non calculable"
        return f"{taux:.0%}"


@admin.register(EtapeCalendrier)
class EtapeCalendrierAdmin(admin.ModelAdmin):
    list_display = [
        "campagne", "type_etape", "date_prevue", "realisee", "date_reelle",
        "ruche", "nombre_cr",
    ]
    list_filter = ["type_etape", "realisee", "campagne"]
    list_editable = ["realisee", "date_reelle", "nombre_cr"]
    search_fields = ["campagne__nom"]
    autocomplete_fields = ["campagne", "ruche"]


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
