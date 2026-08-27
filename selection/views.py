from collections import defaultdict

from django.shortcuts import get_object_or_404, render

from .calculs import calculer_index_colonie
from .models import CampagneElevage, CritereSelection, VueColonieActive, VueMesureComplete


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
