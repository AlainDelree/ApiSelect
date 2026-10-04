# Issue #44 — Fiches PDF : largeurs de colonnes de la fiche rapide, titres courts, plus de tiret dans Lignée

## Modifié

- `fiche_rapide_pdf.html` : nouvelles largeurs de colonnes (total 100 %)
  — Colonie 12 %, Lignée 10 %, les 4 colonnes de critères 11 % chacune
  (44 %), Note libre 34 %. L'issue #42 avait élargi Colonie à 22 % en
  réduisant Note libre à 8 %, rendant cette dernière inutilisable à la
  main (seul son usage réel) et les colonnes de critères inutilement
  larges pour simplement entourer un chiffre de 1 à 4. Vérifié par
  génération réelle du PDF (`pdftotext -layout`) avec un identifiant de
  ruche à 2 et 3 chiffres (« Ruche 12 », « Ruche 123 ») : tient à 12 %
  sans retour à la ligne, pas besoin de monter à 14 %. L'en-tête
  « Agressivité », trop large à 11 % en 10pt, passe en police 8pt
  (`th.col-critere`) plutôt que d'élargir la colonne, comme demandé.
- `fiche_rapide_pdf.html` et `fiche_approfondie_pdf.html` : titre de
  colonne « Lignée reine » → « Lignée » (texte statique du gabarit,
  « reine » jugé inutile) ; cellule Lignée vide (plus de « — ») quand
  la reine n'a pas de lignée connue — gênait plus qu'il n'aidait sur
  une fiche papier.
- Critère « Tenue au cadre » affiché « Tenue » sur la fiche rapide
  (« au cadre » sous-entendu) via une correspondance d'affichage simple
  dans `selection/views.py` (`TITRES_COURTS_CRITERES_PDF`, par code de
  critère, appliquée aux deux fiches PDF mais sans effet sur les
  critères approfondis qui n'y figurent pas) : n'affecte ni
  `CritereSelection.nom` en base, ni l'admin, ni le tableau de
  résultats — aucune migration. Tout critère absent de cette
  correspondance garde son nom complet.
- Tests (`selection/tests.py`, classe `FichesTerrainPdfTests`) :
  3 tests ajoutés (titres courts fiche rapide, titre court fiche
  approfondie, absence de tiret sur les deux fiches). Aucun test
  existant ne vérifiait l'ancien titre « Lignée reine » ou le tiret
  « — » — rien à adapter sur ce point, les 143 tests de `selection`
  passent (`python manage.py test selection`).
