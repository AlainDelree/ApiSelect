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
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from selection.calculs import suggerer_identifiant_fille
from selection.models import (
    Colonie,
    EvenementColonie,
    Reine,
    Ruche,
    Rucher,
    TypeEvenementColonie,
)

from .forms import (
    MarquerReineForm,
    NouvelleReineForm,
    RevisiteReineMorteForm,
    VisiteForm,
    initial_observations_depuis_visite,
)
from .models import (
    ActionVisite,
    ObservationVisite,
    RappelRevisite,
    StatutObservation,
    TypeObservationVisite,
    Vendeur,
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


def _observation_reine_morte_confirmee_sans_remplacement(colonie):
    """Dernière observation « reine morte » confirmée de cette colonie,
    s'il n'y a pas de remérage (`EvenementColonie`) enregistré à une
    date égale ou postérieure à la visite où elle a été constatée —
    sert au signal de couronne barrée sur la tuile et à la mention sur
    la fiche colonie (issue #50). Une observation infirmée ou
    supprimée ne ressort plus ici (filtrée par son statut), donc le
    signal disparaît avec elle."""
    observation = (
        ObservationVisite.objects.filter(
            colonie=colonie,
            type_observation=TypeObservationVisite.REINE_MORTE,
            statut=StatutObservation.CONFIRMEE,
        )
        .select_related("visite")
        .order_by("-visite__date", "-id")
        .first()
    )
    if observation is None:
        return None
    remerage_depuis = EvenementColonie.objects.filter(
        colonie=colonie,
        type_evenement=TypeEvenementColonie.REMERAGE,
        date__gte=observation.visite.date,
    ).exists()
    return None if remerage_depuis else observation


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
            observation_reine_morte_confirmee = None
            if colonie is not None:
                visites = colonie.visites_prefetchees
                derniere_visite = visites[0] if visites else None
                if derniere_visite is not None:
                    jours_depuis_visite = (aujourdhui - derniere_visite.date).days
                observations_ouvertes = colonie.observations_ouvertes_liste
                observation_reine_morte_confirmee = (
                    _observation_reine_morte_confirmee_sans_remplacement(colonie)
                )
            tuiles.append({
                "ruche": ruche,
                "colonie": colonie,
                "derniere_visite": derniere_visite,
                "jours_depuis_visite": jours_depuis_visite,
                "observations_ouvertes": observations_ouvertes,
                "observation_reine_morte_confirmee": observation_reine_morte_confirmee,
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
        "nb_reines_non_marquees": Colonie.objects.filter(
            active=True, reine_actuelle__marquage_effectue=False,
        ).count(),
        "rappels_a_revisiter": rappels_a_revisiter,
    })


def fiche_colonie(request, colonie_id):
    """Fiche colonie (issues #41 et #43) : ruche, rucher, reine,
    configuration actuelle, historique des événements, historique des
    visites (la plus récente en premier) et observations ouvertes
    (confirmer/infirmer, date de revérification)."""
    colonie = get_object_or_404(
        Colonie.objects
        .select_related(
            "ruche__type_ruche", "ruche__rucher",
            "reine_actuelle__mere", "reine_actuelle__vendeur",
        )
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
        "observation_reine_morte_confirmee": (
            _observation_reine_morte_confirmee_sans_remplacement(colonie)
        ),
    })


def _synchroniser_observation(visite, colonie, type_observation, nouvelle_certitude, **extra):
    """Crée, met à jour ou supprime l'observation d'un type donné pour
    cette visite, selon la valeur choisie dans le formulaire à boutons
    — sert aussi bien à la création qu'à la modification (issue #48) :
    observation absente avant et après → rien ; ajoutée → créée
    ouverte ; retirée → supprimée (son rappel éventuel suit par la
    cascade du modèle) ; déjà présente → certitude (et champ annexe)
    mis à jour sans toucher au statut, qui reste celui déjà enregistré
    (ouverte, confirmée ou infirmée). Cas ambigu retenu : si la
    certitude d'une observation déjà confirmée ou infirmée change, son
    statut n'est pas réinitialisé à « ouverte » — comportement le plus
    simple, à la charge d'Alain de confirmer/infirmer à nouveau si
    besoin depuis la fiche colonie."""
    observation = visite.observations.filter(type_observation=type_observation).first()
    if not nouvelle_certitude:
        if observation is not None:
            observation.delete()
        return None
    if observation is None:
        return ObservationVisite.objects.create(
            visite=visite, colonie=colonie, type_observation=type_observation,
            certitude=nouvelle_certitude, **extra,
        )
    observation.certitude = nouvelle_certitude
    for champ, valeur in extra.items():
        setattr(observation, champ, valeur)
    observation.save()
    return observation


