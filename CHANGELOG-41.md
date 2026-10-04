# Issue #41 — Écran d'accueil visuel : tuiles de ruches par rucher, couleur de ruche, fiche colonie

## Ajouté

- `Ruche.couleur` (migration `selection/0016_ruche_couleur.py`, purement
  additive, `default=""`) : couleur hexadécimale réelle de la ruche
  telle que peinte, optionnelle. Saisie dans l'admin via le champ texte
  existant, complété par un sélecteur `<input type="color">` ajouté en
  JS (`selection/static/selection/admin/couleur_ruche.js`) — pas branché
  comme widget direct : un `type="color"` natif ne peut pas rester vide
  (il retombe sur `#000000` dès qu'on lit sa valeur), ce qui aurait
  écrasé silencieusement « couleur inconnue » par du noir au moindre
  enregistrement du formulaire sans y toucher.
- Nouvelle application Django `gestion` (ajoutée à `INSTALLED_APPS`) :
  pages visuelles de gestion du rucher, distincte de `selection`. Lit
  uniquement les modèles de gestion (`Rucher`, `TypeRuche`, `Ruche`,
  `Colonie`, `Reine`, `ConfigurationColonie`, `EvenementColonie`,
  importés depuis `selection.models`) par l'ORM Django — aucune vue
  SQL, aucun SQL propre à PostgreSQL, aucune dépendance à un modèle, une
  vue, une table ou un gabarit de sélection (campagnes, mesures,
  cellules royales, critères, calendrier, vues SQL de sélection).
  - `gestion/views.py` : `accueil` (une section par rucher, une tuile
    par ruche active avec sa colonie active éventuelle, requêtes
    `select_related`/`prefetch_related` pour éviter le N+1) et
    `fiche_colonie` (lecture seule).
  - `gestion/urls.py` : `gestion:accueil` (`/`) et
    `gestion:fiche_colonie` (`/colonies/<id>/`).
  - `gestion/couleurs.py` : couleurs fixes de la pastille de marquage
    des reines (BLANC/JAUNE/ROUGE/VERT/BLEU), sur le même principe que
    `selection/couleurs.py` pour les étapes du calendrier — codées en
    dur volontairement (convention apicole fixe).
  - `gestion/templatetags/gestion_extras.py` : filtre `couleur_marquage`.
  - Gabarits `gestion/templates/gestion/accueil.html`,
    `_tuile_ruche.html`, `fiche_colonie.html` ; feuille de style
    `gestion/static/gestion/style.css` (aucune ressource externe,
    grille de tuiles en `auto-fill` responsive, variables CSS + `prefers-
    color-scheme` pour la lisibilité en clair/sombre). Le bandeau
    « BASE DE TEST » est dupliqué localement dans les gabarits de
    `gestion` (à partir de la variable de contexte globale
    `BASE_DE_TEST_ACTIVE`, déjà injectée pour tous les templates par
    `selection.context_processors.base_de_test_active`) plutôt
    qu'inclus depuis un gabarit `selection/`, pour ne garder aucune
    dépendance de `gestion` vers des fichiers de l'app `selection`
    (seule sa variable de contexte globale, déjà partagée par
    construction, est utilisée).
  - `gestion/tests.py` (9 tests) : tuiles avec couleur et reine
    affichées, ruche sans colonie active affichée « vide », ruche
    retirée du service absente de l'accueil, ruche sans couleur ne
    plante pas, compteurs colonies actives/ruchers, fiche colonie
    affichée avec lien de modification admin, 404 sur colonie
    inexistante.

## Modifié

- `apiselect/urls.py` : la racine `/` affiche désormais l'accueil de
  `gestion` (`include('gestion.urls')`) au lieu de rediriger vers
  `/admin/`. Les routes `/admin/` et `/selection/` restent inchangées.
- `selection/admin.py` : `RucheAdmin` affiche `couleur` dans la liste et
  charge le script du sélecteur de couleur complémentaire.

## Décisions / points d'attention

- Ruchers et ruches : seules les ruches actives (`Ruche.actif=True`,
  boîtes en service) apparaissent sur l'accueil — une boîte retirée du
  service ne reflète plus l'état courant du rucher. Ce filtre n'était
  pas explicitement demandé dans l'issue ; à ajuster si Alain veut
  aussi voir les boîtes retirées.
- Libellé de tuile : « alias + numéro, sans "n°" » repris directement
  de `Ruche.__str__` (déjà sans « n° », cf. modèle existant).
- Migration appliquée uniquement sur `apiselect_dev` (pour vérification
  manuelle de bout en bout, cf. rapport de clôture) — jamais sur
  `apiselect`, comme demandé. Jeu de données fictif peuplé puis purgé
  sur `apiselect_dev` pendant la vérification, aucune donnée réelle
  touchée.
- Tests lancés via `python manage.py test selection gestion` (la
  commande imposée par `CONTEXTE.md`, `test selection`, ne couvre pas
  la nouvelle app ; l'étendre à `gestion` reste sans risque, la
  commande `test` crée toujours sa propre base de test isolée, jamais
  la base réelle).
