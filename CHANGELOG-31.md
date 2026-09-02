## Issue #31 — `Mesure.campagne` obligatoire

- `selection/models.py` : `Mesure.campagne` passe de `on_delete=SET_NULL,
  null=True, blank=True` à `on_delete=PROTECT` (champ requis, plus de
  `null`/`blank`). Empêche la création de mesures invisibles dans le
  tableau de résultats (`/selection/resultats/`), qui filtre par
  campagne. `PROTECT` retenu plutôt que `CASCADE` pour éviter qu'une
  suppression de campagne ne vide silencieusement des mesures.
- `selection/migrations/0015_mesure_campagne_obligatoire.py` : migration
  correspondante. Vérifié avant écriture qu'aucune Mesure réelle n'a de
  campagne nulle : 0 mesure au total sur `apiselect` (production), et
  2 mesures sur `apiselect_dev`, aucune avec `campagne_id` NULL — aucune
  correction de données nécessaire.
- `selection/admin.py` : `MesureAdmin` affichait déjà `campagne` en
  `list_display`/`list_filter`/`autocomplete_fields` ; le formulaire
  d'admin dérive automatiquement le caractère requis de `blank=False`,
  aucun changement nécessaire.
- `selection/tests.py` : `MesureCampagneObligatoireTests` — une Mesure
  sans campagne est rejetée par `full_clean()` ; une Mesure avec
  campagne reste valide.
