from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from selection.gestion_base_test import NOM_RUCHER_TEST, PREFIXE_TEST, verifier_base_de_test
from selection.models import (
    CampagneElevage,
    Colonie,
    CritereSelection,
    LotCriteres,
    Mesure,
    ModeCreationColonie,
    PoidsCritere,
    Reine,
    Ruche,
    Rucher,
    TypeMesure,
    TypeRuche,
)


class Command(BaseCommand):
    help = (
        "Peuple un rucher fictif (\"Rucher Test\", colonies/reines "
        "préfixées TEST-, campagne fictive) pour tester l'outil de bout "
        "en bout sans toucher aux vraies données. Refuse de s'exécuter "
        "si la base active est 'apiselect' (vraie base) — lancer avec "
        "'apiselect --dev' au préalable."
    )

    def handle(self, *args, **options):
        verifier_base_de_test("peupler_donnees_test")

        if Rucher.objects.filter(nom=NOM_RUCHER_TEST).exists():
            self.stdout.write(self.style.WARNING(
                f"Le rucher « {NOM_RUCHER_TEST} » existe déjà : lancez "
                "d'abord 'purger_donnees_test' pour repartir d'un jeu "
                "propre."
            ))
            return

        annee = date.today().year
        type_ruche = TypeRuche.objects.get(code="DADANT10")

        with transaction.atomic():
            rucher = Rucher.objects.create(
                nom=NOM_RUCHER_TEST,
                localisation="Emplacement fictif — données de test",
                notes="Créé par la commande peupler_donnees_test (issue #12).",
            )

            reine_normale = Reine.objects.create(identifiant=f"{PREFIXE_TEST}R1")
            reine_exclue = Reine.objects.create(identifiant=f"{PREFIXE_TEST}R2")
            reine_sans_mesure = Reine.objects.create(identifiant=f"{PREFIXE_TEST}R3")

            colonie_normale = Colonie.objects.create(
                ruche=Ruche.objects.create(type_ruche=type_ruche, numero=901, rucher=rucher),
                reine_actuelle=reine_normale,
                mode_creation=ModeCreationColonie.ACHAT,
                date_creation=date(annee, 4, 1),
                active=True,
            )
            colonie_exclue = Colonie.objects.create(
                ruche=Ruche.objects.create(type_ruche=type_ruche, numero=902, rucher=rucher),
                reine_actuelle=reine_exclue,
                mode_creation=ModeCreationColonie.ESSAIM_ARTIFICIEL,
                date_creation=date(annee, 4, 1),
                active=True,
            )
            colonie_sans_mesure = Colonie.objects.create(
                ruche=Ruche.objects.create(type_ruche=type_ruche, numero=903, rucher=rucher),
                reine_actuelle=reine_sans_mesure,
                mode_creation=ModeCreationColonie.ORIGINE_INCONNUE,
                date_creation=date(annee, 4, 1),
                active=True,
            )

            lot_criteres = LotCriteres.objects.create(
                nom=f"{PREFIXE_TEST}Lot fictif {annee}",
                notes="Lot de critères fictif créé par peupler_donnees_test.",
            )

            campagne = CampagneElevage.objects.create(
                nom=f"{PREFIXE_TEST}Campagne fictive {annee}",
                annee=annee,
                date_reference=date(annee, 6, 1),
                lot_criteres=lot_criteres,
                notes="Campagne fictive créée par peupler_donnees_test.",
            )

            # Le signal post_save de LotCriteres (issue #20) a déjà créé un
            # PoidsCritere à poids=0 pour chacun des critères existants : on
            # ajuste les valeurs plutôt que d'en créer de nouveaux.
            critere_sante = CritereSelection.objects.get(code="SANTE")
            for critere in CritereSelection.objects.exclude(code="SANTE"):
                PoidsCritere.objects.filter(
                    lot=lot_criteres, critere=critere,
                ).update(poids=5)
            PoidsCritere.objects.filter(
                lot=lot_criteres, critere=critere_sante,
            ).update(poids=8, seuil_eliminatoire=Decimal("2"))

            date_mesure = date(annee, 5, 15)

            # Colonie normale : mesures variées sur les deux passes, index exploitable.
            for critere, score in zip(
                CritereSelection.objects.filter(type_mesure=TypeMesure.PASSE_RAPIDE),
                [4, 3, 4, 3],
            ):
                Mesure.objects.create(
                    colonie=colonie_normale, critere=critere, campagne=campagne,
                    date_mesure=date_mesure, valeur_brute="mesure fictive", score=score,
                )
            for critere, score in zip(
                CritereSelection.objects.filter(type_mesure=TypeMesure.PASSE_APPROFONDIE),
                [3, 4],
            ):
                Mesure.objects.create(
                    colonie=colonie_normale, critere=critere, campagne=campagne,
                    date_mesure=date_mesure, valeur_brute="mesure fictive", score=score,
                )

            # Colonie exclue : score de Santé (1) sous le seuil éliminatoire (2).
            Mesure.objects.create(
                colonie=colonie_exclue, critere=critere_sante, campagne=campagne,
                date_mesure=date_mesure, valeur_brute="maladie fictive", score=1,
            )

            # colonie_sans_mesure : volontairement aucune mesure créée.

        self.stdout.write(self.style.SUCCESS(
            f"Jeu de données fictif créé : rucher « {NOM_RUCHER_TEST} », "
            f"3 colonies ({reine_normale.identifiant} avec mesures, "
            f"{reine_exclue.identifiant} exclue par seuil, "
            f"{reine_sans_mesure.identifiant} sans mesure), "
            f"campagne « {campagne.nom} »."
        ))
