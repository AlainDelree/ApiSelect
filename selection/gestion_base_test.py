"""Utilitaires partagés par les commandes `peupler_donnees_test` et
`purger_donnees_test` (issue #12) : marqueurs du jeu de données fictif et
vérification de sécurité contre un lancement accidentel sur la vraie base.
"""

from django.core.management.base import CommandError
from django.db import connection

# Nom de la vraie base, en dur : une vérification de sécurité explicite,
# pas seulement une convention basée sur settings.BASE_DE_TEST_ACTIVE (qui
# ne couvre que le cas positif 'apiselect_dev'). On lit le nom de base
# effectivement connecté (connection.settings_dict), pas une variable
# d'environnement qui pourrait être absente ou périmée.
NOM_BASE_REELLE = "apiselect"

NOM_RUCHER_TEST = "Rucher Test"
PREFIXE_TEST = "TEST-"


def verifier_base_de_test(nom_commande):
    """Lève CommandError si la commande tourne sur la vraie base."""
    nom_base_active = connection.settings_dict["NAME"]
    if nom_base_active == NOM_BASE_REELLE:
        raise CommandError(
            f"{nom_commande} refuse de s'exécuter : la base active est "
            f"'{NOM_BASE_REELLE}' (la vraie base, avec les vraies "
            f"données). Relancez avec 'apiselect --dev' pour cibler la "
            f"base de test 'apiselect_dev'."
        )
