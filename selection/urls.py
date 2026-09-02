from django.urls import path

from . import views

app_name = "selection"

urlpatterns = [
    path("resultats/", views.resultats_selection, name="resultats"),
    path("calendrier/", views.calendrier_elevage, name="calendrier"),
    path("taches/", views.liste_taches, name="taches"),
    path("diagnostic/", views.diagnostic, name="diagnostic"),
    path(
        "taches/<int:etape_id>/marquer-realisee/",
        views.marquer_etape_realisee,
        name="marquer_etape_realisee",
    ),
    path("fiches/rapide/", views.fiche_rapide_pdf, name="fiche_rapide"),
    path(
        "fiches/approfondie/",
        views.fiche_approfondie_formulaire,
        name="fiche_approfondie_formulaire",
    ),
    path(
        "fiches/approfondie/pdf/",
        views.fiche_approfondie_pdf,
        name="fiche_approfondie_pdf",
    ),
]
