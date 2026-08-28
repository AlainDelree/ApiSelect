## Issue #11 — Ajouter "Fusion/Réunion" comme mode de création de Colonie

- `selection/models.py` : ajout de `FUSION = "FUSION", "Fusion / Réunion"`
  à `ModeCreationColonie` (TextChoices), entre `ESSAIM_ARTIFICIEL` et
  `ORIGINE_INCONNUE`. Rappel du modèle conceptuel (déjà établi) :
  `mode_creation` décrit l'origine des abeilles de la colonie,
  indépendamment de l'origine de la reine actuelle — une reine achetée
  peut très bien être introduite dans une colonie issue d'une fusion.
- `selection/migrations/0007_alter_colonie_mode_creation.py` : migration
  `AlterField` générée par `makemigrations`. Nécessaire car Django
  historise la liste `choices` dans l'état des migrations (utilisée pour
  la cohérence des migrations et par certains outils, ex. formulaires
  admin générés à partir de l'état migré) — mais elle ne produit aucune
  opération SQL sur PostgreSQL : `mode_creation` reste un `CharField`
  simple (`max_length=20`), les choix ne sont pas contraints au niveau
  base de données. Aucune migration de données : aucune colonie
  existante n'est corrigée automatiquement (Alain corrigera lui-même la
  colonie concernée via l'admin).
- `selection/tests.py` : nouveau `ModeCreationColonieFusionTests` —
  vérifie qu'une `Colonie` avec `mode_creation=ModeCreationColonie.FUSION`
  est créée et passe `full_clean()` sans erreur.
- Admin Django (`selection/admin.py`) : aucune modification nécessaire,
  `ColonieAdmin` n'a pas de formulaire personnalisé pour `mode_creation` ;
  le champ est rendu à partir de `ModeCreationColonie.choices`, donc la
  nouvelle option "Fusion / Réunion" apparaît automatiquement dans le
  menu déroulant.
- Non vérifié en conditions réelles : la suite de tests n'a pas pu être
  exécutée dans ce worktree (pas de `.env`/identifiants PostgreSQL
  disponibles ici, connexion refusée en local). Vérification faite par
  relecture et `py_compile` uniquement — à confirmer par `python
  manage.py test selection` côté Alain.
