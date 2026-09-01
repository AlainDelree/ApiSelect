from django.core.management.base import BaseCommand
from django.db import transaction

from selection.gestion_base_test import NOM_RUCHER_TEST, PREFIXE_TEST, verifier_base_de_test
from selection.models import CampagneElevage, Colonie, LotCriteres, Reine, Ruche, Rucher


class Command(BaseCommand):
    help = (
        "Supprime uniquement le jeu de données fictif créé par "
        "peupler_donnees_test (rucher \"Rucher Test\", colonies/ruches "
        "associées, campagne et reines préfixées TEST-). Refuse de "
        "s'exécuter si la base active est 'apiselect' (vraie base)."
    )

    def handle(self, *args, **options):
        verifier_base_de_test("purger_donnees_test")

        with transaction.atomic():
            colonies = Colonie.objects.filter(ruche__rucher__nom=NOM_RUCHER_TEST)
            nb_colonies = colonies.count()
            colonies.delete()

            ruches = Ruche.objects.filter(rucher__nom=NOM_RUCHER_TEST)
            nb_ruches = ruches.count()
            ruches.delete()

            campagnes = CampagneElevage.objects.filter(nom__startswith=PREFIXE_TEST)
            nb_campagnes = campagnes.count()
            campagnes.delete()

            # Supprimé après les campagnes (PROTECT empêche de supprimer un
            # LotCriteres encore référencé par une campagne, cf. issue #19).
            lots_criteres = LotCriteres.objects.filter(nom__startswith=PREFIXE_TEST)
            lots_criteres.delete()

            reines = Reine.objects.filter(identifiant__startswith=PREFIXE_TEST)
            nb_reines = reines.count()
            reines.delete()

            ruchers = Rucher.objects.filter(nom=NOM_RUCHER_TEST)
            nb_ruchers = ruchers.count()
            ruchers.delete()

        self.stdout.write(self.style.SUCCESS(
            f"Purge terminée : {nb_ruchers} rucher(s), {nb_ruches} ruche(s), "
            f"{nb_colonies} colonie(s) (mesures/configurations/événements "
            f"associés supprimés en cascade), {nb_campagnes} campagne(s), "
            f"{nb_reines} reine(s)."
        ))
