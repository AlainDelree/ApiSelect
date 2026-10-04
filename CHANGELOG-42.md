# Issue #42 — Fiche rapide PDF : élargir la colonne Colonie (titre coupé)

## Modifié

- `selection/templates/selection/fiche_rapide_pdf.html` : largeur de
  la colonne « Colonie » portée de 8 % à 22 % (reprise de la largeur
  de « Note libre », la plus large), et largeur de « Note libre »
  ramenée de 22 % à 8 % en contrepartie, pour garder un total de
  100 %. Largeurs appliquées à l'identique sur les en-têtes (`th`) et
  sur chaque cellule de donnée (`td`, y compris les cellules vides),
  comme c'était déjà le cas. Corrige le titre « Colonie » coupé par
  la ligne de séparation de la colonne suivante et le retour à la
  ligne des libellés de ruche (ex. « Ruche 12 »). Aucun autre gabarit
  touché, fiche approfondie inchangée. Les 140 tests de `selection`
  passent sans modification.
