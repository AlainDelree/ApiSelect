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
from django.http import Http404, JsonResponse
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

from .catalogue_stocks import charger_catalogue_depart as _charger_catalogue_depart
from .forms import (
    ArticleForm,
    CorrectionStockForm,
    MarquerReineForm,
    MouvementForm,
    NouvelleReineForm,
    ReineForm,
    RevisiteReineMorteForm,
    VisiteForm,
    initial_observations_depuis_visite,
)
from .models import (
    ActionVisite,
    Article,
    FamilleMateriel,
    MotifMouvement,
    MouvementStock,
    ObservationVisite,
    RappelRevisite,
    RubriqueArticle,
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

    articles_stock_bas = [
        article for article in Article.objects.filter(actif=True, seuil_alerte__isnull=False)
        if article.stock_bas
    ]
    articles_stock_negatif = [
        article for article in Article.objects.filter(actif=True)
        if article.stock_negatif
    ]

    return render(request, "gestion/accueil.html", {
        "sections": sections,
        "nb_colonies_actives": Colonie.objects.filter(active=True).count(),
        "nb_ruchers": Rucher.objects.count(),
        "nb_reines_non_marquees": Colonie.objects.filter(
            active=True, reine_actuelle__marquage_effectue=False,
        ).count(),
        "rappels_a_revisiter": rappels_a_revisiter,
        "articles_stock_bas": articles_stock_bas,
        "articles_stock_negatif": articles_stock_negatif,
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
                reine = form.save()

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


def _traiter_formulaire_reine(request, reine, retour):
    """Création ou modification d'une reine par le formulaire unique
    (issue #54) : même gabarit, même classe de formulaire (`ReineForm`)
    pour la création (page « Reines »), la modification (fiche colonie
    et page « Reines ») et, par héritage, le remplacement
    (`NouvelleReineForm`, traité séparément dans `nouvelle_reine` à
    cause des champs propres au remplacement). `retour` indique où
    revenir après l'enregistrement, comme pour `marquer_reine`."""
    if request.method == "POST":
        form = ReineForm(request.POST, instance=reine)
        if form.is_valid():
            form.save()
            if retour.startswith("colonie:"):
                return redirect("gestion:fiche_colonie", colonie_id=retour[len("colonie:"):])
            return redirect("gestion:liste_reines")
    else:
        form = ReineForm(instance=reine)

    return render(request, "gestion/reine_form.html", {
        "reine": reine,
        "form": form,
        "retour": retour,
    })


def modifier_reine(request, reine_id):
    """Bouton « Modifier la reine » de la fiche colonie et de la page
    « Reines » (issue #54) : même formulaire que la création,
    pré-rempli."""
    reine = get_object_or_404(Reine, pk=reine_id)
    retour = request.GET.get("retour") or request.POST.get("retour") or ""
    return _traiter_formulaire_reine(request, reine, retour)


def ajouter_reine(request):
    """Bouton « Ajouter une reine » de la page « Reines » (issue #54) :
    même formulaire vide, pour enregistrer une reine qui n'est pas
    encore installée dans une colonie (ex. une reine achetée qui vient
    d'arriver)."""
    return _traiter_formulaire_reine(request, Reine(), "")


def liste_reines(request):
    """Page « Reines » (issue #54) : toutes les reines enregistrées, y
    compris celles qui ne sont pas affectées à une colonie active —
    contrairement à la fiche colonie et à « Reines à marquer », qui ne
    montrent que les colonies actives."""
    colonies_par_reine = Colonie.objects.select_related(
        "ruche__type_ruche", "ruche__rucher",
    ).order_by("-active", "-id")
    reines = (
        Reine.objects.select_related("vendeur")
        .prefetch_related(
            Prefetch("colonie_dirigee", queryset=colonies_par_reine),
        )
        .order_by("identifiant")
    )
    lignes = [
        {"reine": reine, "colonie": next(iter(reine.colonie_dirigee.all()), None)}
        for reine in reines
    ]
    return render(request, "gestion/liste_reines.html", {"lignes": lignes})


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


def stocks(request):
    """Page « Stocks » (issue #55) : articles groupés par rubrique,
    stock actuel (toujours recalculé depuis les mouvements),
    filtrables par famille de matériel, par rubrique, « stock bas
    seulement », « stock négatif seulement », et masquant par défaut
    les articles inactifs."""
    afficher_inactifs = request.GET.get("inactifs") == "1"
    stock_bas_seulement = request.GET.get("stock_bas") == "1"
    stock_negatif_seulement = request.GET.get("stock_negatif") == "1"
    famille_id = request.GET.get("famille") or ""
    rubrique = request.GET.get("rubrique") or ""

    articles = Article.objects.prefetch_related("familles_compatibles")
    if not afficher_inactifs:
        articles = articles.filter(actif=True)
    if famille_id:
        articles = articles.filter(familles_compatibles__id=famille_id)
    if rubrique:
        articles = articles.filter(rubrique=rubrique)
    articles = articles.order_by("rubrique", "nom").distinct()

    groupes_par_rubrique = {}
    for article in articles:
        if stock_bas_seulement and not article.stock_bas:
            continue
        if stock_negatif_seulement and not article.stock_negatif:
            continue
        groupes_par_rubrique.setdefault(article.rubrique, []).append(article)

    groupes = [
        {"rubrique": code, "libelle": libelle, "articles": groupes_par_rubrique[code]}
        for code, libelle in RubriqueArticle.choices
        if code in groupes_par_rubrique
    ]

    return render(request, "gestion/stocks.html", {
        "groupes": groupes,
        "familles": FamilleMateriel.objects.all(),
        "rubriques": RubriqueArticle.choices,
        "afficher_inactifs": afficher_inactifs,
        "stock_bas_seulement": stock_bas_seulement,
        "stock_negatif_seulement": stock_negatif_seulement,
        "famille_id": famille_id,
        "rubrique": rubrique,
    })


def _traiter_formulaire_article(request, article):
    """Formulaire unique d'un article (issue #55), pour la création
    (bouton « Ajouter un article ») et la modification — mêmes champs
    partout."""
    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect("gestion:stocks")
    else:
        form = ArticleForm(instance=article)
    return render(request, "gestion/article_form.html", {"article": article, "form": form})


def ajouter_article(request):
    return _traiter_formulaire_article(request, Article())


def modifier_article(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    return _traiter_formulaire_article(request, article)


def desactiver_article(request, article_id):
    """Bouton « Désactiver » du formulaire d'article (issue #55) :
    l'article reste en base, caché par défaut de la page « Stocks »,
    jamais supprimé."""
    article = get_object_or_404(Article, pk=article_id)
    if request.method == "POST":
        article.actif = False
        article.save(update_fields=["actif"])
        return redirect("gestion:stocks")
    return redirect("gestion:modifier_article", article_id=article.id)


def supprimer_article(request, article_id):
    """Suppression d'un article derrière une page de confirmation
    explicite (issue #55), possible seulement s'il n'a aucun
    mouvement — la clé étrangère protégée (`on_delete=PROTECT`) sert
    de garde-fou supplémentaire au niveau de la base."""
    article = get_object_or_404(Article, pk=article_id)
    a_des_mouvements = article.mouvements.exists()
    if request.method == "POST":
        if not a_des_mouvements:
            article.delete()
        return redirect("gestion:stocks")
    return render(request, "gestion/confirmer_suppression_article.html", {
        "article": article, "a_des_mouvements": a_des_mouvements,
    })


def ajouter_mouvement(request, article_id, sens):
    """Panneau ouvert depuis le bouton « − » ou « + » de la page
    « Stocks » (issue #55) : quantité (1 par défaut), motif proposé
    selon le bouton (modifiable), date, note facultative. Pour une
    sortie, un avertissement est affiché par JavaScript pendant la
    saisie si le mouvement rendrait le stock négatif — sans bloquer
    l'enregistrement (issue #59)."""
    if sens not in ("entree", "sortie"):
        raise Http404
    article = get_object_or_404(Article, pk=article_id)
    motif_defaut = MotifMouvement.ACHAT if sens == "entree" else MotifMouvement.UTILISATION

    if request.method == "POST":
        form = MouvementForm(request.POST)
        if form.is_valid():
            quantite = form.cleaned_data["quantite"]
            if sens == "sortie":
                quantite = -quantite
            mouvement = form.save(commit=False)
            mouvement.article = article
            mouvement.quantite = quantite
            mouvement.save()
            return redirect("gestion:stocks")
        # Formulaire invalide : réafficher sans calcul d'avertissement
        # (l'avertissement est géré côté client)
        form = MouvementForm(request.POST)
    else:
        form = MouvementForm(initial={
            "date": timezone.localdate(), "quantite": 1, "motif": motif_defaut,
        })
    
    # Ajouter le data attribute pour le stock actuel (utilisé par le JS)
    if form.fields["quantite"].widget.attrs:
        form.fields["quantite"].widget.attrs.update({"data-stock-actuel": article.stock})
    else:
        form.fields["quantite"].widget.attrs = {"data-stock-actuel": article.stock}

    return render(request, "gestion/mouvement_form.html", {
        "article": article, "form": form, "sens": sens,
    })


def corriger_stock(request, article_id):
    """Bouton « Corriger le stock » (issue #55) : la quantité
    réellement comptée est saisie, la différence avec le stock actuel
    est enregistrée comme mouvement de correction d'inventaire — sans
    différence, aucun mouvement n'est créé."""
    article = get_object_or_404(Article, pk=article_id)

    if request.method == "POST":
        form = CorrectionStockForm(request.POST)
        if form.is_valid():
            difference = form.cleaned_data["quantite_comptee"] - article.stock
            if difference != 0:
                MouvementStock.objects.create(
                    article=article, date=form.cleaned_data["date"],
                    quantite=difference, motif=MotifMouvement.CORRECTION,
                    note=form.cleaned_data["note"],
                )
            return redirect("gestion:stocks")
    else:
        form = CorrectionStockForm(initial={
            "date": timezone.localdate(), "quantite_comptee": article.stock,
        })

    return render(request, "gestion/correction_stock_form.html", {
        "article": article, "form": form,
    })


def historique_mouvements(request, article_id):
    """Historique des mouvements d'un article (issue #55), avec
    possibilité d'annuler un mouvement après confirmation explicite."""
    article = get_object_or_404(Article, pk=article_id)
    return render(request, "gestion/historique_mouvements.html", {
        "article": article, "mouvements": article.mouvements.all(),
    })


def annuler_mouvement(request, mouvement_id):
    """Annulation d'un mouvement derrière une page de confirmation
    explicite (issue #55) : rien n'est supprimé avant la validation de
    ce formulaire."""
    mouvement = get_object_or_404(MouvementStock, pk=mouvement_id)
    if request.method == "POST":
        article_id = mouvement.article_id
        mouvement.delete()
        return redirect("gestion:historique_mouvements", article_id=article_id)
    return render(request, "gestion/confirmer_annulation_mouvement.html", {
        "mouvement": mouvement,
    })


def charger_catalogue_depart(request):
    """Bouton « Charger le catalogue de départ » (issue #55), derrière
    une page de confirmation explicite : crée les articles manquants
    du catalogue figé, ne modifie ni ne supprime jamais un article
    existant, et ne crée aucun mouvement."""
    if request.method == "POST":
        resultat = _charger_catalogue_depart()
        return render(request, "gestion/catalogue_depart_resultat.html", {
            "resultat": resultat,
        })
    return render(request, "gestion/confirmer_catalogue_depart.html")
