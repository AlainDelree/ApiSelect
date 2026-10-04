# Issue #49 — Silhouette des ruches : hauteur réduite par des bandes blanches en haut et en bas (petites boîtes)

## Ajouté

- `selection/models.py` : champ facultatif `TypeRuche.hauteur_relative_pourcent`
  (entier, 10 à 100, `null=True, blank=True`), pour les types de boîte
  visuellement plus petits (ex. Apidea). Vide ou 100 : comportement
  actuel inchangé (hauteur complète).
- `selection/migrations/0018_typeruche_hauteur_relative_pourcent.py` :
  migration purement additive, aucune valeur existante remplie —
  Alain complète lui-même les types concernés depuis l'admin.
- `selection/admin.py` : `hauteur_relative_pourcent` ajouté à
  `TypeRucheAdmin.list_display` et `list_editable`, comme
  `nombre_cadres`.

## Modifié

- `gestion/affichage.py` (`bande_ruche`) : calcule désormais aussi
  `hauteur_pourcent` et `marge_verticale_pourcent` à partir de
  `TypeRuche.hauteur_relative_pourcent`, avec la même arithmétique
  entière que pour la largeur (zone colorée centrée verticalement,
  deux bandes blanches hautes/basses égales). Le libellé accessible
  reste inchangé (type, nombre de cadres, couleur — rien sur la
  hauteur).
- `gestion/templates/gestion/_tuile_ruche.html` et
  `gestion/templates/gestion/fiche_colonie.html` : la bande colorée
  reçoit en plus `top`/`bottom` en pourcentage (`bande.marge_verticale_pourcent`),
  en complément de `left`/`width` existants.
- `gestion/static/gestion/style.css` : `.tuile-bande-couleur` ne fixe
  plus `top: 0; bottom: 0;` en dur (valeurs désormais toujours fournies
  en ligne par le gabarit) — le cadre de la bande (`.tuile-bande`,
  hauteur 34px, bordure) ne change pas, seule la zone colorée rétrécit.
- `gestion/tests.py` : nouvelle classe `BandeRucheHauteurTests` —
  hauteur vide ou 100 (bande inchangée), hauteur 50 (zone colorée
  centrée avec deux marges de 25 %), combinaison largeur 50 %
  (5 cadres) + hauteur 50 %, même rendu sur la tuile accueil et la
  fiche colonie, ruche sans colonie active toujours marquée « Vide ».
