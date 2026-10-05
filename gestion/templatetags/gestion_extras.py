from django import template

from gestion.affichage import bande_ruche as _bande_ruche
from gestion.couleurs import couleur_marquage as _couleur_marquage
from gestion.couleurs import couleur_marquage_proposee as _couleur_marquage_proposee
from gestion.couleurs import nom_couleur_marquage as _nom_couleur_marquage

register = template.Library()


@register.filter(name="couleur_marquage")
def couleur_marquage(code):
    """Couleur hexadécimale de la pastille de marquage d'une reine,
    à partir du code `CouleurMarquage` (gris neutre si vide/inconnu)."""
    return _couleur_marquage(code)


@register.filter(name="nom_couleur_marquage")
def nom_couleur_marquage(code):
    """Nom court d'un code `CouleurMarquage` (chaîne vide si absent)."""
    return _nom_couleur_marquage(code)


@register.filter(name="couleur_a_utiliser")
def couleur_a_utiliser(reine):
    """Nom de la couleur à utiliser pour marquer `reine` (issue #53) :
    celle déjà enregistrée, sinon celle de son année de naissance,
    « couleur à choisir » si ni l'une ni l'autre n'est connue."""
    code = _couleur_marquage_proposee(reine)
    if not code:
        return "couleur à choisir"
    return _nom_couleur_marquage(code)


@register.filter(name="bande_ruche")
def bande_ruche(ruche):
    """Couleur, proportion et libellé accessible de la bande d'une
    ruche (issue #47), pour les tuiles d'accueil et la fiche colonie."""
    return _bande_ruche(ruche)
