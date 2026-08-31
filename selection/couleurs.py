"""Palette fixe de couleurs pour le repérage visuel des étapes du
calendrier d'élevage (issue #15).

Codée en dur volontairement : contrairement à `TypeRuche.alias`, ce
n'est PAS un champ éditable en base ni configurable depuis l'admin —
Alain veut un repérage visuel stable d'une campagne à l'autre.

PICKING (greffage) et GARNIR_APIDEA (insertion des CR dans les
Apidea) sont les deux interventions manuelles les plus importantes du
calendrier : couleurs plus vives/saturées que les autres étapes,
qui restent dans des teintes pastel. Chaque couleur a été choisie
avec sa couleur de texte (noir ou blanc) pour un contraste WCAG AA
correct (>= 4.5:1) — cf. rapport de clôture de l'issue #15 pour le
détail des ratios mesurés. ORPHELINAGE (issue #16) reste en pastel,
sur le même principe : étape préparatoire (attente de la règle des 9
jours), pas une intervention aussi critique que PICKING/GARNIR_APIDEA
(ratio de contraste texte noir mesuré à 11.26:1, cf. rapport de
clôture de l'issue #16).
"""

from .models import TypeEtapeCalendrier

COULEURS_ETAPES = {
    TypeEtapeCalendrier.ELEVAGE_MALES: {"fond": "#90caf9", "texte": "#000000"},
    TypeEtapeCalendrier.ORPHELINAGE: {"fond": "#80cbc4", "texte": "#000000"},
    TypeEtapeCalendrier.PICKING: {"fond": "#fb8c00", "texte": "#000000"},
    TypeEtapeCalendrier.RUCHE_ORPHELINE: {"fond": "#ce93d8", "texte": "#000000"},
    TypeEtapeCalendrier.GARNIR_APIDEA: {"fond": "#c62828", "texte": "#ffffff"},
    TypeEtapeCalendrier.CONTROLE_PONTE_GRILLE: {"fond": "#a5d6a7", "texte": "#000000"},
}

_COULEUR_PAR_DEFAUT = {"fond": "#e3f2fd", "texte": "#000000"}


def couleur_etape(type_etape):
    """Couleur de fond + couleur de texte fixes associées à un type
    d'étape du calendrier (dict {"fond": "#rrggbb", "texte": "#rrggbb"}).
    """
    return COULEURS_ETAPES.get(type_etape, _COULEUR_PAR_DEFAUT)
