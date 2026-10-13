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
    path("stocks/", views.stocks, name="stocks"),
    path("stocks/articles/ajouter/", views.ajouter_article, name="ajouter_article"),
    path(
        "stocks/articles/<int:article_id>/modifier/",
        views.modifier_article, name="modifier_article",
    ),
    path(
        "stocks/articles/<int:article_id>/desactiver/",
        views.desactiver_article, name="desactiver_article",
    ),
    path(
        "stocks/articles/<int:article_id>/supprimer/",
        views.supprimer_article, name="supprimer_article",
    ),
    path(
        "stocks/articles/<int:article_id>/mouvement/<str:sens>/",
        views.ajouter_mouvement, name="ajouter_mouvement",
    ),
    path(
        "stocks/articles/<int:article_id>/corriger/",
        views.corriger_stock, name="corriger_stock",
    ),
    path(
        "stocks/articles/<int:article_id>/historique/",
        views.historique_mouvements, name="historique_mouvements",
    ),
    path(
        "stocks/mouvements/<int:mouvement_id>/annuler/",
        views.annuler_mouvement, name="annuler_mouvement",
    ),
    path(
        "stocks/charger-catalogue/",
        views.charger_catalogue_depart, name="charger_catalogue_depart",
    ),
]
