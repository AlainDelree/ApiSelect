import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.shortcuts import get_object_or_404, render

from .calculs import calculer_index_colonie
from .models import (
    CampagneElevage,
    CritereSelection,
    EtapeCalendrier,
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
