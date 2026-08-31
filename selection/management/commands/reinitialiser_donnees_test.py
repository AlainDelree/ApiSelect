from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Enchaîne purger_donnees_test puis peupler_donnees_test pour "
        "repartir d'un jeu de données de test fictif fraîchement recréé "
        "en une seule commande. Refuse de s'exécuter si la base active "
        "est 'apiselect' (vraie base), via la vérification déjà faite "
        "par purger_donnees_test."
    )

    def handle(self, *args, **options):
        call_command("purger_donnees_test")
        call_command("peupler_donnees_test")
