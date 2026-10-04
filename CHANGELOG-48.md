# Issue #48 — Visites : un seul formulaire pour créer et modifier, administration sans ajout de visite

## Ajouté

- `gestion/views.py` : vues `modifier_visite` et `supprimer_visite` ;
  `nouvelle_visite` et `modifier_visite` délèguent désormais toutes
  les deux à `_traiter_formulaire_visite`, qui réutilise le même
  `VisiteForm` et le même gabarit pour créer ou modifier une visite
  (mêmes champs, même comportement de la date de revérification).
  `_synchroniser_observation` remplace `_enregistrer_observation` :
  crée une observation absente (ouverte), met à jour une observation
  déjà présente sans toucher à son statut, supprime une observation
  retirée (son rappel éventuel suit par la cascade du modèle).
- `gestion/forms.py` : `initial_observations_depuis_visite(visite)`
  calcule les valeurs initiales des champs d'observation/action/
  revérification du formulaire à boutons à partir d'une visite
  existante, pour le pré-remplir en modification.
- `gestion/urls.py` : routes
  `colonies/<id>/visites/<id>/modifier/` (`gestion:modifier_visite`)
  et `colonies/<id>/visites/<id>/supprimer/` (`gestion:supprimer_visite`).
- `gestion/templates/gestion/confirmer_suppression_visite.html` :
  page de confirmation explicite listant ce qui sera supprimé (la
  visite, ses actions, ses observations, leurs rappels).
- `gestion/templates/gestion/visite_form.html` (ex
  `nouvelle_visite.html`) : titre, bouton d'enregistrement et bouton
  « Supprimer cette visite » adaptés selon création/modification.
- `gestion/templates/gestion/fiche_colonie.html` : lien « Modifier »
  sur chaque visite de l'historique.
- `gestion/static/gestion/style.css` : styles `.lien-modifier-visite`,
  `.bouton-supprimer`, `.bouton-supprimer-confirmer`, `.bouton-annuler`.
- `gestion/admin.py` : `has_add_permission` renvoyant `False` sur
  `VisiteAdmin`, `ObservationVisiteAdmin`, `RappelRevisiteAdmin`,
  `ActionVisiteInline`, `ObservationVisiteInline` — plus de bouton ni
  de lien « Ajouter », adresse d'ajout refusée (403) ; consultation,
  correction et suppression restent possibles à titre exceptionnel.
- `CONTEXTE.md` : principe de saisie ajouté dans la partie gestion
  (un seul formulaire par type de donnée, administration réservée aux
  référentiels et aux corrections exceptionnelles) ; quelques
  passages condensés ailleurs pour rester sous 4000 caractères.
- `gestion/tests.py` : classes `ModifierVisiteTests` (formulaire
  pré-rempli, mêmes champs qu'à la création, observation inchangée/
  ajoutée/retirée, date de revérification modifiée sans doublon,
  actions remplacées, lien « Modifier » dans l'historique) et
  `SupprimerVisiteTests` (page de confirmation, rien supprimé sans
  validation, suppression en cascade). `AdminVisiteTests` réécrite :
  ajout de visite/observation/rappel refusé (403) dans l'admin,
  aucun lien « Ajouter » sur l'accueil admin, consultation et
  correction du rappel toujours possibles.

## Choix pour les cas ambigus

- Observation déjà confirmée ou infirmée dont le type ou la certitude
  change à la modification : le statut n'est **pas** réinitialisé à
  « ouverte ». Comportement le plus simple — à charge d'Alain de
  confirmer/infirmer à nouveau depuis la fiche colonie si besoin.
- Actions d'une visite modifiée : remplacées intégralement (suppression
  puis recréation) plutôt que fusionnées, les actions n'ayant pas
  d'identité ni de statut propre à préserver.
- Question « couvain ouvert présent ? » (confirmation d'une
  observation « reine morte » ouverte depuis une *autre* visite) :
  posée uniquement à la création, pas à la modification — absente de
  la liste des champs à pré-remplir donnée par l'issue, et ambiguë si
  l'observation concernée est celle de la visite en cours d'édition.
- Date de revérification par défaut en modification, quand il
  n'existe pas encore de rappel : visite + 9 jours (comme à la
  création, mais basé sur la date de la visite plutôt que sur
  aujourd'hui, la date de la visite étant déjà connue).

Aucune migration nécessaire (`makemigrations --check` : aucun
changement détecté). Suite `python manage.py test selection gestion` :
200 tests, OK.
