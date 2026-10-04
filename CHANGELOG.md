# Issue #33 — Correction tests DiagnosticsTests cassés par Mesure.campagne obligatoire

# Issue #34 — Mise à jour de CONTEXTE.md (état actuel + règle de protection des données)

## Modifié

- `CONTEXTE.md` réécrit en place (lecture du code : modèles, admin,
  vues, commandes de gestion, migrations) pour refléter l'état réel du
  projet, condensé sous 4000 caractères (3994) :
  - nouvelle section « Règles de travail » en tête, avec la règle de
    protection des données `apiselect`/`apiselect_dev` (interdiction de
    `flush`/`dropdb`/`loaddata`/DELETE-TRUNCATE/`purgetest` et des
    commandes `purger_donnees_test`/`reinitialiser_donnees_test`/
    `peupler_donnees_test` sans accord explicite d'Alain), l'interdiction
    de `migrate` sur la vraie base, la règle des tests
    (`python manage.py test selection` uniquement) et l'absence de
    `git push` ;
  - ajout de `CelluleRoyale`, des lots de critères (`LotCriteres`,
    indépendants des campagnes), du calendrier à 4 étapes + étape
    facultative « Élevage des mâles », de `Mesure.campagne` obligatoire,
    des nouveaux modes d'acquisition des reines et du mode diagnostic ;
  - ajout de l'état des migrations (0010 à 0015 appliquées sur
    `apiselect_dev`, en attente sur la vraie base `apiselect`) ;
  - vocabulaire, documents de référence et calendrier condensés plutôt
    que supprimés ; mention de `Cours_Apiculture/` (jamais committé ni
    référencé dans une issue) conservée.

Aucun autre fichier touché.

## Corrigé

- `selection/tests.py`, classe `DiagnosticsTests` : les 3 tests
  `test_score_hors_intervalle_declenche_avertissement`,
  `test_score_dans_lintervalle_ne_declenche_rien`,
  `test_score_absent_ne_declenche_rien` créaient une `Mesure` sans
  `campagne`, devenue obligatoire par l'issue #31. Ajout d'un
  `LotCriteres` et d'une `CampagneElevage` dédiés par test (pattern de
  `MesureCampagneObligatoireTests`), assignés au champ `campagne` de
  chaque `Mesure`.
- Recherche systématique de tous les `Mesure.objects.create`/`Mesure(`
  du fichier : aucun autre cas sans `campagne` trouvé.

## Vérification

`python manage.py test selection` : 131 tests, OK (aucun échec).

