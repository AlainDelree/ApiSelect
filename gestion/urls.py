from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("colonies/<int:colonie_id>/", views.fiche_colonie, name="fiche_colonie"),
]
