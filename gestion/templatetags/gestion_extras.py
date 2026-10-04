from django import template

from gestion.affichage import bande_ruche as _bande_ruche
from gestion.couleurs import couleur_marquage as _couleur_marquage

register = template.Library()


@register.filter(name="couleur_marquage")
def couleur_marquage(code):
    """Couleur hexadécimale de la pastille de marquage d'une reine,
    à partir du code `CouleurMarquage` (gris neutre si vide/inconnu)."""
    return _couleur_marquage(code)


@register.filter(name="bande_ruche")
def bande_ruche(ruche):
    """Couleur, proportion et libellé accessible de la bande d'une
    ruche (issue #47), pour les tuiles d'accueil et la fiche colonie."""
    return _bande_ruche(ruche)
