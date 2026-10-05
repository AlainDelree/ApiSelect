from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("colonies/<int:colonie_id>/", views.fiche_colonie, name="fiche_colonie"),
    path(
        "colonies/<int:colonie_id>/nouvelle-visite/",
        views.nouvelle_visite, name="nouvelle_visite",
    ),
    path(
        "colonies/<int:colonie_id>/nouvelle-reine/",
        views.nouvelle_reine, name="nouvelle_reine",
    ),
    path(
        "reines/",
        views.liste_reines, name="liste_reines",
    ),
    path(
        "reines/ajouter/",
        views.ajouter_reine, name="ajouter_reine",
    ),
    path(
        "reines/<int:reine_id>/modifier/",
        views.modifier_reine, name="modifier_reine",
    ),
    path(
        "reines-a-marquer/",
        views.reines_a_marquer, name="reines_a_marquer",
    ),
    path(
        "reines/<int:reine_id>/marquer/",
        views.marquer_reine, name="marquer_reine",
    ),
    path(
        "suggestion-identifiant/",
        views.suggestion_identifiant_reine, name="suggestion_identifiant_reine",
    ),
    path(
        "colonies/<int:colonie_id>/visites/<int:visite_id>/modifier/",
        views.modifier_visite, name="modifier_visite",
    ),
    path(
        "colonies/<int:colonie_id>/visites/<int:visite_id>/supprimer/",
        views.supprimer_visite, name="supprimer_visite",
    ),
    path(
        "observations/<int:observation_id>/confirmer/",
        views.confirmer_observation, name="confirmer_observation",
    ),
    path(
        "observations/<int:observation_id>/infirmer/",
        views.infirmer_observation, name="infirmer_observation",
    ),
]
