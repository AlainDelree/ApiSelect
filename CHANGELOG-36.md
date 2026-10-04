# Issue #36 — Liens vers les fiches de terrain PDF dans l'interface

## Ajouté

- `templates/admin/base.html` : deux nouveaux liens dans la barre de
  liens affichée en haut de toutes les pages de l'admin, à la suite
  des quatre existants (Tableau de résultats de sélection, Calendrier
  d'élevage, Liste des tâches à venir, Diagnostic) :
  - « Fiche rapide » → `selection:fiche_rapide` (PDF direct, ouvert
    dans un nouvel onglet) ;
  - « Fiche approfondie » → `selection:fiche_approfondie_formulaire`
    (formulaire de choix des colonies avant génération du PDF).
  Même style et même séparateur (`·`) que les liens existants, noms
  d'URL Django utilisés (aucune adresse écrite en dur). Le bandeau
  « BASE DE TEST » n'est pas touché.

- `selection/tests.py`, méthode
  `LiensSelectionToutesPagesAdminTests.test_liens_fiches_pdf_presents_sur_laccueil` :
  vérifie que la page d'accueil de l'admin contient bien les liens
  vers `selection:fiche_rapide` et
  `selection:fiche_approfondie_formulaire`.
