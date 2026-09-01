## Issue #23 — Clarifier les critères ambigus (Miel/Récolte, Propreté/Nettoyage) dans le formulaire

- `selection/admin.py` : dans `PoidsCritereInline`, ajout de deux
  classes locales à ce fichier :
  - `ChampCritereAvecRepere` (sous-classe de `forms.ModelChoiceField`)
    surcharge `label_from_instance` pour afficher, uniquement dans ce
    formulaire, un court repère entre parenthèses après le nom du
    critère quand celui-ci prête à confusion. Repères retenus (basés
    sur le contenu réel de `CritereSelection.description`, migration
    `0005_peupler_criteres_selection.py`) :
    - Santé — inchangé
    - Propreté (état du plateau)
    - Agressivité — inchangé
    - Tenue au cadre — inchangé
    - Nettoyage des rayons (test, temps de nettoyage)
    - Récolte (comparée à la moyenne du rucher)
    - Couvain — inchangé
    - Miel (provision stockée)
    - Pollen — inchangé
  - `SelectCritereAvecTitre` (sous-classe de `forms.Select`) surcharge
    `create_option` pour ajouter un attribut HTML `title` sur chaque
    `<option>`, avec la description complète du critère (consultable
    au survol).
  - `PoidsCritereInline.formfield_for_foreignkey` branche ces deux
    classes uniquement pour le champ `critere`. `autocomplete_fields`
    a été retiré de cet inline (il n'y avait que 9 critères ; le
    widget d'autocomplétion Django récupère ses libellés par AJAX via
    `str(obj)` côté `CritereSelectionAdmin`, ce qui aurait ignoré
    `label_from_instance` — un select classique convient mieux ici).
  - `CritereSelection.nom` n'est pas modifié : reste le libellé
    officiel affiché ailleurs (`CritereSelectionAdmin`, tableau de
    résultats, fiches PDF, calendrier), aucun de ces écrans ne passe
    par `PoidsCritereInline`.
- `selection/tests.py` : nouveau
  `PoidsCritereInlineRepereDesambiguisationTests` (4 tests) — vérifie
  que les libellés de "Miel"/"Récolte" et "Propreté"/"Nettoyage des
  rayons" diffèrent et contiennent un repère supplémentaire, que
  `CritereSelection.nom` reste inchangé en base, et que l'attribut
  HTML `title` de l'option contient bien la description complète.
- Vérifié : suite complète `selection.tests` (80 tests) exécutée avec
  succès dans un venv Python temporaire créé pour l'occasion (Django
  5.0, psycopg2-binary, python-dotenv, xhtml2pdf installés localement,
  connexion à PostgreSQL local existante), puis supprimé après usage.
  Les 2 échecs observés lors d'une première passe
  (`BandeauBaseTestTests`) sont dus à la variable d'environnement
  `DJANGO_DB_NAME=apiselect_dev` déjà positionnée dans le shell de la
  session — préexistant, sans lien avec ce changement (confirmé en
  relançant la suite sans cette variable : 80/80 OK).
