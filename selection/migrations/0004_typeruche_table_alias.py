# Remplace le TextChoices Python TypeRuche par une vraie table de référence
# avec alias d'affichage (cf. issue #4) : élimine la duplication de la liste
# des types de ruche entre selection/models.py et le CASE WHEN SQL codé en
# dur dans les vues (migration 0003, LIBELLE_TYPE_RUCHE_CASE).
#
# Conversion CharField -> ForeignKey faite en plusieurs étapes (champ
# temporaire + RunPython) plutôt qu'un AlterField direct, pour que la
# migration de données soit explicite et non destructive même si des
# Ruche existent déjà en base (aucune actuellement, mais on écrit la
# migration proprement, cf. issue).
#
# Ne modifie pas 0002/0003 (déjà appliquées) : DROP + CREATE des deux vues,
# comme le faisait déjà 0003 vis-à-vis de 0002.

import django.db.models.deletion
from django.db import migrations, models

# Source de vérité unique pour le peuplement initial : à ne pas confondre
# avec le contenu de la table une fois en production, modifiable ensuite
# librement depuis l'admin Django sans nouvelle migration.
TYPES_RUCHE_PAR_DEFAUT = [
    {
        "code": "DADANT10", "nom": "Dadant 10", "alias": "Ruche",
        "numerotation_permanente": True,
    },
    {
        "code": "RUCHETTE6", "nom": "Ruchette 6", "alias": "Ruchette",
        "numerotation_permanente": True,
    },
    {
        "code": "APIDEA", "nom": "Apidea", "alias": "",
        "numerotation_permanente": False,
    },
    {
        "code": "DH", "nom": "DH (double haussette)", "alias": "DH",
        "numerotation_permanente": False,
    },
]


def peupler_types_ruche(apps, schema_editor):
    TypeRuche = apps.get_model("selection", "TypeRuche")
    for donnees in TYPES_RUCHE_PAR_DEFAUT:
        TypeRuche.objects.create(**donnees)


def depeupler_types_ruche(apps, schema_editor):
    TypeRuche = apps.get_model("selection", "TypeRuche")
    codes = [donnees["code"] for donnees in TYPES_RUCHE_PAR_DEFAUT]
    TypeRuche.objects.filter(code__in=codes).delete()


def lier_ruches_existantes(apps, schema_editor):
    Ruche = apps.get_model("selection", "Ruche")
    TypeRuche = apps.get_model("selection", "TypeRuche")
    types_par_code = {t.code: t for t in TypeRuche.objects.all()}
    for ruche in Ruche.objects.all():
        ruche.type_ruche_fk = types_par_code[ruche.type_ruche]
        ruche.save(update_fields=["type_ruche_fk"])


def delier_ruches_existantes(apps, schema_editor):
    Ruche = apps.get_model("selection", "Ruche")
    for ruche in Ruche.objects.all():
        ruche.type_ruche = ruche.type_ruche_fk.code
        ruche.save(update_fields=["type_ruche"])


# CASE WHEN codé en dur (0003) -> jointure vers selection_typeruche +
# COALESCE(alias, nom) : une seule source de vérité, modifiable sans
# migration.
VUE_MESURES_COMPLETES_AVEC_JOINTURE = """
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
    (COALESCE(NULLIF(tr.alias, ''), tr.nom) || ' ' || rh.numero) AS ruche_identifiant,
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
JOIN selection_typeruche tr ON tr.id = rh.type_ruche_id
LEFT JOIN selection_rucher ruc ON ruc.id = rh.rucher_id
LEFT JOIN selection_reine rn ON rn.id = col.reine_actuelle_id
JOIN selection_critereselection cr ON cr.id = m.critere_id
LEFT JOIN selection_campagneelevage camp ON camp.id = m.campagne_id
LEFT JOIN selection_poidscritere pc
    ON pc.campagne_id = m.campagne_id AND pc.critere_id = m.critere_id;
"""

VUE_COLONIES_ACTIVES_AVEC_JOINTURE = """
CREATE VIEW vue_colonies_actives AS
SELECT
    col.id AS colonie_id,
    col.mode_creation AS mode_creation,
    col.date_creation AS date_creation,
    rh.id AS ruche_id,
    (COALESCE(NULLIF(tr.alias, ''), tr.nom) || ' ' || rh.numero) AS ruche_identifiant,
    ruc.id AS rucher_id,
    ruc.nom AS rucher_nom,
    rn.id AS reine_id,
    rn.identifiant AS reine_identifiant
FROM selection_colonie col
JOIN selection_ruche rh ON rh.id = col.ruche_id
JOIN selection_typeruche tr ON tr.id = rh.type_ruche_id
LEFT JOIN selection_rucher ruc ON ruc.id = rh.rucher_id
LEFT JOIN selection_reine rn ON rn.id = col.reine_actuelle_id
WHERE col.active = TRUE;
"""

