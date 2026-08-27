# Peuple CritereSelection avec les 9 critères du barème de sélection
# génétique du cours (Maranzan/CRISAB, cf. issue #5) : la table existe
# depuis 0001_initial mais avait été volontairement laissée vide en
# attendant d'aller chercher le contenu exact dans le cours.
#
# Répartition en deux passes (cf. CONTEXTE.md, section "Sélection
# génétique") : passe rapide (toutes colonies, chaque visite) pour les
# 4 premiers critères, passe approfondie (colonies pressenties,
# matériel requis) pour les 5 suivants.
#
# Ne couvre PAS le calcul valeur brute -> score 1-4 : ce barème de
# conversion (seuils par critère, ex. "24000 cellules = 4" pour le
# couvain) reste pour l'instant uniquement dans le cours source
# (non versionné) et dans la tête de l'utilisateur qui remplit
# Mesure.score à la main. Point ouvert signalé dans le rapport de
# l'issue #5, pas traité ici.

from django.db import migrations

# Source de vérité unique pour le peuplement initial, sur le modèle de
# TYPES_RUCHE_PAR_DEFAUT (migration 0004) : modifiable ensuite librement
# depuis l'admin Django sans nouvelle migration.
CRITERES_PAR_DEFAUT = [
    {
        "code": "SANTE", "nom": "Santé", "type_mesure": "PASSE_RAPIDE",
        "unite": "", "ordre": 1,
        "description": (
            "Examen visuel du couvain lors de la visite de printemps, à la "
            "recherche de traces de maladie. Note décroissante de 4 (aucune "
            "trace) à 1 (présence de maladie constatée)."
        ),
    },
    {
        "code": "PROPRETE", "nom": "Propreté", "type_mesure": "PASSE_RAPIDE",
        "unite": "", "ordre": 2,
        "description": (
            "Observation de l'état du plateau de la ruche (débris de cire, "
            "larves mortes). Note de 4 (plateau propre) à 1 (nombreux "
            "déchets avec plusieurs larves)."
        ),
    },
    {
        "code": "AGRESSIVITE", "nom": "Agressivité", "type_mesure": "PASSE_RAPIDE",
        "unite": "", "ordre": 3,
        "description": (
            "« Test du bâton » : passer un bâton deux fois (aller-retour) "
            "devant l'entrée de la ruche, le matin avant la sortie des "
            "abeilles. Note de 4 (peu de sorties, pas de vol) à 1 (sortie "
            "en masse avec attaque)."
        ),
    },
    {
        "code": "TENUE_CADRE", "nom": "Tenue au cadre", "type_mesure": "PASSE_RAPIDE",
        "unite": "", "ordre": 4,
        "description": (
            "Après un léger enfumage, soulever un cadre de couvain ouvert "
            "et tapoter 5 à 6 fois la barrette supérieure. Note de 4 (les "
            "abeilles ne se déplacent pas) à 1 (elles forment des grappes "
            "et tombent)."
        ),
    },
    {
        "code": "NETTOYAGE", "nom": "Nettoyage des rayons",
        "type_mesure": "PASSE_APPROFONDIE", "unite": "h", "ordre": 5,
        "description": (
            "Désoperculer un carré d'environ 3x3 cm de couvain mâle, tuer "
            "les larves, puis chronométrer le temps nécessaire aux "
            "ouvrières pour les évacuer entièrement. Note de 4 (nettoyage "
            "en 3h) à 1 (12h)."
        ),
    },
    {
        "code": "RECOLTE", "nom": "Récolte",
        "type_mesure": "PASSE_APPROFONDIE", "unite": "kg", "ordre": 6,
        "description": (
            "Comparaison de la récolte de miel de la colonie à la moyenne "
            "du rucher. Note de 4 (25% de plus que la moyenne) à 1 "
            "(récolte égale à la moyenne)."
        ),
    },
    {
        "code": "COUVAIN", "nom": "Couvain",
        "type_mesure": "PASSE_APPROFONDIE", "unite": "cellules", "ordre": 7,
        "description": (
            "Mesure du couvain par la formule grand diamètre x petit "
            "diamètre x nombre de cadres de couvain, ramenée à un nombre "
            "de cellules estimé. Note de 4 (environ 24000 cellules) à 1 "
            "(environ 6000 cellules)."
        ),
    },
    {
        "code": "MIEL", "nom": "Miel",
        "type_mesure": "PASSE_APPROFONDIE", "unite": "kg", "ordre": 8,
        "description": (
            "Estimation de la provision de miel de la colonie. Note de 4 "
            "(environ 7 kg) à 1 (environ 1 kg)."
        ),
    },
    {
        "code": "POLLEN", "nom": "Pollen",
        "type_mesure": "PASSE_APPROFONDIE", "unite": "dm²", "ordre": 9,
        "description": (
            "Estimation de la provision de pollen, convertie en surface de "
            "rayon operculé (1 dm² correspond à environ 150 g). Note "
            "attribuée selon le même principe dégressif que les autres "
            "critères de la passe approfondie."
        ),
    },
]


def peupler_criteres_selection(apps, schema_editor):
    CritereSelection = apps.get_model("selection", "CritereSelection")
    for donnees in CRITERES_PAR_DEFAUT:
        CritereSelection.objects.create(**donnees)


def depeupler_criteres_selection(apps, schema_editor):
    CritereSelection = apps.get_model("selection", "CritereSelection")
    codes = [donnees["code"] for donnees in CRITERES_PAR_DEFAUT]
    CritereSelection.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('selection', '0004_typeruche_table_alias'),
    ]

    operations = [
        migrations.RunPython(peupler_criteres_selection, depeupler_criteres_selection),
    ]
