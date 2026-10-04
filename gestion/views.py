"""Vues de l'écran d'accueil visuel, de la fiche colonie et de la
saisie de visite (issues #41 et #43).

Lit uniquement les modèles de gestion du rucher (Rucher, Ruche, Colonie,
Reine, ConfigurationColonie, EvenementColonie, Visite et modèles liés),
par l'ORM Django — aucune vue SQL ni requête PostgreSQL spécifique
(portabilité SQLite, cf. CONTEXTE.md). Ne doit jamais importer la
moindre vue, le moindre modèle ou le moindre gabarit propre à la
sélection génétique.
"""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from selection.models import Colonie, Ruche, Rucher

from .forms import RevisiteReineMorteForm, VisiteForm
from .models import (
    ActionVisite,
    CertitudeObservation,
    ObservationVisite,
    RappelRevisite,
    StatutObservation,
    TypeObservationVisite,
    Visite,
    date_revisite_par_defaut,
)


def _observation_reine_morte_ouverte(colonie):
    return (
        ObservationVisite.objects.filter(
            colonie=colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            statut=StatutObservation.OUVERTE,
        )
        .select_related("rappel")
        .first()
    )


def _cloturer_rappel(observation):
    rappel = getattr(observation, "rappel", None)
    if rappel is not None:
        rappel.traite = True
        rappel.save(update_fields=["traite"])


