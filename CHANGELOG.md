# Issue #33 — Correction tests DiagnosticsTests cassés par Mesure.campagne obligatoire

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

