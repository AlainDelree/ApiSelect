# Issue #47 — Tuiles de ruches : silhouette proportionnelle au nombre de cadres, gris par défaut

## Ajouté

- `selection/models.py` : champ facultatif `TypeRuche.nombre_cadres`
  (entier, migration `0017_typeruche_nombre_cadres.py` purement
  additive, aucune valeur existante remplie — à compléter dans l'admin).
  Visible/modifiable dans `selection/admin.py` (`TypeRucheAdmin`).
- `gestion/affichage.py` : fonction `bande_ruche(ruche)` — couleur de
  la ruche (gris moyen fixe `#9e9e9e` par défaut si vide), largeur
  colorée proportionnelle au nombre de cadres du type (centrée entre
  deux bandes blanches égales ; pleine largeur si inconnu ou ≥ 10), et
  libellé accessible (ex. « Ruchette 6 cadres, couleur bleue »).
  Exposée aux templates via le filtre `bande_ruche` dans
  `gestion/templatetags/gestion_extras.py`.

## Modifié

- `gestion/templates/gestion/_tuile_ruche.html` : la bande de la tuile
  d'accueil utilise désormais `bande_ruche` (largeur/marge en %,
  `role="img"` + `aria-label`) au lieu d'une bande pleine largeur fixe.
- `gestion/templates/gestion/fiche_colonie.html` : la bande (même
  couleur, même proportion) est reprise en tête de la fiche, à la
  place de l'ancien aperçu de couleur (pastille ronde) dans le bloc
  « Ruche ».
- `gestion/static/gestion/style.css` : `.tuile-bande` devient un
  conteneur blanc fixe de 34 px de haut avec cadre fin (visible en
  thème clair et sombre), `.tuile-bande-couleur` dessine la portion
  colorée positionnée/dimensionnée en %, `.fiche-bande` ajoute le cadre
  sur la fiche colonie (pas de bordure héritée d'une tuile parente).
- `gestion/tests.py` : nouvelle classe `BandeRucheTests` (10 cadres →
  pleine largeur, ruchette 6 cadres → proportion 60 % centrée entre
  deux bandes de 20 %, nombre de cadres inconnu → pleine largeur,
  couleur absente/vidée → gris par défaut, libellé accessible, rendu
  identique sur la tuile d'accueil et la fiche colonie, ruche sans
  colonie active toujours marquée « vide »).

Aucune dépendance ajoutée à `selection` au-delà de l'exception déjà en
place (lecture de `Ruche`/`TypeRuche`/`Colonie`, cf. CONTEXTE.md).
Aucun SQL spécifique à PostgreSQL. `python manage.py test selection
gestion` : 185 tests, OK.