def accueil(request):
    """Une section par rucher, une tuile par ruche active (les boîtes
    retirées du service, `Ruche.actif=False`, ne sont pas montrées :
    elles ne reflètent plus l'état courant du rucher). Chaque tuile
    affiche la dernière visite et les observations ouvertes (issue
    #43)."""
    aujourdhui = timezone.localdate()

    observations_ouvertes_qs = ObservationVisite.objects.filter(
        statut=StatutObservation.OUVERTE,
    ).select_related("rappel")
    colonies_actives = (
        Colonie.objects.filter(active=True)
        .select_related("reine_actuelle")
        .prefetch_related(
            Prefetch("visites", queryset=Visite.objects.all(), to_attr="visites_prefetchees"),
            Prefetch(
                "observations_visite",
                queryset=observations_ouvertes_qs,
                to_attr="observations_ouvertes_liste",
            ),
        )
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
            colonie = ruche.colonies_actives[0] if ruche.colonies_actives else None
            derniere_visite = None
            jours_depuis_visite = None
            observations_ouvertes = []
            if colonie is not None:
                visites = colonie.visites_prefetchees
                derniere_visite = visites[0] if visites else None
                if derniere_visite is not None:
                    jours_depuis_visite = (aujourdhui - derniere_visite.date).days
                observations_ouvertes = colonie.observations_ouvertes_liste
            tuiles.append({
                "ruche": ruche,
                "colonie": colonie,
                "derniere_visite": derniere_visite,
                "jours_depuis_visite": jours_depuis_visite,
                "observations_ouvertes": observations_ouvertes,
            })
        sections.append({"rucher": rucher, "tuiles": tuiles})

    rappels_qs = (
        RappelRevisite.objects.filter(traite=False)
        .select_related("observation__colonie__ruche__type_ruche")
        .order_by("date_revisite")
    )
    rappels_a_revisiter = [
        {"rappel": rappel, "en_retard": rappel.date_revisite <= aujourdhui}
        for rappel in rappels_qs
    ]

    return render(request, "gestion/accueil.html", {
        "sections": sections,
        "nb_colonies_actives": Colonie.objects.filter(active=True).count(),
        "nb_ruchers": Rucher.objects.count(),
        "rappels_a_revisiter": rappels_a_revisiter,
    })


def fiche_colonie(request, colonie_id):
    """Fiche colonie (issues #41 et #43) : ruche, rucher, reine,
    configuration actuelle, historique des événements, historique des
    visites (la plus récente en premier) et observations ouvertes
    (confirmer/infirmer, date de revérification)."""
    colonie = get_object_or_404(
        Colonie.objects
        .select_related("ruche__type_ruche", "ruche__rucher", "reine_actuelle__mere")
        .prefetch_related(
            "configurations",
            "evenements",
            Prefetch(
                "visites",
                queryset=Visite.objects.prefetch_related("actions", "observations"),
            ),
        ),
        pk=colonie_id,
    )
    observations_ouvertes = (
        ObservationVisite.objects.filter(colonie=colonie, statut=StatutObservation.OUVERTE)
        .select_related("rappel")
    )
    return render(request, "gestion/fiche_colonie.html", {
        "colonie": colonie,
        "configuration_actuelle": colonie.configurations.first(),
        "evenements": colonie.evenements.all(),
        "visites": colonie.visites.all(),
        "observations_ouvertes": observations_ouvertes,
    })


def _enregistrer_observation(visite, colonie, type_observation, valeur_certitude, **extra):
    if not valeur_certitude:
        return None
    return ObservationVisite.objects.create(
        visite=visite, colonie=colonie, type_observation=type_observation,
        certitude=valeur_certitude, **extra,
    )


def nouvelle_visite(request, colonie_id):
    """Formulaire de saisie d'une visite depuis la fiche colonie, à
    grands boutons à toucher. Si une observation « reine morte » est
    ouverte pour cette colonie, pose en plus la question « couvain
    ouvert présent ? » pour la confirmer ou l'infirmer (issue #43)."""
    colonie = get_object_or_404(
        Colonie.objects.select_related("ruche__type_ruche"), pk=colonie_id,
    )
    observation_reine_morte_ouverte = _observation_reine_morte_ouverte(colonie)

    if request.method == "POST":
        form = VisiteForm(request.POST)
        revisite_form = (
            RevisiteReineMorteForm(request.POST) if observation_reine_morte_ouverte else None
        )
        formulaire_valide = form.is_valid() and (
            revisite_form is None or revisite_form.is_valid()
        )
        if formulaire_valide:
            visite = form.save(commit=False)
            visite.colonie = colonie
            visite.save()

            for type_action in form.cleaned_data["actions"]:
                ActionVisite.objects.create(visite=visite, type_action=type_action)

            _enregistrer_observation(
                visite, colonie, TypeObservationVisite.ESSAIMAGE,
                form.cleaned_data["observation_essaimage"],
                reponse_cellules_royales=form.cleaned_data["reponse_cellules_royales"],
            )
            observation_reine_morte = _enregistrer_observation(
                visite, colonie, TypeObservationVisite.REINE_MORTE,
                form.cleaned_data["observation_reine_morte"],
            )
            if (
                observation_reine_morte is not None
                and observation_reine_morte.certitude == CertitudeObservation.DOUTE
            ):
                # Le modèle a déjà créé le rappel par défaut (visite + 9
                # jours) à l'enregistrement ci-dessus ; on applique ici
                # la date choisie dans le formulaire, s'il y en a une.
                date_choisie = form.cleaned_data["date_reverification_reine_morte"]
                if date_choisie:
                    rappel = observation_reine_morte.rappel
                    rappel.date_revisite = date_choisie
                    rappel.save(update_fields=["date_revisite"])
            _enregistrer_observation(
                visite, colonie, TypeObservationVisite.PILLAGE,
                form.cleaned_data["observation_pillage"],
            )
            _enregistrer_observation(
                visite, colonie, TypeObservationVisite.FRELONS,
                form.cleaned_data["observation_frelons"],
            )

            if observation_reine_morte_ouverte is not None and revisite_form is not None:
                if revisite_form.cleaned_data["couvain_ouvert_present"]:
                    observation_reine_morte_ouverte.infirmer()
                else:
                    observation_reine_morte_ouverte.confirmer()
                _cloturer_rappel(observation_reine_morte_ouverte)

            return redirect("gestion:fiche_colonie", colonie_id=colonie.id)
    else:
        form = VisiteForm(initial={
            "date_reverification_reine_morte": date_revisite_par_defaut(timezone.localdate()),
        })
        revisite_form = RevisiteReineMorteForm() if observation_reine_morte_ouverte else None

    return render(request, "gestion/nouvelle_visite.html", {
        "colonie": colonie,
        "form": form,
        "revisite_form": revisite_form,
        "observation_reine_morte_ouverte": observation_reine_morte_ouverte,
    })


def confirmer_observation(request, observation_id):
    """Confirmation manuelle d'une observation ouverte depuis la fiche
    colonie (issue #43)."""
    observation = get_object_or_404(ObservationVisite, pk=observation_id)
    if request.method == "POST":
        observation.confirmer()
        _cloturer_rappel(observation)
    return redirect("gestion:fiche_colonie", colonie_id=observation.colonie_id)


def infirmer_observation(request, observation_id):
    """Infirmation manuelle d'une observation ouverte depuis la fiche
    colonie (issue #43)."""
    observation = get_object_or_404(ObservationVisite, pk=observation_id)
    if request.method == "POST":
        observation.infirmer()
        _cloturer_rappel(observation)
    return redirect("gestion:fiche_colonie", colonie_id=observation.colonie_id)
