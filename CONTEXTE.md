# Contexte projet — ApiSelect (sélection génétique par élevage de reines)

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

## Objectif / Stack
Gestion d'un rucher orienté élevage de reines, sélection sur critères
mesurables. Usage bureau, utilisateur unique. Python/Django, PostgreSQL
(`apiselect` = réelle, `apiselect_dev` = test), admin Django,
xhtml2pdf (PDF pur Python).

## Vocabulaire (la rigueur vient du code, pas de l'oral)
**Rucher** = emplacement. **Ruche** = boîte physique (type+numéro =
identité ; Apidea/DH : numéro réutilisable). **Colonie** = population
vivante liée à une ruche (mode de création, historique config +
événements séparé). **Reine** = identité généalogique indépendante de
la boîte (mère, lignée mâle probable, station de fécondation, statut
vierge/fécondée, mode d'acquisition : élevée / achetée en CR, vierge
ou fécondée / arrivée avec essaim / remérage naturel — issue #29).
**CelluleRoyale** = tentative individuelle d'élevage (cf. plus bas).
Alias = habillage d'affichage seulement ; recherche/liens sur champs
structurés (id, type+numéro).

## Documents de référence
`Cours_Apiculture/` (gitignoré) : barème + calendrier source. Jamais
committé ni référencé dans une issue.

## Sélection génétique
9 critères (rapide : santé/propreté/agressivité/tenue au cadre ;
approfondie : nettoyage/récolte/couvain/miel/pollen), score 1-4,
fiches PDF. `LotCriteres` = lot nommé réutilisable de poids (0-10)/seuils
éliminatoires, **indépendant des campagnes** (`CampagneElevage.
lot_criteres`, partageable ; nouvelle stratégie = nouveau lot, jamais
modifier l'existant). Index = Σ(score×poids)/Σ(poids).
`Mesure.campagne` **obligatoire** (issue #31, sinon mesure invisible du
tableau de résultats).

## Calendrier d'élevage
4 étapes en cascade (méthode réelle d'Alain, issues #14/#25 : pas de
starter/couveuse séparés, distribution directe en Apidea). Ponte =
jour 0 → **Orphelinage** (règle des 9j), **Picking** +4j (greffage),
**Garnir les Apidea** +14j, **Contrôle ponte et grille** +25j. Étape
facultative **Élevage des mâles** (-16j, activée par campagne via
`elevage_males_actif`, pas encore pratiquée). Multi-campagnes en
parallèle. Suivi individuel de chaque cellule royale (plusieurs par
ruche orpheline) dans `CelluleRoyale` (issue #25), pas en étape
agrégée : trace une tentative (mère greffée, ruche orpheline, Apidea
destination, statut En développement/Devenue reine/Morte avant
éclosion/Perdue), ne disparaît jamais en échec (permet
`CampagneElevage.taux_reussite`). Lien vers `Reine` renseigné
**seulement si Devenue reine** (admin « Confirmer éclosion »).

## Mode diagnostic (issue #32)
Page `/diagnostic/` : vérifications de cohérence consultatives
(n'empêchent jamais la saisie), ex. campagne active sans
`lot_criteres`. Vérification = fonction indépendante dans
`selection/diagnostics.py`, listée dans `VERIFICATIONS`.

## État des migrations et d'avancement
Migrations 0010-0015 (lots de critères, vue mesures complètes, poids
0-10, retrait nombre_cr, date_creation Colonie optionnelle,
Mesure.campagne obligatoire) appliquées sur `apiselect_dev`. **En
attente sur `apiselect`** (vraie base), à appliquer par Alain
lui-même. Saisie réelle en cours : 2 ruchers (Bovesse, Anhée). Alain
reprend le projet après une pause d'un mois.
