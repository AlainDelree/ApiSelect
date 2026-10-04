"""Bande de couleur représentant une ruche (issue #47) : utilisée à la
fois sur les tuiles de l'accueil et en tête de la fiche colonie, pour
qu'une même ruche reste reconnaissable partout.

Couleur : celle de `Ruche.couleur`, gris moyen par défaut si vide.
Largeur : proportionnelle au nombre de cadres du type de ruche
(`TypeRuche.nombre_cadres`), centrée entre deux bandes blanches
réparties à parts égales ; pleine largeur si le nombre de cadres est
inconnu ou atteint 10 (une ruchette 6 cadres est donc plus étroite
qu'une Dadant 10, pas l'inverse).

Ne dépend que de `Ruche`/`TypeRuche` (lus, pas modifiés) — même
exception à la dépendance à sens unique vers `selection` que
`gestion.views` (cf. CONTEXTE.md), aucun SQL spécifique à PostgreSQL.
"""

import colorsys

CADRES_PLEINE_LARGEUR = 10
COULEUR_GRISE_PAR_DEFAUT = "#9e9e9e"

# Bornes supérieures de teinte (en degrés, 0-360) associées à un nom de
# couleur française approximatif, pour le libellé accessible de la
# bande. Approximation volontairement grossière (pas de palette figée
# côté `Ruche.couleur`, contrairement au marquage des reines).
_NOMS_PAR_TEINTE = [
    (15, "rouge"),
    (45, "orange"),
    (70, "jaune"),
    (170, "verte"),
    (200, "turquoise"),
    (250, "bleue"),
    (290, "violette"),
    (330, "rose"),
    (360, "rouge"),
]


def _nom_couleur(couleur_hex):
    couleur_hex = couleur_hex.lstrip("#")
    rouge = int(couleur_hex[0:2], 16) / 255
    vert = int(couleur_hex[2:4], 16) / 255
    bleu = int(couleur_hex[4:6], 16) / 255
    teinte, luminosite, saturation = colorsys.rgb_to_hls(rouge, vert, bleu)

    if saturation < 0.15:
        if luminosite > 0.9:
            return "blanche"
        if luminosite < 0.15:
            return "noire"
        return "grise"

    degres = teinte * 360
    for seuil, nom in _NOMS_PAR_TEINTE:
        if degres < seuil:
            return nom
    return _NOMS_PAR_TEINTE[-1][1]


def bande_ruche(ruche):
    """Couleur, proportion (largeur/marge en %) et libellé accessible
    de la bande d'une ruche. `ruche.type_ruche` doit être préchargé par
    l'appelant (`select_related`) pour éviter une requête par tuile."""
    couleur = ruche.couleur or COULEUR_GRISE_PAR_DEFAUT
    nombre_cadres = ruche.type_ruche.nombre_cadres

    if not nombre_cadres or nombre_cadres >= CADRES_PLEINE_LARGEUR:
        largeur_pourcent = 100
        marge_pourcent = 0
    else:
        largeur_pourcent = nombre_cadres * 10
        marge_pourcent = (100 - largeur_pourcent) // 2

    fragments = [ruche.type_ruche.libelle_affichage]
    if nombre_cadres:
        pluriel = "s" if nombre_cadres != 1 else ""
        fragments.append(f"{nombre_cadres} cadre{pluriel}")
    libelle = f"{' '.join(fragments)}, couleur {_nom_couleur(couleur)}"

    return {
        "couleur": couleur,
        "largeur_pourcent": largeur_pourcent,
        "marge_pourcent": marge_pourcent,
        "libelle": libelle,
    }
