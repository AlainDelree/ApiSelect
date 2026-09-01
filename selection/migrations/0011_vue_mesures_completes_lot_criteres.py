# Adapte la vue `vue_mesures_completes` au découplage des poids (issue
# #19) : la jointure vers selection_poidscritere passe désormais par
# campagne.lot_criteres_id (via selection_campagneelevage) plutôt que
# directement par campagne_id. Migration RunSQL séparée (DROP + CREATE) —
# on ne modifie jamais une migration de vue déjà appliquée (cf.
# 0002_vues_sql.py, 0003, 0004).

from django.db import migrations

DROP_VUE_MESURES_COMPLETES = "DROP VIEW IF EXISTS vue_mesures_completes;"

# Version précédente (0004), utilisée comme SQL de reverse pour revenir à
# l'état d'avant cette migration (jointure directe sur campagne_id, encore
# valable au moment du reverse puisque 0010 serait unappliquée après).
VUE_MESURES_COMPLETES_AVEC_CAMPAGNE_ID = """
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

# Nouvelle version (issue #19) : la jointure vers selection_poidscritere
# passe par campagne.lot_criteres_id plutôt que directement par
# campagne_id (PoidsCritere n'a plus de FK campagne, cf. 0010).
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
    ON pc.lot_id = camp.lot_criteres_id AND pc.critere_id = m.critere_id;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('selection', '0010_lot_criteres'),
    ]

    operations = [
        # DROP avant modification, comme 0004 vis-à-vis de 0003 : lève la
        # dépendance PostgreSQL sur selection_poidscritere.campagne_id
        # (supprimée par 0010) avant de recréer la vue avec la nouvelle
        # jointure. Au reverse, ce DROP recrée la version 0004.
        migrations.RunSQL(
            sql=DROP_VUE_MESURES_COMPLETES,
            reverse_sql=DROP_VUE_MESURES_COMPLETES + VUE_MESURES_COMPLETES_AVEC_CAMPAGNE_ID,
        ),
        migrations.RunSQL(
            sql=CREATE_VUE_MESURES_COMPLETES,
            reverse_sql=DROP_VUE_MESURES_COMPLETES,
        ),
    ]
