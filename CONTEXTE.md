# Contexte projet — ApiSelect (gestion du rucher + sélection génétique par élevage de reines)

## ⚠️ Règles de travail (prioritaires)
- **Données : jamais de suppression/modification sur `apiselect` ou
  `apiselect_dev` sans accord explicite d'Alain** (données réelles
  saisies pendant les tests). Interdits sans accord : `flush`,
  `dropdb`, `loaddata`, DELETE/TRUNCATE, `purgetest`,
  `purger_donnees_test`/`reinitialiser_donnees_test`/
  `peupler_donnees_test` (et leur modification). Données `TEST-`/
  « Rucher Test » incluses (appartiennent à ces commandes).
- Jamais de `migrate` sur `apiselect` : Alain s'en charge.
- Tests : uniquement `python manage.py test selection`.
- Aucun `git push` : Alain pousse après relecture.

## Périmètre : deux parties, dépendance à sens unique
Le projet se scinde en deux, pour donner un jour la gestion seule à
une autre personne (programme Windows autonome) et garder la
sélection pour Alain :
- **Gestion du rucher** (cible, construite d'abord) : ruchers,
  ruches, colonies, suivi des reines ; à construire : visites
  (inspections de colonies), récoltes, traitements, stocks.
- **Sélection des reines** (réservée à Alain, reprise plus tard,
  inchangée pour l'instant) : campagnes, cellules royales, critères,
  mesures, calendrier d'élevage, fiches PDF, résultats, diagnostic.

**Règle de dépendance (impérative pour tout nouveau code de
gestion)** : le code de gestion ne doit jamais importer, référencer
ni dépendre d'un modèle, d'une vue, d'une table ou d'un gabarit de
sélection. Seule la sélection peut dépendre de la gestion.

**Portabilité (pour tout nouveau code)** : la version destinée à
l'autre personne tournera seule sous Windows avec une base SQLite —
donc pas de chemin écrit en dur, pas de SQL propre à PostgreSQL, pas
de dépendance à un script bash.

**Environnement actuel** : la base reste PostgreSQL (`apiselect` /
`apiselect_dev`) ; le passage à SQLite/Windows est un chantier
ultérieur, non commencé.

## Stack
Python/Django, admin Django, xhtml2pdf (PDF pur Python).

## Vocabulaire (la rigueur vient du code, pas de l'oral)
**Rucher** = emplacement. **Ruche** = boîte physique (type+numéro =
identité ; Apidea/DH : numéro réutilisable). **Colonie** = population
vivante liée à une ruche (historique config + événements séparé).
**Reine** = identité généalogique indépendante de la boîte (mère,
lignée mâle probable, station de fécondation, statut vierge/fécondée,
mode d'acquisition : élevée / achetée en CR / arrivée avec essaim /
remérage naturel — issue #29). **CelluleRoyale** = tentative
individuelle d'élevage (sélection). Alias = habillage d'affichage
seulement ; recherche/liens sur champs structurés (id, type+numéro).

## Documents de référence
`Cours_Apiculture/` (gitignoré) : barème + calendrier source. Jamais
committé ni référencé dans une issue.

## Sélection génétique (inchangée, reprise plus tard)
9 critères (rapide : santé/propreté/agressivité/tenue au cadre ;
approfondie : nettoyage/récolte/couvain/miel/pollen), score 1-4,
fiches PDF. `LotCriteres` = lot nommé réutilisable de poids
(0-10)/seuils éliminatoires, indépendant des campagnes
(`CampagneElevage.lot_criteres`, partageable). Index =
Σ(score×poids)/Σ(poids). `Mesure.campagne` obligatoire (issue #31).
Calendrier en 4 étapes en cascade (issues #14/#25) : Ponte (jour 0) →
Orphelinage (9j) → Picking +4j → Garnir les Apidea +14j → Contrôle
ponte et grille +25j ; étape facultative Élevage des mâles (-16j).
Suivi individuel par `CelluleRoyale` (issue #25, statuts En
développement/Devenue reine/Morte avant éclosion/Perdue), lien vers
`Reine` seulement si Devenue reine. Mode diagnostic (`/diagnostic/`,
issue #32) : vérifications consultatives dans
`selection/diagnostics.py` (liste `VERIFICATIONS`).

## État des migrations et d'avancement
Migrations 0010-0015 appliquées sur `apiselect_dev`, **en attente sur
`apiselect`** (Alain s'en charge). Saisie réelle en cours : 2 ruchers
(Bovesse, Anhée). Alain reprend le projet après une pause.
