from django import template

from gestion.couleurs import couleur_marquage as _couleur_marquage

register = template.Library()


@register.filter(name="couleur_marquage")
def couleur_marquage(code):
    """Couleur hexadécimale de la pastille de marquage d'une reine,
    à partir du code `CouleurMarquage` (gris neutre si vide/inconnu)."""
    return _couleur_marquage(code)
