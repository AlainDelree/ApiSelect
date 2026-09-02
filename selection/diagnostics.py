"""Mode diagnostic (issue #32) : vérifications de cohérence des données,
purement consultatives — aucune n'empêche la saisie ni la sauvegarde.

Contexte : verrouiller ces cas via des validations strictes rendrait la
saisie rigide et pénible (usage bureau, saisie le soir) ; un diagnostic
consultable à la demande, qui signale sans bloquer, répond au besoin réel
sans ajouter de friction (cf. CONTEXTE.md).

Chaque vérification est une fonction indépendante, sans argument, qui
retourne une liste d'`Avertissement`. Ajouter une nouvelle vérification =
écrire une fonction de ce type et l'ajouter à `VERIFICATIONS` — jamais
modifier une grosse fonction monolithique.
"""

from dataclasses import dataclass
from typing import Optional

from django.db.models import Q
from django.urls import reverse

from .models import (
    CampagneElevage,
    CelluleRoyale,
    Colonie,
    LotCriteres,
    Mesure,
    Reine,
    StatutCelluleRoyale,
)


@dataclass
class Avertissement:
    """Un problème de cohérence détecté. `url_admin`, quand pertinent,
    pointe vers la fiche admin de l'objet concerné pour une correction en
    un clic."""

    message: str
    url_admin: Optional[str] = None


def campagnes_actives_sans_lot_criteres():
    """Une campagne « active » (au moins une Mesure ou une EtapeCalendrier,
    cette dernière créée automatiquement dès que `date_reference` est
    renseignée) sans `lot_criteres` assigné n'a aucun poids/seuil : ses
    colonies sont silencieusement exclues du tableau de résultats, sans
    indication visible de la cause réelle (cas rencontré par Alain,
    origine de cette issue)."""
    avertissements = []
    campagnes = (
        CampagneElevage.objects
        .filter(lot_criteres__isnull=True)
        .filter(Q(mesures__isnull=False) | Q(etapes__isnull=False))
        .distinct()
    )
    for campagne in campagnes:
        avertissements.append(Avertissement(
            message=(
                f"La campagne « {campagne.nom} » a au moins une mesure ou une "
                f"étape de calendrier mais aucun lot de critères assigné : "
                f"aucun poids ni seuil ne sera trouvé pour le calcul d'index, "
                f"ses colonies apparaîtront exclues sans motif clair."
            ),
            url_admin=reverse("admin:selection_campagneelevage_change", args=[campagne.id]),
        ))
    return avertissements


def lots_criteres_tous_poids_nuls():
    """Un lot dont tous les poids valent 0 est probablement un oubli de
    configuration (ex. lot fraîchement créé, auto-peuplé à 0 par le
    signal `creer_poids_criteres_lot`, jamais rempli ensuite) plutôt
    qu'un choix volontaire — à signaler sans bloquer."""
    avertissements = []
    for lot in LotCriteres.objects.prefetch_related("poids_criteres"):
        poids = list(lot.poids_criteres.values_list("poids", flat=True))
        if poids and all(p == 0 for p in poids):
            avertissements.append(Avertissement(
                message=(
                    f"Le lot de critères « {lot.nom} » a tous ses poids à 0 : "
                    f"probablement un oubli de configuration plutôt qu'un "
                    f"choix volontaire."
                ),
                url_admin=reverse("admin:selection_lotcriteres_change", args=[lot.id]),
            ))
    return avertissements


def colonies_actives_ruche_invalide_ou_inactive():
    """Une colonie active devrait toujours reposer sur une ruche valide et
    en service : une ruche marquée inactive (retirée du service) sous une
    colonie encore active est une incohérence."""
    avertissements = []
    colonies = Colonie.objects.filter(active=True).select_related("ruche")
    for colonie in colonies:
        if colonie.ruche_id is None:
            avertissements.append(Avertissement(
                message=(
                    f"La colonie « {colonie} » est active mais n'a aucune "
                    f"ruche associée valide."
                ),
                url_admin=reverse("admin:selection_colonie_change", args=[colonie.id]),
            ))
        elif not colonie.ruche.actif:
            avertissements.append(Avertissement(
                message=(
                    f"La colonie « {colonie} » est active mais sa ruche "
                    f"« {colonie.ruche} » est marquée inactive (retirée du "
                    f"service)."
                ),
                url_admin=reverse("admin:selection_colonie_change", args=[colonie.id]),
            ))
    return avertissements


