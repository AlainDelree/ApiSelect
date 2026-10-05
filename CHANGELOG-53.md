# Issue #53 — Marquage de la reine : demander la couleur, proposée selon l'année de naissance

## Ajouté

- `gestion/couleurs.py` : formalisation en une seule fonction
  (`couleur_marquage_pour_annee`) de la correspondance année de
  naissance -> couleur de marquage déjà présente sous forme de texte
  dans les libellés de `selection.models.CouleurMarquage` (dernier
  chiffre de l'année : 1/6 blanc, 2/7 jaune, 3/8 rouge, 4/9 vert, 5/0
  bleu). Ajout de `couleur_marquage_proposee(reine)` (couleur déjà
  enregistrée en priorité, sinon celle de l'année de naissance, `None`
  si aucune des deux n'est connue) et de `nom_couleur_marquage(code)`
  (nom court sans la mention de l'année, pour l'affichage).
- `gestion/templatetags/gestion_extras.py` : filtres `nom_couleur_marquage`
  et `couleur_a_utiliser` (ce dernier retourne « couleur à choisir » si
  ni couleur enregistrée ni année de naissance ne sont connues).
- Page « Marquer la reine » (`MarquerReineForm`, `marquer_reine`) :
  champ couleur de marquage obligatoire, proposé à l'ouverture de la
  page (`couleur_marquage_proposee`), modifiable parmi les couleurs du
  modèle. Les trois valeurs (marquage effectué, date, couleur) sont
  enregistrées ensemble.
- Formulaire « Nouvelle reine » (`NouvelleReineForm`, `nouvelle_reine`) :
  nouveau champ facultatif « Date de naissance » ; nouveau champ
  « Couleur du marquage », obligatoire uniquement quand « Marquage
  effectué » est « oui » (validé dans `clean()`), non pris en compte
  sinon — une couleur déjà enregistrée sur une reine existante choisie
  (origine « Reine déjà enregistrée ») n'est jamais touchée par ce
  formulaire. `gestion/static/gestion/nouvelle_reine.js` : la couleur
  est recalculée quand la date de naissance change, tant qu'elle n'a
  pas été modifiée à la main (mapping dupliqué en JS, sans ressource
  externe, à garder cohérent avec `couleur_marquage_pour_annee`) ; sans
  JavaScript, le champ reste visible et modifiable, la validation
  serveur restant identique.

## Modifié

- `gestion/templates/gestion/fiche_colonie.html` : bloc « Reine »,
  fusion des deux lignes « Marquage » / « Marquée » en une seule :
  « Marquée en [couleur] le [date] » pour une reine marquée, « Non
  marquée » sinon (une couleur déjà enregistrée sur une reine non
  encore marquée n'est plus affichée dans ce bloc — elle ne concerne
  que la marche à suivre pour le marquage, cf. page « Reines à
  marquer » ci-dessous).
- `gestion/templates/gestion/reines_a_marquer.html` : affichage de la
  couleur à utiliser pour chaque reine de la liste (`couleur_a_utiliser`),
  pour savoir quel marqueur prendre avant d'aller au rucher. La
  pastille de marquage des tuiles d'accueil n'est pas modifiée (hors
  périmètre de cette issue).

## Tests

`gestion/tests.py` : `CouleurMarquagePourAnneeTests` (une couleur par
année, aucune proposition si année inconnue), `MarquerReineCouleurTests`
(couleur proposée selon l'année, couleur déjà enregistrée proposée en
priorité, naissance inconnue sans proposition, couleur obligatoire pour
marquer), `AffichageMarquageFicheColonieTests` (« Marquée en … le … » /
« Non marquée »), `CouleurAUtiliserReinesAMarquerTests` (couleur à
utiliser / « couleur à choisir »), `NouvelleReineCouleurMarquageTests`
(couleur obligatoire si marquage « oui », non demandée si « non »,
couleur déjà enregistrée conservée pour une reine existante choisie).
Test existant de marquage mis à jour pour couvrir les trois valeurs
enregistrées (date, couleur, marquage effectué). Suite complète
(`python manage.py test selection gestion`) : 255 tests, OK.

Aucune migration : les champs `Reine.date_naissance` et
`Reine.couleur_marquage` existaient déjà.
