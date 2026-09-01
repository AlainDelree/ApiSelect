"""Recalcul automatique des étapes du calendrier d'élevage (issue #7,
révisé issue #14).

Se déclenche à chaque sauvegarde d'une CampagneElevage dont
`date_reference` est renseignée : recalcule `date_prevue` pour chacune
des étapes (cf. calculs.calculer_dates_etapes) via get_or_create + mise
à jour ciblée, en préservant les champs saisis à la main (`realisee`,
`date_reelle`, `notes`) plutôt qu'un delete+recreate qui les perdrait.

L'étape ELEVAGE_MALES (saturation) est facultative (issue #14) : elle
n'est créée/recalculée que si `elevage_males_actif` est coché sur la
campagne. Si le champ est décoché alors qu'une étape ELEVAGE_MALES
existe déjà (ex. campagne modifiée après coup), elle est supprimée
plutôt que laissée orpheline avec une date obsolète.

Auto-peuplement d'un LotCriteres (issue #20) : à la création d'un lot,
un PoidsCritere à poids=0 est créé pour chacun des CritereSelection
existants, pour éviter de les ajouter un par un via l'inline admin.
Les critères ajoutés après coup au système ne sont volontairement pas
rétro-ajoutés aux lots existants (hors périmètre, cf. issue #20).

Ce filet de sécurité est sauté quand la création passe par la page
d'ajout de l'admin (LotCriteresAdmin.save_model, selection/admin.py) :
le formset inline pré-rempli (issue #21) crée déjà les 9 PoidsCritere
avec les vraies valeurs saisies, et laisser le signal agir en plus
provoque un conflit sur la contrainte unique_poids_par_lot dès que ces
valeurs diffèrent de 0 (issue #22). Il reste actif pour toute autre
création (shell, script, API future).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .calculs import calculer_dates_etapes
from .models import (
    CampagneElevage,
    CritereSelection,
    EtapeCalendrier,
    LotCriteres,
    PoidsCritere,
    TypeEtapeCalendrier,
)


@receiver(post_save, sender=CampagneElevage)
def recalculer_etapes_calendrier(sender, instance, **kwargs):
    if not instance.date_reference:
        return

    for type_etape, date_prevue in calculer_dates_etapes(instance.date_reference).items():
        if type_etape == TypeEtapeCalendrier.ELEVAGE_MALES and not instance.elevage_males_actif:
            EtapeCalendrier.objects.filter(
                campagne=instance, type_etape=type_etape,
            ).delete()
            continue

        etape, cree = EtapeCalendrier.objects.get_or_create(
            campagne=instance, type_etape=type_etape,
            defaults={"date_prevue": date_prevue},
        )
        if not cree and etape.date_prevue != date_prevue:
            etape.date_prevue = date_prevue
            etape.save(update_fields=["date_prevue"])


@receiver(post_save, sender=LotCriteres)
def creer_poids_criteres_lot(sender, instance, created, **kwargs):
    if not created:
        return
    if getattr(instance, "_creation_via_admin_formulaire", False):
        return

    for critere in CritereSelection.objects.all():
        PoidsCritere.objects.get_or_create(
            lot=instance, critere=critere, defaults={"poids": 0},
        )
