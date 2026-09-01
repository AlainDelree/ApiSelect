# Découplage des poids/seuils de la campagne (issue #19) : un "Lot de
# critères" indépendant, réutilisable par plusieurs campagnes d'une même
# saison, remplace le lien direct PoidsCritere -> CampagneElevage.

import django.db.models.deletion
from django.db import migrations, models


def supprimer_poids_criteres_lies_a_une_campagne(apps, schema_editor):
    """Supprime les PoidsCritere existants (structure incompatible : ils
    pointent vers une CampagneElevage, plus vers un LotCriteres). Vérifié
    en base 'apiselect' (vraie base) avant modification : aucune
    CampagneElevage ni aucun PoidsCritere réel n'existe à ce jour (cf.
    CONTEXTE.md — pas de campagne réelle créée). Seules des données
    fictives de test (apiselect_dev, via peupler_donnees_test) peuvent
    exister ; elles sont sans conséquence et facilement régénérées via
    'reinitialiser_donnees_test'."""
    PoidsCritere = apps.get_model("selection", "PoidsCritere")
    PoidsCritere.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('selection', '0009_orphelinage_et_suivi_cr'),
    ]

    operations = [
        migrations.RunPython(
            supprimer_poids_criteres_lies_a_une_campagne, migrations.RunPython.noop,
        ),
        migrations.CreateModel(
            name='LotCriteres',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(help_text='Ex. « Lot 2027 - priorité douceur ».', max_length=100, unique=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Lot de critères',
                'verbose_name_plural': 'Lots de critères',
                'ordering': ['nom'],
            },
        ),
        migrations.AddField(
            model_name='campagneelevage',
            name='lot_criteres',
            field=models.ForeignKey(blank=True, help_text="Lot de critères (poids + seuils) utilisé pour le calcul d'index de cette campagne (issue #19). Peut rester vide temporairement, le temps de choisir un lot ; PROTECT empêche de supprimer un lot encore référencé par une campagne.", null=True, on_delete=django.db.models.deletion.PROTECT, related_name='campagnes', to='selection.lotcriteres'),
        ),
        migrations.RemoveConstraint(
            model_name='poidscritere',
            name='unique_poids_par_campagne',
        ),
        migrations.RemoveField(
            model_name='poidscritere',
            name='campagne',
        ),
        migrations.AddField(
            model_name='poidscritere',
            name='lot',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='poids_criteres', to='selection.lotcriteres'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='poidscritere',
            name='critere',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poids_par_lot', to='selection.critereselection'),
        ),
        migrations.AlterModelOptions(
            name='poidscritere',
            options={'ordering': ['lot', 'critere__ordre'], 'verbose_name': 'Poids de critère', 'verbose_name_plural': 'Poids de critères'},
        ),
        migrations.AddConstraint(
            model_name='poidscritere',
            constraint=models.UniqueConstraint(fields=('lot', 'critere'), name='unique_poids_par_lot'),
        ),
    ]
