"""Catalogue de départ des articles de stock (issue #55) : liste
figée transmise par Alain, chargée uniquement à la demande — bouton
« Charger le catalogue de départ » de la page « Stocks ». Jamais
exécuté automatiquement ni par une migration (cf. CONTEXTE.md,
protection des données).

`charger_catalogue_depart` est strictement additive : un article déjà
présent (reconnu par son nom et sa rubrique) n'est jamais modifié ni
supprimé, et aucun mouvement n'est créé — tous les stocks des articles
créés restent à 0. Exécuter la fonction une seconde fois ne change
rien de plus.
"""

from .models import Article, FamilleMateriel, NatureArticle, RubriqueArticle

UNITE_PIECE = "pièce"

RUCHE_10 = "Ruche 10 cadres"
RUCHETTE_6 = "Ruchette 6 cadres"
MINIPLUS = "Miniplus"
APIDEA = "Apidea"

RUCHE = RubriqueArticle.RUCHE
ELEVAGE = RubriqueArticle.ELEVAGE
VISITE = RubriqueArticle.VISITE
ATELIER = RubriqueArticle.ATELIER
RECOLTE = RubriqueArticle.RECOLTE

DURABLE = NatureArticle.DURABLE
CONSOMMABLE = NatureArticle.CONSOMMABLE


def _article(nom, rubrique, nature=DURABLE, unite=UNITE_PIECE, actif=True, familles=()):
    return {
        "nom": nom, "rubrique": rubrique, "nature": nature, "unite": unite,
        "actif": actif, "familles": tuple(familles),
    }


CATALOGUE_DEPART = [
    # Ruche 10 cadres
    _article("corps de ruche", RUCHE, familles=[RUCHE_10]),
    _article("hausse", RUCHE, familles=[RUCHE_10]),
    _article("plancher", RUCHE, familles=[RUCHE_10]),
    _article("tiroir", RUCHE, familles=[RUCHE_10]),
    _article("grille à reine", RUCHE, familles=[RUCHE_10]),
    _article("couvre-cadre à rebord", RUCHE, familles=[RUCHE_10]),
    _article("couvre-cadre sans rebord", RUCHE, familles=[RUCHE_10]),
    _article("toit", RUCHE, familles=[RUCHE_10]),
    _article("chasse-abeilles", RUCHE, familles=[RUCHE_10]),
    _article("partition chaude", RUCHE, familles=[RUCHE_10]),
    _article("partition froide", RUCHE, familles=[RUCHE_10]),
    _article("porte blanche", RUCHE, familles=[RUCHE_10]),
    _article("porte verte", RUCHE, familles=[RUCHE_10]),
    _article("muselière", RUCHE, familles=[RUCHE_10]),

    # Cadres, communs à Ruche 10 cadres et Ruchette 6 cadres
    _article("cadre de corps", RUCHE, familles=[RUCHE_10, RUCHETTE_6]),
    _article("cadre de hausse", RUCHE, familles=[RUCHE_10, RUCHETTE_6]),
    _article("cadre à jambage", RUCHE, familles=[RUCHE_10, RUCHETTE_6]),

    # Nourrisseurs, communs à Ruche 10 cadres et Ruchette 6 cadres
    _article("nourrisseur rond", RUCHE, familles=[RUCHE_10, RUCHETTE_6]),
    _article("nourrisseur rectangulaire", RUCHE, familles=[RUCHE_10, RUCHETTE_6]),

    # Ruchette 6 cadres
    _article("corps de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("hausse de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("plancher de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("tiroir de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("couvre-cadre à rebord de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("couvre-cadre sans rebord de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("toit de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("partition chaude de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("partition froide de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("porte blanche de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("porte verte de ruchette", RUCHE, familles=[RUCHETTE_6]),
    _article("muselière de ruchette", RUCHE, familles=[RUCHETTE_6]),

    # Miniplus — tous inactifs
    _article("corps de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),
    _article("plancher de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),
    _article("toit de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),
    _article("cadre de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),
    _article("partition chaude de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),
    _article("partition froide de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),
    _article("porte blanche de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),
    _article("porte verte de Miniplus", RUCHE, actif=False, familles=[MINIPLUS]),

    # Apidea
    _article("Apidea complet", RUCHE, familles=[APIDEA]),
    _article("cadron", RUCHE, familles=[APIDEA]),
    _article("nourrisseur d'Apidea interne", RUCHE, familles=[APIDEA]),
    _article("nourrisseur d'Apidea de dessus", RUCHE, familles=[APIDEA]),
    _article("porte d'Apidea", RUCHE, familles=[APIDEA]),
    _article("toit d'Apidea", RUCHE, familles=[APIDEA]),
    _article("plancher d'Apidea", RUCHE, familles=[APIDEA]),

    # Élevage
    _article("bigoudi", ELEVAGE, actif=False),
    _article("cupule", ELEVAGE, nature=CONSOMMABLE),
    _article("outil de picking", ELEVAGE),
    _article("cadre d'élevage", ELEVAGE),
    _article("loupe", ELEVAGE),

    # Visite
    _article("brosse", VISITE),
    _article("lève-cadre", VISITE),
    _article("cage à reine", VISITE),
    _article("marqueur à reine", VISITE),
    _article("tenue complète", VISITE),
    _article("vareuse", VISITE),
    _article("voile", VISITE),
    _article("enfumoir", VISITE),
    _article("briquet", VISITE),
    _article("carton", VISITE, nature=CONSOMMABLE),

    # Atelier
    _article("fil de fer", ATELIER, nature=CONSOMMABLE, unite="bobine"),
    _article("clou", ATELIER, nature=CONSOMMABLE),
    _article("marteau", ATELIER),
    _article("cire gaufrée", ATELIER, nature=CONSOMMABLE, unite="feuille"),

    # Récolte
    _article("seau", RECOLTE),
    _article("maturateur", RECOLTE),
    _article("extracteur", RECOLTE),
    _article("double-passoire", RECOLTE),
    _article("fourchette à désoperculer", RECOLTE),
    _article("rouleau à désoperculer", RECOLTE),
    _article("huile pour roulement", RECOLTE, nature=CONSOMMABLE, unite="flacon"),
    _article("hygromètre", RECOLTE),
    _article("peson", RECOLTE),
    _article("pot", RECOLTE, nature=CONSOMMABLE),
    _article("couvercle de pot", RECOLTE, nature=CONSOMMABLE),
    _article("mélangeur", RECOLTE),
]


def charger_catalogue_depart():
    """Crée les articles du catalogue de départ qui n'existent pas
    encore (reconnus par leur nom et leur rubrique). Ne modifie ni ne
    supprime jamais un article existant, et ne crée aucun mouvement :
    tous les stocks créés restent à 0. Retourne un résumé (nombre
    d'articles créés / déjà présents)."""
    familles_cache = {}
    crees = 0
    deja_presents = 0
    for data in CATALOGUE_DEPART:
        article, cree = Article.objects.get_or_create(
            nom=data["nom"], rubrique=data["rubrique"],
            defaults={
                "nature": data["nature"],
                "unite": data["unite"],
                "actif": data["actif"],
            },
        )
        if not cree:
            deja_presents += 1
            continue
        crees += 1
        familles = []
        for nom_famille in data["familles"]:
            famille = familles_cache.get(nom_famille)
            if famille is None:
                famille, _ = FamilleMateriel.objects.get_or_create(nom=nom_famille)
                familles_cache[nom_famille] = famille
            familles.append(famille)
        if familles:
            article.familles_compatibles.set(familles)
    return {"crees": crees, "deja_presents": deja_presents}
