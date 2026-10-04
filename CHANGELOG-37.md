# Issue #37 — Correction de la mise en page des fiches de terrain PDF (largeurs de colonnes)

## Corrigé

- Cause racine (issue #30 constatée visuellement par Alain) : avec
  xhtml2pdf 0.2.17, la largeur d'une colonne de tableau est recalculée
  à partir de **chaque** `<td>` rencontrée (pas seulement l'en-tête) ;
  dès qu'une cellule de donnée n'a aucun contenu (case à remplir à la
  main), son `width` est écrasé par la seule somme du padding, ce qui
  réduit la colonne à quelques pixels — d'où la colonne « Note libre »
  écrasée (fiche rapide) et les 5 colonnes de mesure illisibles (fiche
  approfondie). De plus, `<colgroup>/<col>` (utilisés par la fiche
  approfondie) n'ont aucun gestionnaire dans xhtml2pdf et sont donc
  purement décoratifs : ils ne définissaient aucune largeur réelle,
  d'où les colonnes Colonie/Lignée reine qui se partageaient le tiers
  de la page chacune.

- `selection/templates/selection/fiche_rapide_pdf.html` : largeur de
  chaque colonne définie en pourcentage via des classes CSS
  (`.col-colonie` 8 %, `.col-lignee` 10 %, `.col-critere` 15 %
  (×4 = 60 %), `.col-note-libre` 22 %, total 100 %) appliquées à la
  fois sur les `<th>` **et** sur chaque `<td>` de chaque ligne (y
  compris les cases vides), pour contourner le recalcul destructeur
  ci-dessus. Lignes portées à 1.3 cm de hauteur. Attribut `repeat="1"`
  sur `<table>` pour répéter la ligne d'en-tête sur chaque page.

- `selection/templates/selection/fiche_approfondie_pdf.html` : passage
  en paysage (`@page { size: A4 landscape; }`), suppression du
  `<colgroup>` inopérant, largeur de chaque colonne définie en
  pourcentage via des classes CSS (`.col-colonie` 12 %, `.col-lignee`
  14 %, `.col-critere` 14.8 % (×5 = 74 %), total 100 %) appliquées sur
  `<th>` et chaque `<td>`, y compris les cases de valeur brute vides.
  Lignes portées à 1.3 cm, taille de police des en-têtes remontée à
  9 pt (l'espace gagné par le paysage rend le passage à la ligne entre
  mots suffisant, plus besoin de réduire la police). Attribut
  `repeat="1"` sur `<table>`.

- `selection/templates/selection/_bandeau_test.html` : dans les PDF
  uniquement (nouveau paramètre `pour_pdf` passé par les deux gabarits
  PDF via `{% include ... with pour_pdf=True %}`), l'émoji
  d'avertissement ⚠️ est remplacé par le texte `[ATTENTION]` — la
  police embarquée par xhtml2pdf ne gère pas cet émoji et affichait
  deux carrés noirs à la place. La page web (bandeau affiché sur
  calendrier/résultats/tâches/diagnostic/formulaire) n'est pas
  modifiée, elle garde l'émoji.

Non modifié volontairement : le découpage d'une ligne entre deux pages
n'est pas explicitement désactivable dans cette version de xhtml2pdf
(l'option `splitByRow` du tableau est câblée en dur côté bibliothèque,
sans réglage HTML/CSS exposé) ; en pratique, avec des hauteurs de ligne
réduites (1.3 cm), reportlab déplace déjà la ligne entière sur la page
suivante plutôt que de la couper, sauf cas limite d'une ligne plus
haute qu'une page entière (non applicable ici).

## Ajouté

- `selection/tests.py`,
  `FichesTerrainPdfTests.test_fiche_approfondie_generee_en_paysage` :
  vérifie (même procédé que le test du bandeau — interception du HTML
  juste avant l'appel à `pisa.CreatePDF`) que le CSS généré pour la
  fiche approfondie contient bien `landscape`.

Tests existants (`python manage.py test selection`, 138 tests)
inchangés dans leur comportement, tous passent.
