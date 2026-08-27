"""Recalcul automatique des étapes du calendrier d'élevage (issue #7).

Se déclenche à chaque sauvegarde d'une CampagneElevage dont
`date_reference` est renseignée : recalcule `date_prevue` pour chacune
des étapes (cf. calculs.calculer_dates_etapes) via get_or_create + mise
à jour ciblée, en préservant les champs saisis à la main (`realisee`,
`date_reelle`, `notes`) plutôt qu'un delete+recreate qui les perdrait.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .calculs import calculer_dates_etapes
from .models import CampagneElevage, EtapeCalendrier


@receiver(post_save, sender=CampagneElevage)
def recalculer_etapes_calendrier(sender, instance, **kwargs):
    if not instance.date_reference:
        return

    for type_etape, date_prevue in calculer_dates_etapes(instance.date_reference).items():
        etape, cree = EtapeCalendrier.objects.get_or_create(
            campagne=instance, type_etape=type_etape,
            defaults={"date_prevue": date_prevue},
        )
        if not cree and etape.date_prevue != date_prevue:
            etape.date_prevue = date_prevue
            etape.save(update_fields=["date_prevue"])
