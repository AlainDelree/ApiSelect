"""Couleurs d'affichage de la pastille de marquage des reines (issue #41).

Codées en dur volontairement, comme `selection/couleurs.py` pour les
étapes du calendrier : le code couleur du marquage des reines est une
convention apicole fixe (année en 1 ou 6 = blanc, etc., cf.
`selection.models.CouleurMarquage`), pas une donnée à éditer depuis
l'admin.
"""

COULEURS_MARQUAGE = {
    "BLANC": "#ffffff",
    "JAUNE": "#fdd835",
    "ROUGE": "#e53935",
    "VERT": "#43a047",
    "BLEU": "#1e88e5",
}

_COULEUR_PAR_DEFAUT = "#9e9e9e"


def couleur_marquage(code):
    """Couleur hexadécimale de la pastille de marquage pour un code
    `CouleurMarquage` (gris neutre si absent/inconnu)."""
    return COULEURS_MARQUAGE.get(code, _COULEUR_PAR_DEFAUT)
