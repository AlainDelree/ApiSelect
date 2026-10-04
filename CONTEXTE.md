# Contexte projet — ApiSelect (gestion du rucher + sélection génétique par élevage de reines)

## ⚠️ Règles de travail (prioritaires)
- **Données : jamais de suppression/modification sur `apiselect` ou
  `apiselect_dev` sans accord explicite d'Alain** (données réelles
  saisies pendant les tests). Interdits sans accord : `flush`,
  `dropdb`, `loaddata`, DELETE/TRUNCATE, `purgetest`,
  `purger_donnees_test`/`reinitialiser_donnees_test`/
  `peupler_donnees_test` (et leur modification). Données `TEST-`/
  « Rucher Test » incluses (appartiennent à ces commandes).
- Jamais de `migrate` sur `apiselect`/`apiselect_dev` : Alain s'en
  charge (`apiselect --dev`).
- La vraie base `apiselect` est protégée par un mot de passe connu
  d'Alain seul : CCL ne tente jamais de s'y connecter ni de le
  deviner, ni de lancer `--prod` ou `--migrer`.
- Tests : `python manage.py test selection gestion`. Vérification
  manuelle : jamais remplir ni purger la base de test.
- Aucun `git push` : Alain pousse après relecture.

## Périmètre : deux parties, dépendance à sens unique
Scission en deux pour céder un jour la gestion seule (programme
Windows autonome), sélection réservée à Alain :
- **Gestion du rucher** (cible, construite d'abord) : ruchers, ruches,
  colonies, reines, visites ; à construire : récoltes, traitements,
  stocks. Principe de saisie : un seul formulaire par type de donnée,
  par l'interface visuelle ; admin réservée aux référentiels et aux
  corrections exceptionnelles — jamais un second formulaire de saisie
  pour les mêmes données.
- **Sélection des reines** (réservée à Alain, reprise plus tard,
  inchangée pour l'instant) : campagnes, cellules royales, critères,
  mesures, calendrier d'élevage, fiches PDF, résultats, diagnostic.

**Règle de dépendance (impérative)** : le code de gestion ne doit
jamais importer/référencer un modèle, une vue, une table ou un
gabarit de sélection. Seule la sélection dépend de la gestion.

**Portabilité** : pas de chemin en dur, pas de SQL PostgreSQL-
spécifique, pas de dépendance à un script bash — version Windows
autonome prévue sous SQLite (base actuelle : PostgreSQL).

## Stack
Python/Django, admin Django, xhtml2pdf. Documents de référence :
`Cours_Apiculture/` (gitignoré), jamais committé.

## Vocabulaire (la rigueur vient du code, pas de l'oral)
**Rucher** = emplacement. **Ruche** = boîte physique (type+numéro =
identité ; Apidea/DH : numéro réutilisable). **Colonie** = population
vivante liée à une ruche (historique config + événements séparé).
**Reine** = identité généalogique indépendante de la boîte (mère,
lignée mâle probable, station de fécondation, statut vierge/fécondée,
mode d'acquisition : élevée / achetée en CR / arrivée avec essaim /
remérage naturel). **CelluleRoyale** = tentative d'élevage (sélection).
Alias : affichage seulement, jamais recherché/lié (champs structurés
id/type+numéro).

## Sélection (inchangée)
9 critères (rapide : santé/propreté/agressivité/tenue au cadre ;
approfondie : nettoyage/récolte/couvain/miel/pollen), score 1-4,
fiches PDF. `LotCriteres` = lot nommé réutilisable de poids
(0-10)/seuils éliminatoires, indépendant des campagnes
(`CampagneElevage.lot_criteres`, partageable). Index =
Σ(score×poids)/Σ(poids). `Mesure.campagne` obligatoire (issue #31).
Calendrier en cascade (issues #14/#25) : Ponte(0)→Orphelinage(9j)→
Picking(+4j)→Garnir Apidea(+14j)→Contrôle ponte/grille(+25j) ;
Élevage des mâles facultatif(-16j). Suivi individuel par
`CelluleRoyale` (issue #25, 4 statuts), lien vers `Reine` seulement si
devenue reine. Diagnostic (`/diagnostic/`, issue #32) :
`selection/diagnostics.py`, liste `VERIFICATIONS`.

## État des migrations et d'avancement
`apiselect_dev` à jour. Sur `apiselect` : 0010-0014 appliquées,
0015/0016 et celles de `gestion` en attente (Alain s'en charge).
Saisie réelle : 2 ruchers (Bovesse, Anhée).
