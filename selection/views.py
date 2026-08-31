import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from xhtml2pdf import pisa

from .calculs import calculer_index_colonie
from .models import (
    CampagneElevage,
    CritereSelection,
    EtapeCalendrier,
    Reine,
    TypeMesure,
    VueColonieActive,
    VueMesureComplete,
)

NOMS_MOIS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre",
    12: "Décembre",
}
NOMS_JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def resultats_selection(request):
    """Tableau des colonies actives d'une campagne, triées par index de
    sélection décroissant, avec le détail des 9 critères en colonnes.

    Campagne par défaut : la plus récente selon l'ordering du modèle
    (année décroissante, puis nom) — cf. rapport de clôture pour
    l'ambiguïté sur ce choix.
    """
    campagnes = CampagneElevage.objects.all()

    if not campagnes.exists():
        return render(request, "selection/resultats.html", {
            "campagnes": campagnes,
            "campagne_selectionnee": None,
            "criteres": [],
            "lignes": [],
        })

    campagne_id = request.GET.get("campagne")
    if campagne_id:
        campagne_selectionnee = get_object_or_404(CampagneElevage, pk=campagne_id)
    else:
        campagne_selectionnee = campagnes.first()

    criteres = list(CritereSelection.objects.all())
    colonies = list(VueColonieActive.objects.all())

    scores_par_colonie = defaultdict(dict)
    for mesure in VueMesureComplete.objects.filter(campagne_id=campagne_selectionnee.id):
        scores_par_colonie[mesure.colonie_id][mesure.critere_id] = mesure.score

    lignes = []
    for colonie in colonies:
        resultat = calculer_index_colonie(colonie.colonie_id, campagne_selectionnee.id)
        scores = scores_par_colonie.get(colonie.colonie_id, {})
        lignes.append({
            "colonie": colonie,
            "resultat": resultat,
            "scores_par_critere": [scores.get(critere.id) for critere in criteres],
            "a_des_mesures": bool(scores),
        })

    # Colonies sans index exploitable (exclues ou sans mesure) reléguées en
    # fin de tableau plutôt que mélangées par un index conventionnel à 0 —
    # cf. rapport de clôture pour l'ambiguïté sur ce choix.
    lignes.sort(key=lambda ligne: (
        ligne["resultat"].index is None,
        -ligne["resultat"].index if ligne["resultat"].index is not None else 0,
    ))

    return render(request, "selection/resultats.html", {
        "campagnes": campagnes,
        "campagne_selectionnee": campagne_selectionnee,
        "criteres": criteres,
        "lignes": lignes,
    })


def calendrier_elevage(request):
    """Calendrier mois par mois de toutes les étapes calculées (toutes
    campagnes confondues, superposées quand plusieurs tombent le même
    jour). Navigation par `?annee=&mois=`, mois courant par défaut.

    Grille HTML simple (une case par jour, étapes empilées en petites
    lignes avec le nom de la campagne) plutôt qu'une bibliothèque JS —
    cf. rapport de clôture pour ce choix de mise en page.
    """
    aujourdhui = date.today()
    try:
        annee = int(request.GET.get("annee", aujourdhui.year))
    except ValueError:
        annee = aujourdhui.year
    try:
        mois = int(request.GET.get("mois", aujourdhui.month))
    except ValueError:
        mois = aujourdhui.month
    if not 1 <= mois <= 12:
        mois = aujourdhui.month

    premier_jour_mois = date(annee, mois, 1)
    dernier_jour_mois = date(annee, mois, calendar.monthrange(annee, mois)[1])

    etapes_par_jour = defaultdict(list)
    for etape in (
        EtapeCalendrier.objects
        .filter(date_prevue__gte=premier_jour_mois, date_prevue__lte=dernier_jour_mois)
        .select_related("campagne")
        .order_by("type_etape")
    ):
        etapes_par_jour[etape.date_prevue].append(etape)

    semaines = [
        [
            {
                "date": jour,
                "hors_mois": jour.month != mois,
                "aujourdhui": jour == aujourdhui,
                "etapes": etapes_par_jour.get(jour, []),
            }
            for jour in semaine
        ]
        for semaine in calendar.Calendar(firstweekday=0).monthdatescalendar(annee, mois)
    ]

    mois_precedent = premier_jour_mois - timedelta(days=1)
    mois_suivant = dernier_jour_mois + timedelta(days=1)

    return render(request, "selection/calendrier.html", {
        "annee": annee,
        "mois": mois,
        "nom_mois": NOMS_MOIS[mois],
        "noms_jours_semaine": NOMS_JOURS_SEMAINE,
        "semaines": semaines,
        "aujourdhui": aujourdhui,
        "annee_precedente": mois_precedent.year,
        "mois_precedent": mois_precedent.month,
        "annee_suivante": mois_suivant.year,
        "mois_suivant": mois_suivant.month,
    })


def liste_taches(request):
    """Liste chronologique des prochaines étapes non réalisées, toutes
    campagnes confondues, avec le nom de la campagne et le type d'étape.

    Marquer une étape comme réalisée se fait depuis sa fiche dans
    l'administration (cohérent avec le reste de l'app, où l'admin reste
    l'unique point de saisie) — cf. rapport de clôture pour ce choix.
    """
    etapes = (
        EtapeCalendrier.objects
        .filter(realisee=False)
        .select_related("campagne")
        .order_by("date_prevue")
    )
    return render(request, "selection/taches.html", {
        "etapes": etapes,
        "aujourdhui": date.today(),
    })


