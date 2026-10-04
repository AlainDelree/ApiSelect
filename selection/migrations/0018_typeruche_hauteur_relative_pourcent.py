# Champ facultatif « hauteur relative (%) » sur TypeRuche (issue #49) :
# purement additif, aucune valeur existante remplie (null=True) — Alain
# complète lui-même les types concernés (ex. Apidea) depuis l'admin.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selection', '0017_typeruche_nombre_cadres'),
    ]

    operations = [
        migrations.AddField(
            model_name='typeruche',
            name='hauteur_relative_pourcent',
            field=models.PositiveSmallIntegerField(blank=True, help_text="Hauteur relative (%) de la bande de couleur, de 10 à 100, pour les types de boîte visuellement plus petits (ex. Apidea). Laisser vide, ou mettre 100, pour la hauteur complète actuelle (issue #49).", null=True, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(100)]),
        ),
    ]