def _traiter_formulaire_visite(request, colonie, visite):
    """Formulaire à boutons de saisie d'une visite, commun à la
    création et à la modification (issue #48) : même gabarit, même
    classe de formulaire, mêmes champs. Seule la création pose en plus
    la question « couvain ouvert présent ? » si une observation
    « reine morte » reste ouverte depuis une visite précédente — sans
    objet en modification, qui ne porte que sur les champs de la
    visite éditée (issue #43)."""
    creation = visite.pk is None
    observation_reine_morte_ouverte = (
        _observation_reine_morte_ouverte(colonie) if creation else None
    )

    if request.method == "POST":
        form = VisiteForm(request.POST, instance=visite)
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

            visite.actions.all().delete()
            for type_action in form.cleaned_data["actions"]:
                ActionVisite.objects.create(visite=visite, type_action=type_action)

            _synchroniser_observation(
                visite, colonie, TypeObservationVisite.ESSAIMAGE,
                form.cleaned_data["observation_essaimage"],
                reponse_cellules_royales=form.cleaned_data["reponse_cellules_royales"],
            )
            observation_reine_morte = _synchroniser_observation(
                visite, colonie, TypeObservationVisite.REINE_MORTE,
                form.cleaned_data["observation_reine_morte"],
            )
            if observation_reine_morte is not None:
                # Le modèle crée (ou garde) le rappel par défaut à
                # l'enregistrement ci-dessus s'il y a lieu ; on
                # applique ici la date choisie dans le formulaire,
                # s'il y en a une et qu'un rappel existe bien.
                date_choisie = form.cleaned_data["date_reverification_reine_morte"]
                rappel = getattr(observation_reine_morte, "rappel", None)
                if date_choisie and rappel is not None:
                    rappel.date_revisite = date_choisie
                    rappel.save(update_fields=["date_revisite"])
            _synchroniser_observation(
                visite, colonie, TypeObservationVisite.PILLAGE,
                form.cleaned_data["observation_pillage"],
            )
            _synchroniser_observation(
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
        if creation:
            initial = {
                "date_reverification_reine_morte": date_revisite_par_defaut(timezone.localdate()),
            }
        else:
            initial = initial_observations_depuis_visite(visite)
        form = VisiteForm(instance=visite, initial=initial)
        revisite_form = RevisiteReineMorteForm() if observation_reine_morte_ouverte else None

    return render(request, "gestion/visite_form.html", {
        "colonie": colonie,
        "visite": visite,
        "form": form,
        "revisite_form": revisite_form,
        "observation_reine_morte_ouverte": observation_reine_morte_ouverte,
    })


def nouvelle_visite(request, colonie_id):
    """Formulaire de saisie d'une nouvelle visite depuis la fiche
    colonie, à grands boutons à toucher (issue #43)."""
    colonie = get_object_or_404(
        Colonie.objects.select_related("ruche__type_ruche"), pk=colonie_id,
    )
    return _traiter_formulaire_visite(request, colonie, Visite(colonie=colonie))


def modifier_visite(request, colonie_id, visite_id):
    """Même formulaire que la création, pré-rempli, pour modifier une
    visite existante (issue #48)."""
    colonie = get_object_or_404(
        Colonie.objects.select_related("ruche__type_ruche"), pk=colonie_id,
    )
    visite = get_object_or_404(Visite, pk=visite_id, colonie=colonie)
    return _traiter_formulaire_visite(request, colonie, visite)


def supprimer_visite(request, colonie_id, visite_id):
    """Suppression d'une visite derrière une page de confirmation
    explicite (issue #48) : rien n'est supprimé avant la validation de
    ce formulaire. Supprime avec elle ses actions, ses observations et
    les rappels de revérification liés, par cascade du modèle."""
    colonie = get_object_or_404(
        Colonie.objects.select_related("ruche__type_ruche"), pk=colonie_id,
    )
    visite = get_object_or_404(Visite, pk=visite_id, colonie=colonie)
    if request.method == "POST":
        visite.delete()
        return redirect("gestion:fiche_colonie", colonie_id=colonie.id)
    return render(request, "gestion/confirmer_suppression_visite.html", {
        "colonie": colonie,
        "visite": visite,
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


def nouvelle_reine(request, colonie_id):
    """Formulaire de remplacement de reine depuis la fiche colonie
    (issue #51), à grands boutons comme celui de visite. À
    l'enregistrement : la nouvelle reine devient la reine actuelle de
    la colonie, un événement de remérage est créé à la date choisie en
    conservant la trace de l'ancienne reine (`EvenementColonie.
    ancienne_reine`), et cette dernière n'est ni supprimée ni modifiée
    — seulement détachée de la colonie. Ce remérage fait disparaître le
    signal « reine morte » de l'issue #50, qui ne ressort plus dès
    qu'un tel événement existe à une date égale ou postérieure à
    l'observation confirmée (cf. `_observation_reine_morte_confirmee_
    sans_remplacement`)."""
    colonie = get_object_or_404(
        Colonie.objects.select_related("ruche__type_ruche", "reine_actuelle"),
        pk=colonie_id,
    )
    if request.method == "POST":
        form = NouvelleReineForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data["origine"] == "EXISTANTE":
                reine = data["reine_existante"]
            else:
                vendeur = data.get("vendeur")
                if vendeur is None and data.get("nouveau_vendeur_nom"):
                    vendeur = Vendeur.objects.create(
                        nom=data["nouveau_vendeur_nom"],
                        telephone=data.get("nouveau_vendeur_telephone", ""),
                        adresse=data.get("nouveau_vendeur_adresse", ""),
                    )
                reine = Reine.objects.create(
                    identifiant=data["identifiant"],
                    mere=data.get("mere"),
                    mode_acquisition=data.get("mode_acquisition") or "",
                    vendeur=vendeur,
                    statut=data.get("statut") or None,
                    date_fecondation=data.get("date_fecondation"),
                    date_naissance=data.get("date_naissance"),
                    marquage_effectue=data["marquage_effectue"],
                    date_marquage=data.get("date_marquage"),
                    couleur_marquage=(
                        data.get("couleur_marquage") if data["marquage_effectue"] else ""
                    ),
                )

            ancienne_reine = colonie.reine_actuelle
            colonie.reine_actuelle = reine
            colonie.save(update_fields=["reine_actuelle"])

            EvenementColonie.objects.create(
                colonie=colonie,
                date=data["date_remplacement"],
                type_evenement=TypeEvenementColonie.REMERAGE,
                reine=reine,
                ancienne_reine=ancienne_reine,
            )
            return redirect("gestion:fiche_colonie", colonie_id=colonie.id)
    else:
        form = NouvelleReineForm()

    return render(request, "gestion/nouvelle_reine_form.html", {
        "colonie": colonie,
        "form": form,
    })


def suggestion_identifiant_reine(request):
    """Petit point d'entrée JSON utilisé en amélioration progressive
    par le formulaire de remplacement de reine (issue #51) : réutilise
    la logique de suggestion existante (`suggerer_identifiant_fille`,
    déjà en place pour les cellules royales devenues reines) quand une
    mère est choisie. Sans JavaScript, l'identifiant reste à saisir à
    la main — aucune fonctionnalité perdue."""
    try:
        mere = Reine.objects.get(pk=request.GET.get("mere_id"))
        annee = int(request.GET.get("annee"))
    except (Reine.DoesNotExist, TypeError, ValueError):
        return JsonResponse({"identifiant": ""})
    return JsonResponse({"identifiant": suggerer_identifiant_fille(mere, annee)})


def marquer_reine(request, reine_id):
    """Page de confirmation du marquage d'une reine (issue #51),
    atteinte depuis le bouton « Marquer la reine » de la fiche colonie
    ou depuis la liste « Reines à marquer » — `retour` indique où
    revenir après l'enregistrement."""
    reine = get_object_or_404(Reine, pk=reine_id)
    retour = request.GET.get("retour") or request.POST.get("retour") or ""

    if request.method == "POST":
        form = MarquerReineForm(request.POST, reine=reine)
        if form.is_valid():
            reine.marquage_effectue = True
            reine.date_marquage = form.cleaned_data["date_marquage"]
            reine.couleur_marquage = form.cleaned_data["couleur_marquage"]
            reine.save(
                update_fields=["marquage_effectue", "date_marquage", "couleur_marquage"],
            )
            if retour.startswith("colonie:"):
                return redirect("gestion:fiche_colonie", colonie_id=retour[len("colonie:"):])
            return redirect("gestion:reines_a_marquer")
    else:
        form = MarquerReineForm(reine=reine)

    return render(request, "gestion/marquer_reine_form.html", {
        "reine": reine,
        "form": form,
        "retour": retour,
    })


def reines_a_marquer(request):
    """Liste des reines non marquées des colonies actives (issue #51),
    atteinte depuis le compteur de l'accueil."""
    colonies = (
        Colonie.objects.filter(active=True, reine_actuelle__marquage_effectue=False)
        .select_related("reine_actuelle", "ruche__type_ruche", "ruche__rucher")
        .order_by("ruche__rucher__nom", "ruche__numero")
    )
    return render(request, "gestion/reines_a_marquer.html", {"colonies": colonies})