def _campagne_selectionnee(request):
    """Campagne demandée via `?campagne=`, ou la plus récente par défaut
    (même règle que `resultats_selection`) ; None si aucune campagne
    n'existe encore."""
    campagne_id = request.GET.get("campagne") or request.POST.get("campagne")
    if campagne_id:
        return get_object_or_404(CampagneElevage, pk=campagne_id)
    return CampagneElevage.objects.first()


def _lignees_par_reine(colonies):
    """Lignée mâle probable par reine, pour les colonies données — la vue
    `vue_colonies_actives` expose l'identifiant de la reine mais pas ce
    champ, non repris dans l'aplatissement SQL."""
    reine_ids = [colonie.reine_id for colonie in colonies if colonie.reine_id]
    return {
        reine_id: lignee
        for reine_id, lignee in Reine.objects.filter(id__in=reine_ids).values_list(
            "id", "lignee_male_probable"
        )
        if lignee
    }


def _rendre_pdf(request, template_name, contexte, nom_fichier):
    """Rend un gabarit HTML en PDF via xhtml2pdf (portable Linux/Windows
    sans dépendance système, cf. CONTEXTE.md — préféré à WeasyPrint pour
    cette raison). `request` est transmis pour que les context processors
    (dont le bandeau de base de test, issue #12) s'appliquent aussi aux
    fiches imprimées."""
    html = render_to_string(template_name, contexte, request=request)
    reponse = HttpResponse(content_type="application/pdf")
    reponse["Content-Disposition"] = f'inline; filename="{nom_fichier}"'
    resultat_pisa = pisa.CreatePDF(html, dest=reponse)
    if resultat_pisa.err:
        return HttpResponse("Erreur lors de la génération du PDF.", status=500)
    return reponse


def fiche_rapide_pdf(request):
    """Fiche de terrain imprimable pour la passe rapide : une ligne par
    colonie active (toutes, sans sélection préalable), colonnes des 4
    critères PASSE_RAPIDE avec assez d'espace pour entourer une note de 1
    à 4 à la main plutôt que d'écrire (cf. CONTEXTE.md — visite au rucher,
    gants + propolis), colonne « note libre » finale.
    """
    campagne = _campagne_selectionnee(request)
    criteres = list(CritereSelection.objects.filter(type_mesure=TypeMesure.PASSE_RAPIDE))
    colonies = list(VueColonieActive.objects.all())
    lignees = _lignees_par_reine(colonies)

    ruchers = {colonie.rucher_nom for colonie in colonies if colonie.rucher_nom}
    nom_rucher = ruchers.pop() if len(ruchers) == 1 else "Tous ruchers"

    contexte = {
        "campagne": campagne,
        "date_jour": date.today(),
        "nom_rucher": nom_rucher,
        "criteres": criteres,
        "lignes": [
            {"colonie": colonie, "lignee": lignees.get(colonie.reine_id, "")}
            for colonie in colonies
        ],
    }
    return _rendre_pdf(request, "selection/fiche_rapide_pdf.html", contexte, "fiche_rapide.pdf")


def fiche_approfondie_formulaire(request):
    """Formulaire de sélection des colonies à inclure dans la fiche
    approfondie : à la différence de la fiche rapide, elle ne concerne que
    des candidates déjà pressenties, jamais toutes les colonies actives
    par défaut (cf. issue #8)."""
    campagnes = CampagneElevage.objects.all()
    campagne_selectionnee = _campagne_selectionnee(request) if campagnes.exists() else None
    colonies = list(VueColonieActive.objects.all())
    return render(request, "selection/fiche_approfondie_formulaire.html", {
        "campagnes": campagnes,
        "campagne_selectionnee": campagne_selectionnee,
        "colonies": colonies,
    })


def fiche_approfondie_pdf(request):
    """Fiche de terrain imprimable pour la passe approfondie, limitée aux
    colonies choisies dans `fiche_approfondie_formulaire`. Colonnes des 5
    critères PASSE_APPROFONDIE avec un espace pour la valeur brute
    mesurée — pas directement un score 1-4, ce barème nécessitant une
    mesure physique convertie ensuite (cf. CONTEXTE.md)."""
    campagne = _campagne_selectionnee(request)
    colonie_ids = request.POST.getlist("colonies") or request.GET.getlist("colonies")
    criteres = list(CritereSelection.objects.filter(type_mesure=TypeMesure.PASSE_APPROFONDIE))
    colonies = list(VueColonieActive.objects.filter(colonie_id__in=colonie_ids))
    lignees = _lignees_par_reine(colonies)

    contexte = {
        "campagne": campagne,
        "date_jour": date.today(),
        "criteres": criteres,
        "lignes": [
            {"colonie": colonie, "lignee": lignees.get(colonie.reine_id, "")}
            for colonie in colonies
        ],
    }
    return _rendre_pdf(
        request, "selection/fiche_approfondie_pdf.html", contexte, "fiche_approfondie.pdf"
    )
