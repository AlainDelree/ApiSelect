"""Calcul de l'index pondéré de sélection (Index = Σ(score×poids) / Σ(poids)).

Logique métier conditionnelle volontairement tenue hors SQL : les jointures
et l'aplatissement des données vivent dans les vues PostgreSQL (cf.
selection/migrations/0002_vues_sql.py, modèle VueMesureComplete), le calcul
final et les seuils éliminatoires vivent ici, testables sans base de données
réelle (voir MesureIndex : simple porte-données, indépendant de l'ORM).
"""

from dataclasses import dataclass
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
