# Issue #43 — Saisie d'une visite depuis la fiche colonie (observations avec doute et rappels)

## Ajouté

- Nouvelle application de modèles `gestion/models.py` (migration
  purement additive `gestion/migrations/0001_initial.py`, dépendant de
  `selection.Colonie` par clé étrangère — même exception déjà en place
  dans `gestion/views.py` à la règle de dépendance à sens unique, en
  attendant que `Colonie` soit déplacée dans `gestion`) :
  - `Visite` : colonie, date (par défaut aujourd'hui), observation de
    la reine (vue/œufs vus/rien vu), cadres de couvain, cadres
    d'abeilles, réserves (faibles/correctes/bonnes), comportement
    (1 calme à 4 agressive), notes. Tout facultatif sauf colonie et
    date.
  - `ActionVisite` (plusieurs par visite) : hausse ajoutée/retirée,
    nourrissement, traitement, suppression des CR.
  - `ObservationVisite` (plusieurs par visite, dénormalise `colonie`
    pour lister directement les observations ouvertes d'une colonie) :
    essaimage/reine morte/pillage/frelons, certitude
    (constaté/doute), statut (ouverte/confirmée/infirmée — reste
    « ouverte » tant qu'elle n'est pas confirmée/infirmée), réponse
    "cellules royales" (pour l'essaimage uniquement).
  - `RappelRevisite` (OneToOne sur une observation) : créé
    automatiquement pour une « reine morte » en doute, à la date de
    visite + 9 jours par défaut (modifiable à la saisie,
    `date_revisite_par_defaut`), marqué `traite` à la confirmation ou
    l'infirmation.
  - Aucun SQL propre à PostgreSQL, uniquement des types de champs
    standard de l'ORM (portabilité SQLite, cf. `CONTEXTE.md`).
- `gestion/forms.py` : `VisiteForm` (ModelForm + champs supplémentaires
  pour les actions/observations, tous en `RadioSelect`/
  `CheckboxSelectMultiple` pour un rendu en gros boutons à toucher),
  `RevisiteReineMorteForm` (question « couvain ouvert présent ? »
  posée à la visite suivante quand une observation « reine morte » est
  ouverte : oui → infirmée, non → confirmée).
- `gestion/views.py` :
  - `nouvelle_visite` (`/gestion/colonies/<id>/nouvelle-visite/`) :
    formulaire de saisie, enregistre la visite, ses actions et ses
    observations (avec création du rappel à 9 jours si « reine morte »
    en doute), pose et traite la question de revérification si une
    observation « reine morte » est déjà ouverte pour la colonie, puis
    redirige vers la fiche colonie.
  - `confirmer_observation` / `infirmer_observation`
    (`/gestion/observations/<id>/confirmer|infirmer/`) : confirmation
    ou infirmation manuelle depuis la fiche colonie, pour toute
    observation ouverte (clôture aussi le rappel associé s'il existe).
  - `fiche_colonie` : ajout de l'historique des visites (plus récente
    en premier, avec reine/cadres/réserves/comportement/actions/
    observations/notes) et d'un bloc « Observations ouvertes » avec
    boutons confirmer/infirmer et date de revérification.
  - `accueil` : ajout par tuile de la dernière visite (« il y a N
    jours » / « aucune visite ») et d'une pastille par observation
    ouverte (« Reine morte ? », « Essaimage ? », « Pillage »,
    « Frelons », teinte différente constaté/doute), et d'un bloc
    « À revérifier » listant les rappels non traités (mise en
    évidence de ceux dont l'échéance est atteinte ou dépassée). Le
    calcul d'un seuil « à visiter » n'est pas traité ici (hors
    périmètre de cette issue).
- Gabarit `gestion/templates/gestion/nouvelle_visite.html` : formulaire
  à grands boutons à toucher, couleur et numéro de la ruche rappelés en
  tête, aucune ressource externe, lisible sur tablette/téléphone.
  `fiche_colonie.html` et `accueil.html`/`_tuile_ruche.html` mis à
  jour en conséquence.
- `gestion/static/gestion/style.css` : styles pour les groupes de gros
  boutons (`.groupe-choix`, mise en évidence du choix sélectionné via
  `label:has(input:checked)`, sans JavaScript), tags d'actions et
  d'observations sur l'historique des visites, pastilles
  d'observations ouvertes sur les tuiles, bloc « À revérifier ».
- `gestion/admin.py` : `VisiteAdmin` (inlines actions/observations),
  `ObservationVisiteAdmin` (statut modifiable en liste),
  `RappelRevisiteAdmin` (traité modifiable en liste).
- `gestion/tests.py` : visite complète, visite minimale (date seule),
  observation en doute/constatée restant ouverte, création du rappel à
  9 jours (et son absence pour une reine morte constatée), réponse
  « cellules royales » enregistrée pour l'essaimage, confirmation et
  infirmation depuis la fiche colonie, confirmation/infirmation d'une
  « reine morte » ouverte à la visite suivante selon la présence de
  couvain ouvert, affichage de la dernière visite/des pastilles/du
  bloc « à revérifier » sur l'accueil, ruche sans visite sans erreur.
  Tests existants inchangés et toujours au vert
  (`python manage.py test selection gestion` : 165 tests, OK).
- `CONTEXTE.md` : commande de tests corrigée
  (`python manage.py test selection gestion`, l'ancienne ne couvrait
  pas `gestion`), ajout de la règle « vérification manuelle ne remplit
  ni ne purge jamais la base de test », état des migrations corrigé
  (0010-0014 déjà appliquées sur `apiselect`, seules 0015/0016 et
  celles de `gestion` restent en attente). D'autres passages condensés
  pour rester sous 4000 caractères.

## Recoupement avec `EvenementColonie` (non modifié dans cette issue)

`EvenementColonie` (type `MORTALITE`, entre autres) reste la trace
officielle d'un changement d'état durable de la colonie, saisie à la
main dans l'admin ; `ObservationVisite` (type `REINE_MORTE`) est une
observation de terrain, datée d'une visite, qui peut rester en doute
puis être confirmée ou infirmée. Les deux ne sont pas fusionnées ici :
une observation « reine morte » confirmée ne crée pas automatiquement
un `EvenementColonie` de type `MORTALITE`, et les deux listes
s'affichent séparément sur la fiche colonie. Proposition pour une
issue suivante : à la confirmation d'une observation « reine morte »,
proposer (sans l'imposer) la création automatique de l'`EvenementColonie`
correspondant, pour éviter la double saisie — attention toutefois à ne
pas en faire une création systématique si Alain saisit parfois la
mortalité directement dans l'admin sans passer par une visite.
