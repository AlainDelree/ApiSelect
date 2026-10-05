# Issue #54 — Modifier une reine et liste des reines depuis l'interface visuelle (un seul formulaire)

## Ajouté

- `gestion/forms.py` : `ReineForm`, formulaire unique pour tous les
  champs propres à une reine (identifiant, mère, statut, mode
  d'acquisition, vendeur — avec création directe d'un nouveau vendeur,
  date de naissance, date de fécondation, station de fécondation,
  marquage effectué, date de marquage, couleur de marquage — proposée
  selon l'année de naissance, issue #53 —, lignée mâle probable, date
  de décès, notes). Règles conservées : couleur obligatoire quand le
  marquage est effectué, couleur déjà enregistrée jamais effacée
  silencieusement, identifiant unique (message clair en cas de
  doublon). `NouvelleReineForm` (remplacement, issue #51) hérite
  désormais de `ReineForm` au lieu de dupliquer ces champs : seuls la
  date de remplacement et le choix d'origine (reine déjà enregistrée /
  nouvelle) lui restent propres.
- `gestion/views.py` : `modifier_reine` (modification, pré-remplie,
  retour vers la fiche colonie ou la page « Reines » selon le
  paramètre `retour`), `ajouter_reine` (création d'une reine sans
  colonie) et `liste_reines` (page « Reines », toutes les reines y
  compris celles sans colonie active : identifiant, colonie actuelle
  ou « sans colonie », origine, vendeur, pastille de marquage, date de
  naissance).
- `gestion/urls.py` : `reines/`, `reines/ajouter/`,
  `reines/<id>/modifier/`.
- `gestion/templates/gestion/_champs_reine.html` : partiel commun aux
  trois formulaires (création, modification, remplacement) pour les
  champs de la reine — garantit qu'aucun champ ne diffère entre eux.
- `gestion/templates/gestion/reine_form.html` et
  `gestion/templates/gestion/liste_reines.html`.
- `gestion/static/gestion/reine_champs.js` : comportements communs
  (affichage du bloc vendeur selon le mode d'acquisition, du bloc date
  et couleur de marquage selon « marquage effectué », proposition de
  couleur selon l'année de naissance) factorisés depuis
  `nouvelle_reine.js` et partagés avec `reine_form.js`
  (création/modification).
- Bouton « Modifier la reine » dans le bloc « Reine » de la fiche
  colonie (`fiche_colonie.html`), à côté de « Marquer la reine ».
- Lien « Reines → » dans l'en-tête de l'accueil, à côté du compteur
  « reines non marquées ».
- Tests (`gestion/tests.py`, `ModifierReineTests`) : modification
  depuis la fiche colonie (couleur, date de naissance, mère),
  formulaire pré-rempli, doublon d'identifiant refusé avec message
  clair, couleur obligatoire si marquage effectué, couleur déjà
  enregistrée non effacée silencieusement, création d'une reine sans
  colonie depuis la page « Reines », la page « Reines » liste aussi
  les reines sans colonie, mêmes champs exposés par les formulaires de
  création/modification/remplacement, lien depuis l'accueil.

## Non modifié

- Administration Django des reines (`selection/admin.py`,
  `ReineAdmin`) : inchangée, comme demandé dans l'issue.
- Aucune migration (tous les champs existaient déjà).

## Avis sur la désactivation de l'ajout dans l'admin pour `Reine`

Envisageable sans risque pour une issue ultérieure :
`CelluleRoyaleAdmin.confirmer_eclosion` (`selection/admin.py`) crée la
reine par un appel direct `Reine.objects.create(...)` dans le code de
l'action, pas via la vue d'ajout de `ReineAdmin` — `has_add_permission`
ne s'applique qu'au bouton/formulaire « Ajouter » de l'admin et ne
conditionne pas les créations faites par le code. Désactiver l'ajout
sur `ReineAdmin` (comme déjà fait pour d'autres modèles, ex.
`EtapeCalendrierInline`) n'affecterait donc pas cette action.
