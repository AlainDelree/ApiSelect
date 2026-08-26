# Vues PostgreSQL en lecture seule pour la couche de restitution.
#
# Ces vues centralisent les jointures/aplatissements de lecture ; la logique
# métier conditionnelle (calcul d'index, seuils éliminatoires) reste en
# Python (voir selection/calculs.py) et n'est volontairement PAS répliquée
# ici.

from django.db import migrations, models

CREATE_VUE_MESURES_COMPLETES = """
CREATE VIEW vue_mesures_completes AS
SELECT
    m.id AS mesure_id,
    m.date_mesure AS date_mesure,
    m.valeur_brute AS valeur_brute,
    m.score AS score,
    col.id AS colonie_id,
    ruc.id AS rucher_id,
    ruc.nom AS rucher_nom,
    rh.id AS ruche_id,
    (rh.type_ruche || ' n°' || rh.numero) AS ruche_identifiant,
    rn.id AS reine_id,
    rn.identifiant AS reine_identifiant,
    cr.id AS critere_id,
    cr.code AS critere_code,
    cr.nom AS critere_nom,
    camp.id AS campagne_id,
    camp.nom AS campagne_nom,
    pc.poids AS poids,
    pc.seuil_eliminatoire AS seuil_eliminatoire
FROM selection_mesure m
JOIN selection_colonie col ON col.id = m.colonie_id
JOIN selection_ruche rh ON rh.id = col.ruche_id
LEFT JOIN selection_rucher ruc ON ruc.id = rh.rucher_id
LEFT JOIN selection_reine rn ON rn.id = col.reine_actuelle_id
JOIN selection_critereselection cr ON cr.id = m.critere_id
LEFT JOIN selection_campagneelevage camp ON camp.id = m.campagne_id
LEFT JOIN selection_poidscritere pc
    ON pc.campagne_id = m.campagne_id AND pc.critere_id = m.critere_id;
"""

CREATE_VUE_COLONIES_ACTIVES = """
CREATE VIEW vue_colonies_actives AS
SELECT
    col.id AS colonie_id,
    col.mode_creation AS mode_creation,
    col.date_creation AS date_creation,
    rh.id AS ruche_id,
    (rh.type_ruche || ' n°' || rh.numero) AS ruche_identifiant,
    ruc.id AS rucher_id,
    ruc.nom AS rucher_nom,
    rn.id AS reine_id,
    rn.identifiant AS reine_identifiant
FROM selection_colonie col
JOIN selection_ruche rh ON rh.id = col.ruche_id
LEFT JOIN selection_rucher ruc ON ruc.id = rh.rucher_id
LEFT JOIN selection_reine rn ON rn.id = col.reine_actuelle_id
WHERE col.active = TRUE;
"""

# Chaîne mère -> grand-mère -> ... pour chaque reine. La génération 0 est
# la reine elle-même (ancre pratique pour retrouver son propre identifiant
# sans jointure supplémentaire côté appelant) ; génération 1 = mère,
# génération 2 = grand-mère, etc. `id` est une clé de substitution
# (ROW_NUMBER) exigée par Django pour une pk de modèle en lecture seule,
# la vue n'ayant pas de clé naturelle à une seule colonne.
CREATE_VUE_GENEALOGIE_REINES = """
CREATE VIEW vue_genealogie_reines AS
WITH RECURSIVE genealogie AS (
    SELECT
        r.id AS reine_id,
        r.identifiant AS reine_identifiant,
        r.id AS ancetre_id,
        r.identifiant AS ancetre_identifiant,
        0 AS generation
    FROM selection_reine r
    UNION ALL
    SELECT
        g.reine_id,
        g.reine_identifiant,
        mere.id AS ancetre_id,
        mere.identifiant AS ancetre_identifiant,
        g.generation + 1 AS generation
    FROM genealogie g
    JOIN selection_reine courante ON courante.id = g.ancetre_id
    JOIN selection_reine mere ON mere.id = courante.mere_id
)
SELECT
    ROW_NUMBER() OVER (ORDER BY reine_id, generation) AS id,
    reine_id,
    reine_identifiant,
    ancetre_id,
    ancetre_identifiant,
    generation
FROM genealogie;
"""

