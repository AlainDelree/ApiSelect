"""Couleurs d'affichage de la pastille de marquage des reines (issue #41),
et correspondance année de naissance -> couleur de marquage (issue #53).

Codées en dur volontairement, comme `selection/couleurs.py` pour les
étapes du calendrier : le code couleur du marquage des reines est une
convention apicole fixe (année en 1 ou 6 = blanc, etc., cf.
`selection.models.CouleurMarquage`), pas une donnée à éditer depuis
l'admin.
"""

from selection.models import CouleurMarquage

COULEURS_MARQUAGE = {
    "BLANC": "#ffffff",
    "JAUNE": "#fdd835",
    "ROUGE": "#e53935",
    "VERT": "#43a047",
    "BLEU": "#1e88e5",
}

_COULEUR_PAR_DEFAUT = "#9e9e9e"

NOMS_COULEURS_MARQUAGE = {
    CouleurMarquage.BLANC: "blanc",
    CouleurMarquage.JAUNE: "jaune",
    CouleurMarquage.ROUGE: "rouge",
    CouleurMarquage.VERT: "vert",
    CouleurMarquage.BLEU: "bleu",
}

# Convention apicole : dernier chiffre de l'année de naissance de la
# reine -> couleur de marquage. Doit rester cohérente avec les libellés
# de `CouleurMarquage` (ex. "Blanc (années en 1 ou 6)"), qui font foi.
_COULEUR_PAR_DERNIER_CHIFFRE_ANNEE = {
    1: CouleurMarquage.BLANC, 6: CouleurMarquage.BLANC,
    2: CouleurMarquage.JAUNE, 7: CouleurMarquage.JAUNE,
    3: CouleurMarquage.ROUGE, 8: CouleurMarquage.ROUGE,
    4: CouleurMarquage.VERT, 9: CouleurMarquage.VERT,
    5: CouleurMarquage.BLEU, 0: CouleurMarquage.BLEU,
}


def couleur_marquage(code):
    """Couleur hexadécimale de la pastille de marquage pour un code
    `CouleurMarquage` (gris neutre si absent/inconnu)."""
    return COULEURS_MARQUAGE.get(code, _COULEUR_PAR_DEFAUT)


def couleur_marquage_pour_annee(annee):
    """Code `CouleurMarquage` associé à une année de naissance de reine,
    selon la convention apicole du dernier chiffre de l'année (`None` si
    `annee` est vide)."""
    if not annee:
        return None
    return _COULEUR_PAR_DERNIER_CHIFFRE_ANNEE.get(annee % 10)


def couleur_marquage_proposee(reine):
    """Couleur à utiliser pour marquer `reine` : celle déjà enregistrée
    en priorité, sinon celle calculée depuis son année de naissance
    (`None` si ni l'une ni l'autre n'est disponible)."""
    if reine.couleur_marquage:
        return reine.couleur_marquage
    if reine.date_naissance:
        return couleur_marquage_pour_annee(reine.date_naissance.year)
    return None


def nom_couleur_marquage(code):
    """Nom court (sans la mention de l'année) d'un code `CouleurMarquage`,
    chaîne vide si absent/inconnu."""
    return NOMS_COULEURS_MARQUAGE.get(code, "")
