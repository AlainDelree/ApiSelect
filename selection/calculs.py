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
# Calendrier d'élevage : dates en cascade (issue #7, révisé issue #14)
#
# La première version (issue #7) reprenait la logique du cours générique
# (Maranzan/CRISAB) et du fichier Cours_Apiculture/calendrier élevage de
# reine.ods (gitignoré, cf. CONTEXTE.md — jamais committé), sans vérifier
# qu'elle correspondait à la pratique réelle d'Alain. L'issue #14 corrige
# les décalages pour refléter sa méthode : pas de starter séparé (il
# greffe directement dans une ruche orpheline qui élève les cellules
# royales jusqu'à operculation et au-delà, fusion starter+finisseur), pas
# de couveuse (les cellules restent sur la colonie orpheline jusqu'à
# distribution), distribution directe dans les Apidea après la période de
# fragilité (nymphose ~J10-J13) et avant la naissance (~J16), pas de
# libération ni de contrôle des naissances séparés. Les décalages
# PICKING (+4j, greffage d'une larve de 12-36h à J4) et ELEVAGE_MALES
# (-16j, saturation) sont inchangés de l'issue #7. Les décalages
# GARNIR_APIDEA (+14j) et CONTROLE_PONTE_GRILLE (+25j) sont ceux fournis
# par Alain pour sa méthode réelle (issue #14), pas des cellules de
# l'ODS. Le décalage ORPHELINAGE (-5j) est ajouté par l'issue #16 : « loi
# des 9 jours » du cours Maranzan/CRISAB — 3 jours de stade œuf + 6 jours
# de couvain ouvert, période après laquelle la colonie rendue orpheline
# n'a plus de couvain ouvrable pour élever elle-même une reine et est
# donc réellement prête à prendre en charge le greffage (PICKING).
# Calcul : PICKING (+4j) − 9j = -5j depuis la ponte de référence.
#
# L'étape RUCHE_ORPHELINE (même date que PICKING, +4j) est retirée par
# l'issue #25 : son rôle (indiquer quelle ruche est orpheline) est
# redondant maintenant que PICKING porte lui-même ruche_origine/
# ruche_destination (cf. selection/models.py, EtapeCalendrier), et le
# suivi individuel de chaque cellule royale vit dans le modèle
# CelluleRoyale plutôt que dans une étape agrégée du calendrier.
# ---------------------------------------------------------------------------

DECALAGES_JOURS_ETAPES = {
    "ELEVAGE_MALES": -16,
    "ORPHELINAGE": -5,
    "PICKING": 4,
    "GARNIR_APIDEA": 14,
    "CONTROLE_PONTE_GRILLE": 25,
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


# ---------------------------------------------------------------------------
# Convention de nommage des reines filles (issue #25)
#
# Le nom porte la lettre de la lignée FONDATRICE (pas du parent immédiat)
# + année de naissance + numéro de séquence dans cette lignée/année,
# toutes campagnes confondues (la génétique de la mère ne change pas
# entre deux vagues de picking de la même saison — seul le père varie,
# non tracé dans le nom). Rejeté : chaînage complet du parent immédiat
# (ex. A24-1-1-1...), illisible sur plusieurs générations. La généalogie
# fine complète reste consultable via Reine.mere et la vue
# vue_genealogie_reines — le nom est un repère rapide, pas la source de
# vérité généalogique.
# ---------------------------------------------------------------------------

def lettre_lignee_fondatrice(reine):
    """Remonte récursivement `reine.mere` jusqu'à une reine sans mère
    connue (la fondatrice de la lignée), retourne la première lettre de
    son identifiant (majuscule)."""
    fondatrice = reine
    while fondatrice.mere is not None:
        fondatrice = fondatrice.mere
    return fondatrice.identifiant[0].upper()


def suggerer_identifiant_fille(mere, annee_naissance):
    """Suggère un identifiant pour une fille de `mere`, née en
    `annee_naissance` : lettre de la lignée fondatrice + année sur 2
    chiffres + prochain numéro de séquence disponible pour cette
    combinaison lettre+année, tous comptés sur l'ensemble des Reines
    existantes (peu importe la campagne). Ex. A26-1, A26-2, puis A27-1
    l'année suivante — toujours la lettre de la fondatrice, jamais celle
    du parent immédiat.
    """
    from .models import Reine  # import différé : évite un cycle au chargement de l'app

    prefixe = f"{lettre_lignee_fondatrice(mere)}{annee_naissance % 100:02d}-"
    prochain_numero = 1
    for identifiant in Reine.objects.filter(
        identifiant__startswith=prefixe,
    ).values_list("identifiant", flat=True):
        suffixe = identifiant[len(prefixe):]
        if suffixe.isdigit():
            prochain_numero = max(prochain_numero, int(suffixe) + 1)
    return f"{prefixe}{prochain_numero}"
