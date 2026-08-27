from django.urls import path

from . import views

app_name = "selection"

urlpatterns = [
    path("resultats/", views.resultats_selection, name="resultats"),
    path("calendrier/", views.calendrier_elevage, name="calendrier"),
    path("taches/", views.liste_taches, name="taches"),
]
