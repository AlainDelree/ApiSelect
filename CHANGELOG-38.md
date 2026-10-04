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
