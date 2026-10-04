"""Vues de l'écran d'accueil visuel et de la fiche colonie (issue #41).

Lit uniquement les modèles de gestion du rucher (Rucher, Ruche, Colonie,
Reine, ConfigurationColonie, EvenementColonie), par l'ORM Django —
aucune vue SQL ni requête PostgreSQL spécifique (portabilité SQLite,
cf. CONTEXTE.md). Ne doit jamais importer la moindre vue, le moindre
modèle ou le moindre gabarit propre à la sélection génétique.
"""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from selection.models import Colonie, Ruche, Rucher


def accueil(request):
    """Une section par rucher, une tuile par ruche active (les boîtes
    retirées du service, `Ruche.actif=False`, ne sont pas montrées :
    elles ne reflètent plus l'état courant du rucher)."""
    colonies_actives = Colonie.objects.filter(active=True).select_related(
        "reine_actuelle",
    )
    ruches = (
        Ruche.objects.filter(actif=True)
        .select_related("type_ruche")
        .prefetch_related(
            Prefetch("colonies", queryset=colonies_actives, to_attr="colonies_actives"),
        )
    )
    ruchers = Rucher.objects.prefetch_related(
        Prefetch("ruches", queryset=ruches, to_attr="ruches_actives"),
    )

    sections = []
    for rucher in ruchers:
        tuiles = []
        for ruche in rucher.ruches_actives:
            tuiles.append({
                "ruche": ruche,
                "colonie": ruche.colonies_actives[0] if ruche.colonies_actives else None,
            })
        sections.append({"rucher": rucher, "tuiles": tuiles})

    return render(request, "gestion/accueil.html", {
        "sections": sections,
        "nb_colonies_actives": Colonie.objects.filter(active=True).count(),
        "nb_ruchers": Rucher.objects.count(),
    })


def fiche_colonie(request, colonie_id):
    """Fiche colonie en lecture seule (issue #41) : ruche, rucher, reine,
    configuration actuelle (la plus récente), historique des événements.
    La saisie reste réservée à l'admin Django pour cette première
    version (lien « Modifier dans l'administration »)."""
    colonie = get_object_or_404(
        Colonie.objects
        .select_related("ruche__type_ruche", "ruche__rucher", "reine_actuelle__mere")
        .prefetch_related("configurations", "evenements"),
        pk=colonie_id,
    )
    return render(request, "gestion/fiche_colonie.html", {
        "colonie": colonie,
        "configuration_actuelle": colonie.configurations.first(),
        "evenements": colonie.evenements.all(),
    })
