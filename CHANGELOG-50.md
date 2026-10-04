# Issue #50 — Observations : « confirmée » sans « doute » à l'affichage, signal « reine morte » sur la tuile

## Modifié

- `gestion/models.py`, `ObservationVisite` :
  - `confirmer()` fixe désormais aussi `certitude` à
    `CertitudeObservation.CONSTATE` (en plus du statut), pour qu'une
    observation confirmée ne reste jamais « en doute » en base — une
    fois le doute levé, il n'a plus de sens de l'afficher. `infirmer()`
    inchangé : la certitude d'origine est conservée telle quelle.
  - nouvelle méthode `libelle_statut_affichage()` : retourne la
    certitude (« constaté »/« doute ») tant que l'observation est
    ouverte, et le statut seul (« confirmée »/« infirmée ») une fois
    tranchée — sert à l'affichage dans l'historique des visites et la
    fiche colonie, pour ne plus mélanger les deux notions.
- `gestion/views.py` :
  - nouvelle fonction `_observation_reine_morte_confirmee_sans_remplacement(colonie)` :
    dernière observation « reine morte » confirmée de la colonie, `None`
    si un `EvenementColonie` de type `REMERAGE` existe à une date égale
    ou postérieure à la date de la visite de l'observation (ou si
    aucune observation « reine morte » confirmée n'existe). Une
    observation infirmée ou supprimée sort naturellement du filtre
    `statut=CONFIRMEE`, donc le signal disparaît avec elle.
  - `accueil` : chaque tuile reçoit `observation_reine_morte_confirmee`.
  - `fiche_colonie` : le contexte reçoit `observation_reine_morte_confirmee`.
- `gestion/templates/gestion/_tuile_ruche.html` :
  - tuile avec signal actif : classe `tuile-reine-morte` sur la ligne de
    la reine (identifiant conservé, affichage atténué) + étiquette
    « (morte) » ; nouveau bloc `tuile-signal-reine-morte` avec icône
    SVG inline (couronne barrée, `currentColor`, aucune ressource
    externe) et texte « Reine morte », `role="img"` +
    `aria-label` explicite pour l'accessibilité.
- `gestion/templates/gestion/fiche_colonie.html` :
  - bloc « Reine » : ligne « Reine morte confirmée le [date de la
    visite] » si le signal est actif.
  - historique des visites : chaque observation affiche désormais
    `{{ observation.libelle_statut_affichage }}` au lieu de
    « (certitude — statut) » ; classe CSS `statut-{{ observation.statut|lower }}`
    ajoutée sur la pastille, en plus de `certitude-...`.
- `gestion/static/gestion/style.css` :
  - `.tuile-reine-morte`, `.etiquette-morte`, `.tuile-signal-reine-morte`,
    `.icone-reine-morte` (couleur fixe lisible en thème clair et sombre) ;
  - `.signal-reine-morte` pour la ligne de la fiche colonie ;
  - `.tag-observation.statut-infirmee` : fond neutre + opacité réduite
    (atténuation visuelle d'une observation infirmée), déclarée après
    les règles `certitude-*` pour l'emporter sur elles à spécificité
    égale.
- `gestion/tests.py` :
  - `AffichageObservationsTests` : observation ouverte affichée avec sa
    certitude, confirmée affichée sans mention de « doute »/« constaté »,
    infirmée affichée atténuée (`statut-infirmee`) sans mention de
    certitude, confirmation (bouton fiche et visite suivante avec
    « couvain ouvert présent ? » = non) fixant la certitude à
    « constaté », infirmation conservant la certitude d'origine.
  - `SignalReineMorteTests` : signal (icône + texte + étiquette
    « morte » + mention sur la fiche) pour une reine morte confirmée ;
    absence de signal pour une observation ouverte ou infirmée ;
    absence après un remérage daté à la même date ou après la visite de
    l'observation ; présence si le remérage est antérieur ; colonie
    sans observation sans erreur sur l'accueil ni la fiche.

Aucun changement de structure de base (pas de nouveau champ, pas de
migration) : le signal est calculé à l'affichage à partir des données
existantes (`ObservationVisite`, `EvenementColonie`).

## Vérification

`python manage.py test selection gestion` : 220 tests, OK (aucun
échec).

## Note

Tentative précédente sur cette même issue : le travail (modèles, vues,
gabarits, CSS, tests) était déjà présent et correct dans le worktree,
mais une erreur d'insertion avait scindé un test existant
(`SupprimerVisiteTests.test_confirmation_supprime_visite_actions_observations_et_rappels`)
en coupant sa dernière assertion pour la recoller à la toute fin du
fichier, à l'intérieur d'un test sans rapport
(`SignalReineMorteTests.test_colonie_sans_observation_sans_erreur`), ce
qui provoquait une erreur (`AttributeError`) à l'exécution. Corrigé en
remettant cette assertion à sa place d'origine.
