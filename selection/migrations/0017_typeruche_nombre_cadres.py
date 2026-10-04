# Champ facultatif « nombre de cadres » sur TypeRuche (issue #47) :
# purement additif, aucune valeur existante remplie (null=True) — Alain
# complète lui-même les types déjà en base depuis l'admin.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selection', '0016_ruche_couleur'),
    ]

    operations = [
        migrations.AddField(
            model_name='typeruche',
            name='nombre_cadres',
            field=models.PositiveSmallIntegerField(blank=True, help_text="Nombre de cadres de ce type de ruche (ex. 10 pour une Dadant 10, 6 pour une ruchette). Laisser vide si inconnu : la bande de couleur des tuiles et de la fiche colonie s'affiche alors pleine largeur — la valeur n'est jamais déduite du nom du type (issue #47).", null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
