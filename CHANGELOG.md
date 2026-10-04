# Issue #33 — Correction tests DiagnosticsTests cassés par Mesure.campagne obligatoire

# Issue #38 — Tableau de résultats de sélection sur la page d'accueil de l'admin

## Ajouté

- `selection/templates/selection/_tableau_resultats.html` : gabarit
  partiel du tableau de résultats (sélecteur de campagne + tableau
  compact, lignes colorées retenue/sans mesure/exclue, 9 colonnes de
  critères avec en-tête abrégé sur 3 lettres et nom complet en
  infobulle `title`, défilement horizontal interne si le tableau
  dépasse son cadre). Inclus à la fois par `selection/resultats.html`
  et par la nouvelle page d'accueil de l'admin, pour ne pas dupliquer
  le rendu.
- `templates/admin/index.html` : surcharge de `admin/index.html`
  (motif `{% extends "admin/index.html" %}` déjà utilisé par
  `templates/admin/base.html` pour le même site) ajoutant un bloc
  `#tableau-resultats-admin` dans l'espace libre à droite des modules
  de l'admin (« Actions récentes » notamment). Mise en page en
  flexbox scoped à `.dashboard #content-start` : le cadre `#content`
  historique (600px) n'est pas élargi, le nouveau bloc devient un
  second item flexible qui se place à côté sur écran large et passe
  dessous (`flex-wrap`) sur écran étroit.

## Modifié

- `selection/views.py` : extraction de `_contexte_resultats(request)`
  (calcul partagé par `resultats_selection` et par la nouvelle
  `admin_index_avec_tableau`), sans changement de comportement pour
  `selection:resultats`. Nouvelle fonction `admin_index_avec_tableau`
  qui enrichit `admin.site.index()` du même contexte.
- `apiselect/urls.py` : ajout de
  `path('admin/', admin.site.admin_view(admin_index_avec_tableau))`
  juste avant `path('admin/', admin.site.urls)` — n'intercepte que
  l'URL exacte `/admin/` (page d'accueil), toutes les autres URL
  `/admin/...` retombent sur `admin.site.urls`, inchangé. Permission
  identique à l'index standard (`admin.site.admin_view`, même
  décorateurs `never_cache`/`csrf_protect`) sans sous-classer
  `AdminSite` ni réenregistrer les modèles déjà inscrits sur le site
  par défaut.
- `selection/templates/selection/resultats.html` : remplace le
  contenu dupliqué (formulaire + tableau) par
  `{% include "selection/_tableau_resultats.html" %}` ; conserve le
  bandeau de base de test, le lien de retour et les liens vers les
  fiches PDF. Page toujours fonctionnelle à `selection/resultats/`,
  sans redirection.
