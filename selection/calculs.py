"""Calcul de l'index pondéré de sélection (Index = Σ(score×poids) / Σ(poids)).

Logique métier conditionnelle volontairement tenue hors SQL : les jointures
et l'aplatissement des données vivent dans les vues PostgreSQL (cf.
selection/migrations/0002_vues_sql.py, modèle VueMesureComplete), le calcul
final et les seuils éliminatoires vivent ici, testables sans base de données
réelle (voir MesureIndex : simple porte-données, indépendant de l'ORM).
"""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Iterable, Optional


@dataclass
class MesureIndex:
    """Une mesure, réduite aux champs nécessaires au calcul de l'index."""

    critere_nom: str
    score: Optional[Decimal]
    poids: Optional[int]
    seuil_eliminatoire: Optional[Decimal]


@dataclass
class ResultatIndex:
    """Résultat du calcul pour une colonie sur une campagne donnée."""

    exclue: bool
    motif_exclusion: Optional[str]
    index: Optional[Decimal]
    nb_criteres_pris_en_compte: int


def calculer_index(mesures: Iterable[MesureIndex]) -> ResultatIndex:
    """Calcule l'index pondéré à partir d'un ensemble de mesures.

    Une mesure sans score n'est pas exploitable et est ignorée. Dès qu'une
    mesure a un score sous le seuil éliminatoire de son critère, la colonie
    est marquée exclue (index=None) : les seuils priment sur le calcul
    normal. Les critères à poids 0 sont inclus dans la somme (ils ne
    changent rien au résultat, poids=0 ne pesant ni sur le numérateur ni
    sur le dénominateur) plutôt qu'explicitement exclus : plus simple à
    maintenir qu'un filtre dédié, pour un résultat identique. Les mesures
    sans poids connu pour la campagne (pas de PoidsCritere défini) sont
    ignorées faute de pondération exploitable.
    """
    numerateur = Decimal("0")
    denominateur = Decimal("0")
    nb_criteres = 0

    for mesure in mesures:
        if mesure.score is None:
            continue

        if (
            mesure.seuil_eliminatoire is not None
            and Decimal(mesure.score) < Decimal(mesure.seuil_eliminatoire)
        ):
            return ResultatIndex(
                exclue=True,
                motif_exclusion=(
                    f"Critère « {mesure.critere_nom} » sous le seuil "
                    f"éliminatoire ({mesure.score} < {mesure.seuil_eliminatoire})"
                ),
                index=None,
                nb_criteres_pris_en_compte=0,
            )

        if mesure.poids is None:
            continue

        numerateur += Decimal(mesure.score) * Decimal(mesure.poids)
        denominateur += Decimal(mesure.poids)
        nb_criteres += 1

    if denominateur == 0:
        return ResultatIndex(
            exclue=False,
            motif_exclusion=None,
            index=None,
            nb_criteres_pris_en_compte=nb_criteres,
        )

    return ResultatIndex(
        exclue=False,
        motif_exclusion=None,
        index=numerateur / denominateur,
        nb_criteres_pris_en_compte=nb_criteres,
    )


def calculer_index_colonie(colonie_id: int, campagne_id: int) -> ResultatIndex:
    """Version connectée à la base : lit `VueMesureComplete` pour la
    colonie et la campagne données, puis délègue à `calculer_index`."""
    from .models import VueMesureComplete  # import différé : évite un cycle au chargement de l'app

    lignes = VueMesureComplete.objects.filter(
        colonie_id=colonie_id, campagne_id=campagne_id,
    )
    mesures = (
        MesureIndex(
            critere_nom=ligne.critere_nom,
            score=ligne.score,
            poids=ligne.poids,
            seuil_eliminatoire=ligne.seuil_eliminatoire,
        )
        for ligne in lignes
    )
    return calculer_index(mesures)


# ---------------------------------------------------------------------------
# Calendrier d'élevage : dates en cascade (issue #7)
#
# Logique reprise du fichier source Cours_Apiculture/calendrier élevage de
# reine.ods (gitignoré, cf. CONTEXTE.md — jamais committé). Sur la feuille
# "Calendrier" de ce fichier, toutes les dates de la grille se déduisent par
# une cascade de +1 jour à partir d'une cellule ancre (B14), elle-même égale
# à la date de ponte si elle est saisie, sinon à la date de picking moins 4
# jours (formule =IF(ponte>0; ponte; picking-4)). La feuille "récapitulatif"
# nomme chaque étape utile du cours en référençant une cellule précise de
# cette grille. Les décalages ci-dessous sont les écarts en jours, relevés
# cellule par cellule dans l'ODS, entre chaque étape nommée et cette date de
# ponte (jour 0) :
#   B14 (ponte, jour 0) -> F14 (picking/enlarvement, jour+4)
#   -> A22 (finisseur, jour+5) -> E22 (couveuse, jour+9)
#   -> D30 (peuplement ruchettes, jour+14) -> A38 (libération, jour+17)
#   -> C38 (contrôle naissances, jour+19) -> C46 (début ponte, jour+25)
#   -> D46 (contrôle ponte, jour+26)
# L'étape "élevage des mâles" n'a PAS de cellule calculée dans l'ODS (qui ne
# porte qu'un champ texte libre "Mâle :" pour la lignée) : son décalage de
# -16 jours reprend le principe de saturation de mâles décrit dans le cours
# et résumé dans CONTEXTE.md, pas une formule du tableur — cf. rapport de
# clôture de l'issue #7 pour cette ambiguïté.
# ---------------------------------------------------------------------------

DECALAGES_JOURS_ETAPES = {
    "ELEVAGE_MALES": -16,
    "PICKING": 4,
    "STARTER": 4,
    "FINISSEUR": 5,
    "COUVEUSE": 9,
    "RUCHETTES": 14,
    "LIBERATION": 17,
    "CONTROLE_NAISSANCE": 19,
    "DEBUT_PONTE": 25,
    "CONTROLE_PONTE": 26,
}


def calculer_dates_etapes(date_ponte):
    """À partir de la date de ponte (jour 0 de la cascade de l'ODS),
    calcule la date de chaque étape du calendrier d'élevage.

    Retourne {code_étape: date}, code_étape correspondant aux valeurs de
    `TypeEtapeCalendrier` (selection/models.py).
    """
    return {
        code: date_ponte + timedelta(days=decalage)
        for code, decalage in DECALAGES_JOURS_ETAPES.items()
    }