def reines_genealogie_chronologie_incoherente():
    """Une reine référencée comme `mere` d'une autre ne devrait pas être
    née après elle — incohérence généalogique chronologique, vérifiée
    seulement quand les deux dates de naissance sont renseignées."""
    avertissements = []
    filles = (
        Reine.objects
        .filter(mere__isnull=False, date_naissance__isnull=False)
        .filter(mere__date_naissance__isnull=False)
        .select_related("mere")
    )
    for fille in filles:
        if fille.mere.date_naissance > fille.date_naissance:
            avertissements.append(Avertissement(
                message=(
                    f"La reine « {fille.mere.identifiant} » (née le "
                    f"{fille.mere.date_naissance}) est enregistrée comme mère "
                    f"de « {fille.identifiant} » (née le {fille.date_naissance}) "
                    f"alors qu'elle est née après elle."
                ),
                url_admin=reverse("admin:selection_reine_change", args=[fille.id]),
            ))
    return avertissements


def cellules_royales_statut_reine_incoherents():
    """Le statut DEVENUE_REINE et le champ `reine` d'une CelluleRoyale
    doivent être renseignés ensemble ou pas du tout — l'un sans l'autre
    est une incohérence d'état."""
    avertissements = []
    cellules = CelluleRoyale.objects.select_related("mere", "campagne", "reine")
    for cellule in cellules:
        if cellule.statut == StatutCelluleRoyale.DEVENUE_REINE and cellule.reine_id is None:
            avertissements.append(Avertissement(
                message=(
                    f"La cellule royale « {cellule} » a le statut « Devenue "
                    f"reine » mais aucune reine n'est renseignée."
                ),
                url_admin=reverse("admin:selection_celluleroyale_change", args=[cellule.id]),
            ))
        elif cellule.reine_id is not None and cellule.statut != StatutCelluleRoyale.DEVENUE_REINE:
            avertissements.append(Avertissement(
                message=(
                    f"La cellule royale « {cellule} » a une reine renseignée "
                    f"(« {cellule.reine.identifiant} ») mais son statut n'est "
                    f"pas « Devenue reine » (actuellement "
                    f"« {cellule.get_statut_display()} »)."
                ),
                url_admin=reverse("admin:selection_celluleroyale_change", args=[cellule.id]),
            ))
    return avertissements


def mesures_score_hors_intervalle():
    """Filet de sécurité si un score est jamais saisi hors du formulaire
    admin standard (qui applique déjà les validateurs 1-4) — via un
    script, une migration de données ou une future API."""
    avertissements = []
    mesures = (
        Mesure.objects
        .filter(score__isnull=False)
        .exclude(score__gte=1, score__lte=4)
        .select_related("colonie", "critere")
    )
    for mesure in mesures:
        avertissements.append(Avertissement(
            message=(
                f"La mesure « {mesure} » a un score de {mesure.score}, hors "
                f"de l'intervalle attendu 1-4."
            ),
            url_admin=reverse("admin:selection_mesure_change", args=[mesure.id]),
        ))
    return avertissements


# Titre affiché + fonction de vérification. Ajouter une vérification ici
# suffit à l'intégrer au diagnostic (vue + gabarit itèrent cette liste).
VERIFICATIONS = [
    ("Campagnes actives sans lot de critères", campagnes_actives_sans_lot_criteres),
    ("Lots de critères à poids tous nuls", lots_criteres_tous_poids_nuls),
    ("Colonies actives à ruche invalide ou inactive", colonies_actives_ruche_invalide_ou_inactive),
    ("Généalogie de reines chronologiquement incohérente", reines_genealogie_chronologie_incoherente),
    ("Cellules royales à statut/reine incohérents", cellules_royales_statut_reine_incoherents),
    ("Mesures à score hors intervalle 1-4", mesures_score_hors_intervalle),
]


def executer_diagnostics():
    """Exécute toutes les vérifications enregistrées. Retourne la liste
    complète (titre, avertissements) même pour les vérifications sans
    résultat, pour laisser le gabarit décider de l'affichage."""
    return [(titre, fonction()) for titre, fonction in VERIFICATIONS]
