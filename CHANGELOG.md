# Issue #33 — Correction tests DiagnosticsTests cassés par Mesure.campagne obligatoire

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

# Issue #49 — Silhouette des ruches : hauteur réduite par des bandes blanches en haut et en bas (petites boîtes)

## Ajouté

- `selection/models.py` : champ facultatif `TypeRuche.hauteur_relative_pourcent`
  (entier, 10 à 100, `null=True, blank=True`), pour les types de boîte
  visuellement plus petits (ex. Apidea). Vide ou 100 : comportement
  actuel inchangé (hauteur complète).
- `selection/migrations/0018_typeruche_hauteur_relative_pourcent.py` :
  migration purement additive, aucune valeur existante remplie —
  Alain complète lui-même les types concernés depuis l'admin.
- `selection/admin.py` : `hauteur_relative_pourcent` ajouté à
  `TypeRucheAdmin.list_display` et `list_editable`, comme
  `nombre_cadres`.

## Modifié

- `gestion/affichage.py` (`bande_ruche`) : calcule désormais aussi
  `hauteur_pourcent` et `marge_verticale_pourcent` à partir de
  `TypeRuche.hauteur_relative_pourcent`, avec la même arithmétique
  entière que pour la largeur (zone colorée centrée verticalement,
  deux bandes blanches hautes/basses égales). Le libellé accessible
  reste inchangé (type, nombre de cadres, couleur — rien sur la
  hauteur).
- `gestion/templates/gestion/_tuile_ruche.html` et
  `gestion/templates/gestion/fiche_colonie.html` : la bande colorée
  reçoit en plus `top`/`bottom` en pourcentage (`bande.marge_verticale_pourcent`),
  en complément de `left`/`width` existants.
- `gestion/static/gestion/style.css` : `.tuile-bande-couleur` ne fixe
  plus `top: 0; bottom: 0;` en dur (valeurs désormais toujours fournies
  en ligne par le gabarit) — le cadre de la bande (`.tuile-bande`,
  hauteur 34px, bordure) ne change pas, seule la zone colorée rétrécit.
- `gestion/tests.py` : nouvelle classe `BandeRucheHauteurTests` —
  hauteur vide ou 100 (bande inchangée), hauteur 50 (zone colorée
  centrée avec deux marges de 25 %), combinaison largeur 50 %
  (5 cadres) + hauteur 50 %, même rendu sur la tuile accueil et la
  fiche colonie, ruche sans colonie active toujours marquée « Vide ».

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

# Issue #47 — Tuiles de ruches : silhouette proportionnelle au nombre de cadres, gris par défaut

## Ajouté

- `selection/models.py` : champ facultatif `TypeRuche.nombre_cadres`
  (entier, migration `0017_typeruche_nombre_cadres.py` purement
  additive, aucune valeur existante remplie — à compléter dans l'admin).
  Visible/modifiable dans `selection/admin.py` (`TypeRucheAdmin`).
- `gestion/affichage.py` : fonction `bande_ruche(ruche)` — couleur de
  la ruche (gris moyen fixe `#9e9e9e` par défaut si vide), largeur
  colorée proportionnelle au nombre de cadres du type (centrée entre
  deux bandes blanches égales ; pleine largeur si inconnu ou ≥ 10), et
  libellé accessible (ex. « Ruchette 6 cadres, couleur bleue »).
  Exposée aux templates via le filtre `bande_ruche` dans
  `gestion/templatetags/gestion_extras.py`.

## Modifié

- `gestion/templates/gestion/_tuile_ruche.html` : la bande de la tuile
  d'accueil utilise désormais `bande_ruche` (largeur/marge en %,
  `role="img"` + `aria-label`) au lieu d'une bande pleine largeur fixe.
- `gestion/templates/gestion/fiche_colonie.html` : la bande (même
  couleur, même proportion) est reprise en tête de la fiche, à la
  place de l'ancien aperçu de couleur (pastille ronde) dans le bloc
  « Ruche ».
