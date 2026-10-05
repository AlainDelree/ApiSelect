# Issue #51 — Remplacement de reine : nouvelle reine d'une colonie (origine, vendeur, marquage)

## Ajouté

- `selection/models.py`, `ModeAcquisitionReine` : nouvelle valeur
  `DONNEE` (« Donnée »). Les quatre autres origines demandées par
  l'issue existaient déjà sous d'autres noms (introduites par
  l'issue #25/#29) et sont réutilisées sans renommage ni modification
  des données existantes : « élevée par la colonie elle-même » =
  `REMERAGE_NATUREL` (remérage naturel), « élevage personnel » =
  `ELEVEE` (élevée sur le rucher), « achetée » = `ACHETEE_CR` /
  `ACHETEE_VIERGE` / `ACHETEE_FECONDEE` (selon le stade), « issue d'un
  essaim capturé » = `ARRIVEE_ESSAIM`. Nouveau tuple
  `MODES_ACQUISITION_ACHAT` (les trois valeurs d'achat) : sert à savoir
  quand proposer le champ vendeur.
- `gestion/models.py` : nouveau modèle `Vendeur` (nom obligatoire,
  téléphone et adresse facultatifs) — défini dans `gestion`, pas dans
  `selection`, pour que ce soit `Reine` (dans `selection`) qui le
  référence par clé étrangère et jamais l'inverse ; aucune dépendance
  circulaire entre les migrations des deux applications, et `gestion`
  ne dépend toujours pas de `selection` au-delà de l'exception déjà
  documentée (`Colonie`). Migration `gestion/migrations/0002_vendeur.py`.
- `selection/models.py`, `Reine` : nouveaux champs `vendeur` (FK
  facultative vers `gestion.Vendeur`), `marquage_effectue` (booléen,
  défaut `False`) et `date_marquage` (date facultative). `couleur_marquage`
  reste déterminée par l'année de naissance, saisie à part, inchangée.
  `EvenementColonie` : nouveau champ `ancienne_reine` (FK facultative
  vers `Reine`, `on_delete=SET_NULL`), pour conserver la trace de la
  reine remplacée lors d'un remérage sans la modifier ni la supprimer.
  Migration `selection/migrations/0019_evenementcolonie_ancienne_reine_reine_date_marquage_and_more.py` :
  purement additive (AddField/AlterField sur les choix de
  `mode_acquisition`), aucune donnée existante modifiée — les reines
  déjà en base reçoivent `marquage_effectue=False` par défaut, à
  corriger manuellement (admin ou bouton « Marquer la reine »).
- `gestion/forms.py` :
  - `NouvelleReineForm` : formulaire à grands boutons du remplacement
    de reine (date, origine — reine déjà enregistrée et non affectée à
    une colonie active, ou nouvelle reine —, pour une nouvelle reine :
    identifiant, mère, mode d'acquisition, vendeur déjà enregistré ou
    nouveau vendeur créé directement dans ce même formulaire, statut,
    date de fécondation, marquage effectué + date). Validation :
    identifiant obligatoire et non dupliqué pour une nouvelle reine,
    reine existante obligatoire pour l'autre origine, vendeur
    (existant ou nouveau) exigé quand le mode d'acquisition est un
    achat.
  - `MarquerReineForm` : date de marquage (proposée aujourd'hui,
    modifiable).
- `gestion/views.py` :
  - `nouvelle_reine(request, colonie_id)` : à l'enregistrement, crée
    (ou réutilise) le vendeur si besoin, crée la nouvelle reine ou
    reprend la reine existante choisie, détache l'ancienne reine
    (`Colonie.reine_actuelle` réassignée, l'ancienne reine n'est ni
    supprimée ni modifiée) et crée un `EvenementColonie` de type
    `REMERAGE` à la date choisie avec `reine` (nouvelle) et
    `ancienne_reine` (détachée). Ce remérage fait disparaître le signal
    « reine morte » de l'issue #50 (logique déjà en place, inchangée :
    `_observation_reine_morte_confirmee_sans_remplacement`).
  - `suggestion_identifiant_reine(request)` : petit point d'entrée JSON
    réutilisant `selection.calculs.suggerer_identifiant_fille` quand une
    mère est choisie (amélioration progressive, aucune fonctionnalité
    perdue sans JavaScript).
  - `marquer_reine(request, reine_id)` : page de confirmation du
    marquage, atteinte depuis la fiche colonie ou la liste « Reines à
    marquer » (paramètre `retour`).
  - `reines_a_marquer(request)` : liste des reines non marquées des
    colonies actives.
  - `accueil` : nouveau `nb_reines_non_marquees` dans le contexte.
- `gestion/urls.py` : routes `nouvelle-reine`, `reines-a-marquer`,
  `reines/<id>/marquer`, `suggestion-identifiant`.
- `gestion/templates/gestion/nouvelle_reine_form.html`,
  `marquer_reine_form.html`, `reines_a_marquer.html` : nouveaux
  gabarits, même style à grands boutons que le formulaire de visite.
- `gestion/static/gestion/nouvelle_reine.js` : amélioration progressive
  (affichage conditionnel reine existante/nouvelle, bloc vendeur,
  champ date de marquage, suggestion d'identifiant depuis la mère) —
  tous les champs restent visibles et fonctionnels sans JavaScript.
- `gestion/templates/gestion/fiche_colonie.html` : bouton « + Nouvelle
  reine » ; bloc « Reine » complété avec « Marquée le [date] » / « Non
  marquée », le vendeur (si renseigné) et un bouton « Marquer la
  reine » quand la reine actuelle n'est pas encore marquée.
- `gestion/templates/gestion/_tuile_ruche.html` : pastille de marquage
  pleine (reine marquée) ou vide en contour (reine non marquée, avec
  `aria-label="Non marquée"`).
- `gestion/templates/gestion/accueil.html` : compteur « N reines non
  marquées » dans l'en-tête, lien vers la page « Reines à marquer ».
- `gestion/static/gestion/style.css` : `.pastille-marquage-vide`,
  `.bouton-nouvelle-reine`, `.bouton-marquer-reine`,
  `.compteur-a-marquer`, `.liste-reines-a-marquer`, styles de champs
  texte/liste déroulante dans les formulaires à grands boutons.
- `gestion/admin.py` : `VendeurAdmin` (consultation/corrections
  exceptionnelles — la saisie normale se fait depuis le formulaire de
  remplacement).
- `selection/admin.py`, `ReineAdmin` : colonnes/filtres `vendeur`,
  `marquage_effectue`, `date_marquage` ; `marquage_effectue` et
  `date_marquage` éditables en liste (pour qu'Alain coche les reines
  déjà marquées existantes sans passer par chaque fiche).
- Tests : `gestion/tests.py` (`NouvelleReineFormulaireTests`,
  `MarquageReineTests`) et `selection/tests.py`
  (`VendeurReineTests`, `MarquageEffectueTests`,
  `EvenementColonieAncienneReineTests`, et un cas `DONNEE` ajouté à
  `NouveauxModesAcquisitionReineTests`) : remplacement avec nouvelle
  reine achetée + nouveau vendeur, vendeur déjà enregistré réutilisé
  sans doublon, reine existante non affectée, mode sans vendeur,
  achat sans vendeur refusé, reine déjà affectée à une colonie active
  exclue de la liste, disparition du signal « reine morte » après
  remplacement, vendeur affiché sur la fiche colonie, pastille pleine
  ou vide selon le marquage, bouton « Marquer la reine », compteur et
  page « Reines à marquer » limités aux colonies actives non marquées,
  valeur par défaut du marquage sur une reine sans incidence sur ses
  autres champs. `python manage.py test selection gestion` : 241
  tests, tous au vert.

## Note d'incident (corrigée)

Une commande `manage.py shell` lancée par erreur pendant le
diagnostic d'un test (hors du runner de tests) s'est connectée à la
vraie base `apiselect` (nom de base par défaut en l'absence de
`.env`, authentification locale sans mot de passe) et y a créé un
rucher de test ("Rucher Debug"). Repéré immédiatement : seule cette
ligne avait été insérée (la requête suivante a échoué avant toute
autre écriture) ; supprimée aussitôt par une suppression ciblée sur
son identifiant exact. Base vérifiée après coup : seuls les ruchers
réels (Bovesse, Anhée) restent. Par précaution, tout diagnostic
ultérieur dans ce traitement est passé exclusivement par
`manage.py test` (base de test isolée, détruite en fin de run).