DROP_VUE_MESURES_COMPLETES = "DROP VIEW IF EXISTS vue_mesures_completes;"
DROP_VUE_COLONIES_ACTIVES = "DROP VIEW IF EXISTS vue_colonies_actives;"
DROP_VUE_GENEALOGIE_REINES = "DROP VIEW IF EXISTS vue_genealogie_reines;"


class Migration(migrations.Migration):

    dependencies = [
        ("selection", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=CREATE_VUE_MESURES_COMPLETES,
            reverse_sql=DROP_VUE_MESURES_COMPLETES,
        ),
        migrations.RunSQL(
            sql=CREATE_VUE_COLONIES_ACTIVES,
            reverse_sql=DROP_VUE_COLONIES_ACTIVES,
        ),
        migrations.RunSQL(
            sql=CREATE_VUE_GENEALOGIE_REINES,
            reverse_sql=DROP_VUE_GENEALOGIE_REINES,
        ),
        # CreateModel avec managed=False : ne génère aucun DDL, ne fait que
        # déclarer aux migrations Django l'état des modèles en lecture
        # seule pointant sur les vues créées ci-dessus (nécessaire pour que
        # `makemigrations` ne les détecte plus comme changement en attente).
        migrations.CreateModel(
            name='VueColonieActive',
            fields=[
                ('colonie_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('mode_creation', models.CharField(max_length=20)),
                ('date_creation', models.DateField()),
                ('ruche_id', models.BigIntegerField()),
                ('ruche_identifiant', models.CharField(max_length=140)),
                ('rucher_id', models.BigIntegerField(null=True)),
                ('rucher_nom', models.CharField(max_length=100, null=True)),
                ('reine_id', models.BigIntegerField(null=True)),
                ('reine_identifiant', models.CharField(max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Colonie active (vue)',
                'verbose_name_plural': 'Colonies actives (vue)',
                'db_table': 'vue_colonies_actives',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VueGenealogieReine',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('reine_id', models.BigIntegerField()),
                ('reine_identifiant', models.CharField(max_length=50)),
                ('ancetre_id', models.BigIntegerField()),
                ('ancetre_identifiant', models.CharField(max_length=50)),
                ('generation', models.PositiveIntegerField()),
            ],
            options={
                'verbose_name': 'Généalogie de reine (vue)',
                'verbose_name_plural': 'Généalogies de reines (vue)',
                'db_table': 'vue_genealogie_reines',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VueMesureComplete',
            fields=[
                ('mesure_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('date_mesure', models.DateField()),
                ('valeur_brute', models.CharField(max_length=100)),
                ('score', models.PositiveSmallIntegerField(null=True)),
                ('colonie_id', models.BigIntegerField()),
                ('rucher_id', models.BigIntegerField(null=True)),
                ('rucher_nom', models.CharField(max_length=100, null=True)),
                ('ruche_id', models.BigIntegerField()),
                ('ruche_identifiant', models.CharField(max_length=140)),
                ('reine_id', models.BigIntegerField(null=True)),
                ('reine_identifiant', models.CharField(max_length=50, null=True)),
                ('critere_id', models.BigIntegerField()),
                ('critere_code', models.SlugField()),
                ('critere_nom', models.CharField(max_length=100)),
                ('campagne_id', models.BigIntegerField(null=True)),
                ('campagne_nom', models.CharField(max_length=100, null=True)),
                ('poids', models.PositiveSmallIntegerField(null=True)),
                ('seuil_eliminatoire', models.DecimalField(decimal_places=2, max_digits=6, null=True)),
            ],
            options={
                'verbose_name': 'Mesure complète (vue)',
                'verbose_name_plural': 'Mesures complètes (vue)',
                'db_table': 'vue_mesures_completes',
                'managed': False,
            },
        ),
    ]
