from django.urls import path

from . import views

app_name = "selection"

urlpatterns = [
    path("resultats/", views.resultats_selection, name="resultats"),
]