- `gestion/static/gestion/style.css` : `.tuile-bande` devient un
  conteneur blanc fixe de 34 px de haut avec cadre fin (visible en
  thème clair et sombre), `.tuile-bande-couleur` dessine la portion
  colorée positionnée/dimensionnée en %, `.fiche-bande` ajoute le cadre
  sur la fiche colonie (pas de bordure héritée d'une tuile parente).
- `gestion/tests.py` : nouvelle classe `BandeRucheTests` (10 cadres →
  pleine largeur, ruchette 6 cadres → proportion 60 % centrée entre
  deux bandes de 20 %, nombre de cadres inconnu → pleine largeur,
  couleur absente/vidée → gris par défaut, libellé accessible, rendu
  identique sur la tuile d'accueil et la fiche colonie, ruche sans
  colonie active toujours marquée « vide »).

Aucune dépendance ajoutée à `selection` au-delà de l'exception déjà en
place (lecture de `Ruche`/`TypeRuche`/`Colonie`, cf. CONTEXTE.md).
Aucun SQL spécifique à PostgreSQL. `python manage.py test selection
gestion` : 185 tests, OK.

## Lanceur apiselect : base de test par défaut, mode --prod avec mot de passe demandé au clavier (issue #46)

- `bin/apiselect` : `apiselect` (sans option) et `apiselect --dev` ciblent
  désormais tous deux la base de test `apiselect_dev` (comportement
  inchangé de `--dev`). `apiselect --prod` cible la vraie base `apiselect`
  avec le rôle `apiselect_prod` ; mot de passe demandé au clavier (saisie
  masquée), jamais écrit sur disque ni journalisé, transmis uniquement au
  process du serveur via variable d'environnement effacée à la sortie du
  script. Échec d'authentification détecté avant lancement du serveur,
  message clair, arrêt propre. `apiselect --prod --migrer` affiche le plan
  de migration, rappelle la nécessité d'une sauvegarde, demande
  confirmation ("oui"), applique les migrations sur la vraie base sans
  lancer de serveur.
- Page ouverte au démarrage : racine du site (`/`) au lieu de `/admin/`.
- Dossier du projet déduit de l'emplacement réel du script (lien
  symbolique résolu), plus de chemin en dur `/home/alain/ApiSelect`.
- `README.md` : usage des trois formes de commande, section dédiée au
  mode `--prod`.
- `CONTEXTE.md` : règle ajoutée (vraie base protégée par un mot de passe
  inconnu de CCL, jamais recherché ni deviné, `--prod`/`--migrer` jamais
  lancés par CCL) ; autres passages condensés pour rester sous 4000
  caractères.

# Issue #45 — Visites : correctif de l'admin, date de revérification proposée à la saisie, finitions d'affichage

## Corrigé

