# Généré à la main (issue #55) : migration purement additive pour le
# suivi des stocks (matériel et consommables), étape 1. Aucune donnée
# n'est créée ici — le catalogue de départ ne se charge que par le
# bouton dédié de la page « Stocks », jamais par une migration.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0002_vendeur'),
    ]

    operations = [
        migrations.CreateModel(
            name='FamilleMateriel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Famille de matériel',
                'verbose_name_plural': 'Familles de matériel',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=150)),
                ('rubrique', models.CharField(choices=[('RUCHE', 'Ruche et ruchette'), ('ELEVAGE', 'Élevage'), ('VISITE', 'Visite'), ('ATELIER', 'Atelier'), ('RECOLTE', 'Récolte'), ('AUTRE', 'Autre')], max_length=20)),
                ('nature', models.CharField(choices=[('DURABLE', 'Matériel durable'), ('CONSOMMABLE', 'Consommable')], max_length=20)),
                ('unite', models.CharField(help_text='Pièce, bobine, feuille, flacon, kg, litre…', max_length=30)),
                ('seuil_alerte', models.DecimalField(blank=True, decimal_places=2, help_text='Badge « Stock bas » si le stock descend sous ce seuil.', max_digits=10, null=True)),
                ('actif', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('familles_compatibles', models.ManyToManyField(blank=True, related_name='articles', to='gestion.famillemateriel')),
            ],
            options={
                'verbose_name': 'Article',
                'verbose_name_plural': 'Articles',
                'ordering': ['rubrique', 'nom'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together={('nom', 'rubrique')},
        ),
        migrations.CreateModel(
            name='MouvementStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.localdate)),
                ('quantite', models.DecimalField(decimal_places=2, max_digits=10)),
                ('motif', models.CharField(choices=[('STOCK_INITIAL', 'Stock initial'), ('ACHAT', 'Achat'), ('UTILISATION', 'Utilisation'), ('PERTE', 'Perte ou casse'), ('DON_VENTE', 'Don ou vente'), ('CORRECTION', "Correction d'inventaire")], max_length=20)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('numero_lot', models.CharField(blank=True, max_length=100)),
                ('date_peremption', models.DateField(blank=True, null=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mouvements', to='gestion.article')),
            ],
            options={
                'verbose_name': 'Mouvement de stock',
                'verbose_name_plural': 'Mouvements de stock',
                'ordering': ['-date', '-id'],
            },
        ),
    ]
