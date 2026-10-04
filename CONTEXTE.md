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
- Tests : `python manage.py test selection gestion`. Vérification
  manuelle : jamais remplir ni purger la base de test.
- Aucun `git push` : Alain pousse après relecture.

## Périmètre : deux parties, dépendance à sens unique
Scission en deux, pour donner un jour la gestion seule à une autre
personne (programme Windows autonome) et garder la sélection pour
Alain :
- **Gestion du rucher** (cible, construite d'abord) : ruchers, ruches,
  colonies, reines, visites ; à construire : récoltes, traitements,
  stocks.
- **Sélection des reines** (réservée à Alain, reprise plus tard,
  inchangée pour l'instant) : campagnes, cellules royales, critères,
  mesures, calendrier d'élevage, fiches PDF, résultats, diagnostic.

**Règle de dépendance (impérative pour tout nouveau code de
gestion)** : le code de gestion ne doit jamais importer, référencer
ni dépendre d'un modèle, d'une vue, d'une table ou d'un gabarit de
sélection. Seule la sélection peut dépendre de la gestion.

**Portabilité (pour tout nouveau code)** : pas de chemin écrit en dur,
pas de SQL propre à PostgreSQL, pas de dépendance à un script bash —
la version Windows autonome tournera sous SQLite (chantier ultérieur,
non commencé ; base actuelle : PostgreSQL `apiselect`/`apiselect_dev`).

## Stack
Python/Django, admin Django, xhtml2pdf.

## Vocabulaire (la rigueur vient du code, pas de l'oral)
**Rucher** = emplacement. **Ruche** = boîte physique (type+numéro =
identité ; Apidea/DH : numéro réutilisable). **Colonie** = population
vivante liée à une ruche (historique config + événements séparé).
**Reine** = identité généalogique indépendante de la boîte (mère,
lignée mâle probable, station de fécondation, statut vierge/fécondée,
mode d'acquisition : élevée / achetée en CR / arrivée avec essaim /
remérage naturel — issue #29). **CelluleRoyale** = tentative individuelle d'élevage (sélection).
Alias : affichage seulement, jamais recherché/lié (champs structurés
id/type+numéro).

## Documents de référence
`Cours_Apiculture/` (gitignoré) : barème + calendrier source, jamais
committé ni référencé.

## Sélection génétique (inchangée, reprise plus tard)
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
Tout est à jour sur `apiselect_dev`. Sur `apiselect`, 0010-0014 sont
déjà appliquées (constaté par Alain) ; seules 0015, 0016 et celles de
`gestion` à venir y sont encore en attente (Alain s'en charge).
Saisie réelle en cours : 2 ruchers (Bovesse, Anhée). Alain reprend le
projet après une pause.
