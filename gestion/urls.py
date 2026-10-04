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