# Définitions précédentes (0003) — CASE WHEN sur le code technique — utilisées
# comme SQL de reverse pour revenir à l'état d'avant cette migration.
LIBELLE_TYPE_RUCHE_CASE = """CASE rh.type_ruche
        WHEN 'DADANT10' THEN 'Dadant 10'
        WHEN 'RUCHETTE6' THEN 'Ruchette 6'
        WHEN 'APIDEA' THEN 'Apidea'
        WHEN 'DH' THEN 'DH (double haussette)'
        ELSE rh.type_ruche
    END"""

VUE_MESURES_COMPLETES_AVEC_LIBELLE = f"""
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
    ({LIBELLE_TYPE_RUCHE_CASE} || ' n°' || rh.numero) AS ruche_identifiant,
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

VUE_COLONIES_ACTIVES_AVEC_LIBELLE = f"""
CREATE VIEW vue_colonies_actives AS
SELECT
    col.id AS colonie_id,
    col.mode_creation AS mode_creation,
    col.date_creation AS date_creation,
    rh.id AS ruche_id,
    ({LIBELLE_TYPE_RUCHE_CASE} || ' n°' || rh.numero) AS ruche_identifiant,
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

DROP_VUE_MESURES_COMPLETES = "DROP VIEW IF EXISTS vue_mesures_completes;"
DROP_VUE_COLONIES_ACTIVES = "DROP VIEW IF EXISTS vue_colonies_actives;"


class Migration(migrations.Migration):

    dependencies = [
        ('selection', '0003_libelle_type_ruche_vues'),
    ]

    operations = [
        migrations.CreateModel(
            name='TypeRuche',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(help_text='Code technique stable (ex. DADANT10), utilisé en base et par les migrations de données. Ne pas modifier après coup.', max_length=20, unique=True)),
                ('nom', models.CharField(help_text='Nom complet (ex. Dadant 10).', max_length=100)),
                ('alias', models.CharField(blank=True, help_text="Libellé court pour l'affichage courant (ex. Ruche). Laisser vide pour utiliser le nom complet.", max_length=50)),
                ('numerotation_permanente', models.BooleanField(default=False, help_text='Coché si Type + numéro forment une identité stable dans le temps (une planche physique donnée porte toujours le même numéro), comme Dadant 10/Ruchette 6. Décoché pour une numérotation réutilisable sans identité permanente sur les planches, comme Apidea/DH.')),
            ],
            options={
                'verbose_name': 'Type de ruche',
                'verbose_name_plural': 'Types de ruche',
                'ordering': ['nom'],
            },
        ),
        migrations.RunPython(peupler_types_ruche, depeupler_types_ruche),
        # Les vues 0003 référencent directement rh.type_ruche (CASE WHEN) :
        # on les DROP ici, avant toute modification de la colonne, pour lever
        # la dépendance PostgreSQL (sinon RemoveField échouerait). Elles sont
        # recréées (jointure) tout à la fin de cette migration. Au reverse,
        # ce DROP se transforme en re-création de la version 0003 — mais
        # seulement une fois la colonne CharField d'origine restaurée par les
        # opérations suivantes (l'ordre d'unapply est l'inverse de cette
        # liste).
        migrations.RunSQL(
            sql=DROP_VUE_MESURES_COMPLETES,
            reverse_sql=DROP_VUE_MESURES_COMPLETES + VUE_MESURES_COMPLETES_AVEC_LIBELLE,
        ),
        migrations.RunSQL(
            sql=DROP_VUE_COLONIES_ACTIVES,
            reverse_sql=DROP_VUE_COLONIES_ACTIVES + VUE_COLONIES_ACTIVES_AVEC_LIBELLE,
        ),
        migrations.AddField(
            model_name='ruche',
            name='type_ruche_fk',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='ruches_fk', to='selection.typeruche',
            ),
        ),
        migrations.RunPython(lier_ruches_existantes, delier_ruches_existantes),
        migrations.RemoveField(
            model_name='ruche',
            name='type_ruche',
        ),
        migrations.RenameField(
            model_name='ruche',
            old_name='type_ruche_fk',
            new_name='type_ruche',
        ),
        migrations.AlterField(
            model_name='ruche',
            name='type_ruche',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ruches', to='selection.typeruche',
            ),
        ),
        migrations.AlterModelOptions(
            name='ruche',
            options={'ordering': ['type_ruche__nom', 'numero'], 'verbose_name': 'Ruche', 'verbose_name_plural': 'Ruches'},
        ),
        # Recréation finale, une fois la colonne type_ruche_id en place :
        # jointure vers selection_typeruche + COALESCE(alias, nom). Au
        # reverse, simple DROP (la version 0003 est recréée par le RunSQL
        # ci-dessus, unappliqué après celui-ci).
        migrations.RunSQL(
            sql=VUE_MESURES_COMPLETES_AVEC_JOINTURE,
            reverse_sql=DROP_VUE_MESURES_COMPLETES,
        ),
        migrations.RunSQL(
            sql=VUE_COLONIES_ACTIVES_AVEC_JOINTURE,
            reverse_sql=DROP_VUE_COLONIES_ACTIVES,
        ),
    ]