- `gestion/models.py` : `ObservationVisite.save()` surchargé pour
  garantir, quelle que soit l'origine de l'observation (formulaire à
  boutons, administration, autre accès) :
  - la `colonie` est toujours renseignée automatiquement depuis
    `self.visite.colonie` (plus jamais demandée au formulaire) — corrige
    l'erreur « null value in column colonie_id... violates not-null
    constraint » obtenue depuis `/admin/gestion/visite/add/` quand on y
    ajoute une observation (le sous-formulaire d'admin ne renseignait
    jamais ce champ dénormalisé) ;
  - une observation « reine morte » en doute et ouverte reçoit son
    rappel de revérification à la création si elle n'en a pas déjà un
    (`RappelRevisite.objects.get_or_create`, date par défaut
    `date_revisite_par_defaut`) — aucun doublon si l'observation est
    ré-enregistrée (relation un-à-un + `get_or_create`).
  - `date_revisite_par_defaut` accepte désormais aussi une date au
    format ISO (chaîne), pas seulement un objet `date` : nécessaire
    pour fonctionner correctement avant tout rechargement depuis la
    base (observation créée juste après sa visite dans la même
    transaction/requête).
  - Le nombre de jours reste centralisé dans l'unique constante
    `DELAI_RAPPEL_REINE_MORTE_JOURS` déjà en place (issue #43),
    utilisée par `date_revisite_par_defaut` aussi bien depuis le modèle
    que depuis le formulaire à boutons.
- `gestion/views.py` (`nouvelle_visite`) : ne crée plus le
  `RappelRevisite` directement (désormais fait par le modèle à
  l'enregistrement de l'observation) ; applique seulement la date
  choisie dans le formulaire au rappel déjà créé, s'il y en a une —
  évite la création d'un second rappel (contrainte un-à-un) tout en
  conservant le comportement existant du formulaire à boutons.

## Ajouté

- `gestion/forms.py` (`VisiteForm.clean`) : refuse une date de
  revérification antérieure à la date de la visite, avec message en
  français (« La date de revérification ne peut pas être antérieure à
  la date de la visite. »), affiché sous le champ concerné dans
  `nouvelle_visite.html`.
- `gestion/static/gestion/visite.js` : script fourni avec le projet
  (aucune ressource externe) pour le formulaire à boutons — le champ
  « Date de revérification » n'est visible que lorsque « Reine morte »
  est choisie en doute ; sa valeur proposée (visite + 9 jours) se
  recalcule quand la date de la visite change, tant que l'utilisatrice
  n'a pas elle-même modifié ce champ ; reste librement modifiable.
  Dégradation sans JavaScript : champ toujours visible et modifiable,
  le serveur applique visite + 9 jours s'il est laissé vide à l'envoi
  (déjà le comportement de secours existant, inchangé).
- `gestion/models.py` (`Visite.details_affichage`) : liste des segments
  réellement renseignés (reine observée, cadres de couvain/abeilles,
  réserves, comportement) pour l'historique des visites de la fiche
  colonie — une visite sans aucun de ces éléments n'affiche plus que sa
  date.
- Tests (`gestion/tests.py`) :
  - `ModeleObservationVisiteTests` : colonie renseignée automatiquement
    même sans la fournir, pas de second rappel au ré-enregistrement.
  - `AdminVisiteTests` : ajout d'une visite avec observation « reine
    morte » en doute par POST sur `/admin/gestion/visite/add/` sans
    erreur, colonie renseignée, un seul rappel créé à 9 jours ; date du
    rappel modifiable après coup via
    `admin:gestion_rappelrevisite_change`.
  - `RevisiteFormulaireBoutonsTests` : date de revérification choisie
    dans le formulaire utilisée pour le rappel ; date antérieure à la
    visite refusée (message affiché, aucune visite créée).
  - `HistoriqueVisitesAffichageTests` : visite sans rien renseigné
    n'affiche que sa date ; visite partielle n'affiche que les champs
    renseignés.
  - Trois tests existants (`NouvelleVisiteTests.
    test_visite_suivante_confirme/infirme_reine_morte_...`,
    `AccueilVisitesTests.test_rappel_a_revisiter_affiche_sur_accueil`)
    adaptés : ils créaient un `RappelRevisite` manuellement après avoir
    créé l'observation « reine morte » en doute à la main — devenu un
    doublon en conflit avec la création automatique par le modèle ;
    utilisent désormais le rappel auto-créé (`observation.rappel`),
    éventuellement réassigné à une date différente par `.save()`
    plutôt que par un second `.objects.create()`.
  - Les 176 tests de `gestion` + `selection` passent
    (`python manage.py test selection gestion`).

## Modifié

- `gestion/templates/gestion/fiche_colonie.html` : historique des
  visites basé sur `visite.details_affichage` (segments joints par
  « · », uniquement ceux renseignés) à la place de l'ancien texte fixe
  qui affichait « ? »/« non renseigné » pour chaque champ vide.
- `gestion/templates/gestion/nouvelle_visite.html` : inclusion de
  `gestion/visite.js` ; affichage de l'erreur du champ « Date de
  revérification » si la date est antérieure à la visite.
- `gestion/static/gestion/style.css` :
  - `.tag-action, .tag-observation` : marges intérieures augmentées
    (0.35em/0.75em au lieu de 0.2em/0.6em) et `line-height` explicite —
    le texte long (ex. « Reine morte (doute — ouverte) ») touchait les
    bords arrondis de la pastille orange sur l'historique des visites ;
  - `.erreur-champ` ajoutée pour l'affichage du message de validation
    en rouge sous un champ de formulaire.

## Non modifié (vérifié conforme)

- `gestion/admin.py` : `ObservationVisiteInline.fields` excluait déjà
  `colonie` du sous-formulaire (c'est justement l'absence
  d'auto-remplissage côté modèle qui provoquait l'erreur, pas sa
  présence dans le formulaire) — aucun changement nécessaire ici, la
  correction se fait entièrement dans `ObservationVisite.save()`.
  `RappelRevisiteAdmin` permettait déjà de modifier `date_revisite`
  après coup.

## Protection des données

Aucune commande `migrate`, `peupler_donnees_test`,
`purger_donnees_test`/`reinitialiser_donnees_test`/`purgetest`
exécutée ; aucune suppression/modification de données sur `apiselect`
ni `apiselect_dev` ; aucun serveur lancé contre ces bases. Tests
exécutés uniquement via `python manage.py test selection gestion`
(176 tests, OK). Aucune migration nécessaire (vérifié par `manage.py
makemigrations --check --dry-run gestion selection` : aucun
changement détecté). Aucun `git push`.

# Issue #44 — Fiches PDF : largeurs de colonnes de la fiche rapide, titres courts, plus de tiret dans Lignée

## Modifié

- `fiche_rapide_pdf.html` : nouvelles largeurs de colonnes (total 100 %)
  — Colonie 12 %, Lignée 10 %, les 4 colonnes de critères 11 % chacune
  (44 %), Note libre 34 %. L'issue #42 avait élargi Colonie à 22 % en
  réduisant Note libre à 8 %, rendant cette dernière inutilisable à la
  main (seul son usage réel) et les colonnes de critères inutilement
  larges pour simplement entourer un chiffre de 1 à 4. Vérifié par
  génération réelle du PDF (`pdftotext -layout`) avec un identifiant de
  ruche à 2 et 3 chiffres (« Ruche 12 », « Ruche 123 ») : tient à 12 %
  sans retour à la ligne, pas besoin de monter à 14 %. L'en-tête
  « Agressivité », trop large à 11 % en 10pt, passe en police 8pt
  (`th.col-critere`) plutôt que d'élargir la colonne, comme demandé.
- `fiche_rapide_pdf.html` et `fiche_approfondie_pdf.html` : titre de
  colonne « Lignée reine » → « Lignée » (texte statique du gabarit,
  « reine » jugé inutile) ; cellule Lignée vide (plus de « — ») quand
  la reine n'a pas de lignée connue — gênait plus qu'il n'aidait sur
  une fiche papier.
- Critère « Tenue au cadre » affiché « Tenue » sur la fiche rapide
  (« au cadre » sous-entendu) via une correspondance d'affichage simple
  dans `selection/views.py` (`TITRES_COURTS_CRITERES_PDF`, par code de
  critère, appliquée aux deux fiches PDF mais sans effet sur les
  critères approfondis qui n'y figurent pas) : n'affecte ni
  `CritereSelection.nom` en base, ni l'admin, ni le tableau de
  résultats — aucune migration. Tout critère absent de cette
  correspondance garde son nom complet.
- Tests (`selection/tests.py`, classe `FichesTerrainPdfTests`) :
  3 tests ajoutés (titres courts fiche rapide, titre court fiche
  approfondie, absence de tiret sur les deux fiches). Aucun test
  existant ne vérifiait l'ancien titre « Lignée reine » ou le tiret
  « — » — rien à adapter sur ce point, les 143 tests de `selection`
  passent (`python manage.py test selection`).

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

# Issue #42 — Fiche rapide PDF : élargir la colonne Colonie (titre coupé)

## Modifié

- `selection/templates/selection/fiche_rapide_pdf.html` : largeur de
  la colonne « Colonie » portée de 8 % à 22 % (reprise de la largeur
  de « Note libre », la plus large), et largeur de « Note libre »
  ramenée de 22 % à 8 % en contrepartie, pour garder un total de
  100 %. Largeurs appliquées à l'identique sur les en-têtes (`th`) et
  sur chaque cellule de donnée (`td`, y compris les cellules vides),
  comme c'était déjà le cas. Corrige le titre « Colonie » coupé par
  la ligne de séparation de la colonne suivante et le retour à la
  ligne des libellés de ruche (ex. « Ruche 12 »). Aucun autre gabarit
  touché, fiche approfondie inchangée. Les 140 tests de `selection`
  passent sans modification.

# Issue #40 — CONTEXTE.md : nouveau périmètre (gestion du rucher d'abord, sélection ensuite)

## Modifié

- `CONTEXTE.md` : nouvelle section « Périmètre : deux parties,
  dépendance à sens unique » qui décrit le découpage cible — gestion
  du rucher (ruchers, ruches, colonies, reines, et à construire :
  visites, récoltes, traitements, stocks) construite d'abord, puis
  sélection des reines (campagnes, cellules royales, critères,
  mesures, calendrier d'élevage, fiches PDF, résultats, diagnostic)
  réservée à Alain et reprise plus tard sans changement. Ajoute la
  règle de dépendance impérative (le code de gestion ne doit jamais
  dépendre d'un modèle/vue/table/gabarit de sélection, seule la
  sélection peut dépendre de la gestion) et la règle de portabilité
  pour tout nouveau code (pas de chemin en dur, pas de SQL propre à
  PostgreSQL, pas de dépendance à un script bash, en vue d'une future
  version Windows/SQLite) ainsi qu'une note précisant que
  l'environnement actuel reste PostgreSQL. Section « Règles de
  travail » conservée intacte. Sections « Sélection génétique »,
  « Calendrier d'élevage » et « Mode diagnostic » fusionnées et
  condensées, Vocabulaire et Stack légèrement raccourcis, pour tenir
  sous la limite de 4000 caractères (3996 caractères au final) tout
  en ajoutant le nouveau contenu. Mention de `Cours_Apiculture/`
  (jamais committé ni référencé dans une issue) conservée.

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

