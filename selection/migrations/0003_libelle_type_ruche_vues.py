# Corrige l'affichage de `ruche_identifiant` dans vue_mesures_completes et
# vue_colonies_actives : la migration 0002 concaténait le code technique
# brut du type de ruche (ex. "DADANT10 n°3") au lieu de son libellé humain
# (ex. "Dadant 10 n°3"). On DROP + CREATE les deux vues plutôt que de
# modifier 0002, déjà appliquée.

from django.db import migrations

# Traduction code -> libellé, dupliquée depuis TypeRuche.choices
# (selection/models.py) : compromis accepté pour avoir un affichage lisible
# directement dans pgAdmin, sans recalcul côté Python. À METTRE À JOUR si un
# type de ruche est ajouté/modifié dans TypeRuche.choices.
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

# Définitions précédentes (0002) — code technique brut, sans traduction —
# utilisées comme SQL de reverse pour revenir à l'état d'avant cette
# migration.
VUE_MESURES_COMPLETES_BRUTE = """
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

VUE_COLONIES_ACTIVES_BRUTE = """
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

DROP_VUE_MESURES_COMPLETES = "DROP VIEW IF EXISTS vue_mesures_completes;"
DROP_VUE_COLONIES_ACTIVES = "DROP VIEW IF EXISTS vue_colonies_actives;"


class Migration(migrations.Migration):

    dependencies = [
        ("selection", "0002_vues_sql"),
    ]

    operations = [
        migrations.RunSQL(
            sql=DROP_VUE_MESURES_COMPLETES + VUE_MESURES_COMPLETES_AVEC_LIBELLE,
            reverse_sql=DROP_VUE_MESURES_COMPLETES + VUE_MESURES_COMPLETES_BRUTE,
        ),
        migrations.RunSQL(
            sql=DROP_VUE_COLONIES_ACTIVES + VUE_COLONIES_ACTIVES_AVEC_LIBELLE,
            reverse_sql=DROP_VUE_COLONIES_ACTIVES + VUE_COLONIES_ACTIVES_BRUTE,
        ),
    ]