- `templates/admin/base.html` : le lien « Tableau de résultats de
  sélection » de la barre de liens pointe désormais vers
  `admin:index` (la page d'accueil, qui affiche le tableau) au lieu
  de `selection:resultats`.
- `selection/tests.py`, classe `LiensSelectionToutesPagesAdminTests` :
  les deux tests vérifiant la présence du lien « Tableau de résultats
  de sélection » sont adaptés à sa nouvelle cible (`admin:index`),
  en vérifiant le balisage exact de l'ancre plutôt qu'un simple
  sous-texte d'URL (évite un faux positif avec les autres occurrences
  de `/admin/` sur la page, ex. fil d'Ariane).

## Tests

- `selection/tests.py`, nouvelle classe
  `ResultatsSelectionSurPageAccueilAdminTests` : la page d'accueil de
  l'admin affiche le tableau (colonie, index, statut) pour la
  campagne la plus récente par défaut, et respecte `?campagne=` pour
  en afficher une autre.
- Suite complète : `python manage.py test selection` → 139 tests, OK.

## Vérification manuelle

- Serveur de dev lancé localement avec `DJANGO_DB_NAME=apiselect_dev`
  (jamais sur `apiselect`), sur un port dédié, dans ce worktree
  uniquement : `GET /admin/` affiche le tableau (bandeau « BASE DE
  TEST » intact, sélecteur de campagne, 3 occurrences du bloc), `GET
  /selection/resultats/` toujours fonctionnel et inchangé dans son
  contenu, `?campagne=<id inexistant>` renvoie 404 comme avant.
  Serveur arrêté après vérification, aucune donnée modifiée.

## Points d'attention

- Le bloc `#tableau-resultats-admin` est ajouté via le bloc
  `{% block footer %}` de `admin/index.html` (seul point d'extension
  disponible après `#content` dans `admin/base.html`) ; la mise en
  page flexbox qui le place à droite est scoped à `.dashboard
  #content-start` et ne touche pas les autres pages de l'admin.

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

# Issue #35 — Suppression de l'obligation de login en usage local

## Ajouté

- `selection/middleware.py` : `ConnexionAutomatiqueLocaleMiddleware`.
  Quand une requête n'est pas authentifiée ET provient de 127.0.0.1 /
  ::1, connecte automatiquement :
  - le premier superutilisateur actif de la base ciblée, s'il en
    existe un ;
  - sinon un nouvel utilisateur `local` (superutilisateur, staff,
    actif), créé avec `set_unusable_password()` — aucune connexion par
    mot de passe possible avec ce compte.
  Toute requête dont `REMOTE_ADDR` n'est pas une adresse locale garde
  le comportement Django normal (redirection vers `/admin/login/`).
  Aucun utilisateur existant n'est modifié, supprimé ni réinitialisé.

- `selection/tests.py`, classe `ConnexionAutomatiqueLocaleMiddlewareTests`
  (5 tests) :
  - accès à `/admin/` sans login depuis l'adresse locale ;
  - `/admin/login/` redirige vers `/admin/` (plus de formulaire) en
    local ;
  - création de l'utilisateur `local` seulement s'il n'existe aucun
    superutilisateur ;
  - réutilisation d'un superutilisateur existant sans en créer un
    autre (mot de passe existant inchangé) ;
  - requête non locale (`REMOTE_ADDR` différent) renvoyée vers le
    login avec `?next=`.

## Modifié

- `apiselect/settings.py` : ajout de
  `selection.middleware.ConnexionAutomatiqueLocaleMiddleware` dans
  `MIDDLEWARE`, juste après `AuthenticationMiddleware` (dépend de
  `request.user` déjà résolu). Aucune autre entrée modifiée. Comportement
  identique sur `apiselect` et `apiselect_dev` (le middleware ne
  dépend pas du nom de la base).

## Non touché (volontairement)

- Aucune migration, aucun changement de modèle.
- Aucune donnée existante lue/modifiée/supprimée sur `apiselect` ni
  `apiselect_dev` (tests lancés uniquement sur la base temporaire
  `test_apiselect`).
- Les 3 tests `DiagnosticsTests` mentionnés dans l'issue comme
  potentiellement en échec sont en réalité déjà corrigés (commit
  9744438, issue #33) — rien à faire ici, hors périmètre de toute
  façon.

## Vérification

`python manage.py test selection` : 136 tests, OK (aucun échec).

# Issue #34 — Mise à jour de CONTEXTE.md (état actuel + règle de protection des données)

## Modifié

- `CONTEXTE.md` réécrit en place (lecture du code : modèles, admin,
  vues, commandes de gestion, migrations) pour refléter l'état réel du
  projet, condensé sous 4000 caractères (3994) :
  - nouvelle section « Règles de travail » en tête, avec la règle de
    protection des données `apiselect`/`apiselect_dev` (interdiction de
    `flush`/`dropdb`/`loaddata`/DELETE-TRUNCATE/`purgetest` et des
    commandes `purger_donnees_test`/`reinitialiser_donnees_test`/
    `peupler_donnees_test` sans accord explicite d'Alain), l'interdiction
    de `migrate` sur la vraie base, la règle des tests
    (`python manage.py test selection` uniquement) et l'absence de
    `git push` ;
  - ajout de `CelluleRoyale`, des lots de critères (`LotCriteres`,
    indépendants des campagnes), du calendrier à 4 étapes + étape
    facultative « Élevage des mâles », de `Mesure.campagne` obligatoire,
    des nouveaux modes d'acquisition des reines et du mode diagnostic ;
  - ajout de l'état des migrations (0010 à 0015 appliquées sur
    `apiselect_dev`, en attente sur la vraie base `apiselect`) ;
  - vocabulaire, documents de référence et calendrier condensés plutôt
    que supprimés ; mention de `Cours_Apiculture/` (jamais committé ni
    référencé dans une issue) conservée.

Aucun autre fichier touché.

## Corrigé

- `selection/tests.py`, classe `DiagnosticsTests` : les 3 tests
  `test_score_hors_intervalle_declenche_avertissement`,
  `test_score_dans_lintervalle_ne_declenche_rien`,
  `test_score_absent_ne_declenche_rien` créaient une `Mesure` sans
  `campagne`, devenue obligatoire par l'issue #31. Ajout d'un
  `LotCriteres` et d'une `CampagneElevage` dédiés par test (pattern de
  `MesureCampagneObligatoireTests`), assignés au champ `campagne` de
  chaque `Mesure`.
- Recherche systématique de tous les `Mesure.objects.create`/`Mesure(`
  du fichier : aucun autre cas sans `campagne` trouvé.

## Vérification

`python manage.py test selection` : 131 tests, OK (aucun échec).

