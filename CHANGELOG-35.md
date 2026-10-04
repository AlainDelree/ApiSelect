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
