# Contexte projet — ApiSelect (sélection génétique par élevage de reines)

## Objectif / Stack
Outil de gestion d'un rucher orienté élevage de reines et sélection
sur critères mesurables. Usage bureau (saisie le soir, pas mobile/
terrain, propolis/gants). Utilisateur unique. Python/Django,
PostgreSQL, admin Django (saisie par lot), xhtml2pdf (PDF, pure
Python — portable Linux/Windows sans dépendance système, préféré à
WeasyPrint pour cette raison), calendrier (FullCalendar ou vue custom).

## Vocabulaire — distinctions du modèle
(l'utilisateur mélange ces termes à l'oral ; la rigueur vient du code)
- **Rucher** : emplacement géographique.
- **Ruche** : boîte physique. Type + numéro = identité (numéro cloué
  sur la boîte). Types en table (TypeRuche + alias) : Dadant 10/
  "Ruche", Ruchette 6/"Ruchette", Apidea, DH. Affichage : alias +
  numéro sans "n°" (ex. "Ruche 3"). Apidea/DH : numéro réutilisable,
  pas d'identité permanente sur les planches.
- **Colonie** : population vivante à un instant donné, liée à une
  ruche. Mode de création : achat/essaimage naturel/artificiel/
  fusion-réunion/origine inconnue (indépendant de l'origine de la
  reine actuelle, ex. reine achetée dans une colonie issue de fusion).
  Historique de configuration (corps + hausses) et de déménagement/
  remérage à tracer.
- **Reine** : identité généalogique réelle, indépendante de la boîte.
  Liée à sa mère, lignée mâle probable (fécondation en vol =
  probabiliste), station de fécondation, marquage couleur/année.
- Cadres "corps"/"hausse" (2 hausse = 1 corps en hauteur),
  interchangeables Dadant/ruchette selon la hauteur, pas la largeur.
- Hors scope : inventaire matériel/consommables, suivi varroa,
  entretien/peinture. Piste future (non conçue) : vocabulaire
  configurable si l'outil est partagé (ex. "Ruche" = boîte pour
  certains, = colonie pour d'autres).
- **Principe** : l'alias est un habillage d'affichage, jamais un
  identifiant fonctionnel — recherche/liens/actions utilisent
  toujours les champs structurés (type+numéro, id).

## Documents de référence (locaux, non versionnés)
`Cours_Apiculture/`, gitignoré (droits d'auteur, dépôt public) :
- `Elevage de reine.pdf` — cours (Maranzan/CRISAB), barème détaillé.
- `calendrier élevage de reine.ods` — logique de dates en cascade
  d'origine, base du module calendrier.
Ne jamais committer ni référencer dans une issue.

## Sélection génétique
9 critères du cours, deux passes : **rapide** (toutes colonies) santé/
propreté/agressivité/tenue au cadre ; **approfondie** (colonies
pressenties) nettoyage/récolte/couvain/miel/pollen. Score 1-4 selon
barème du cours (`Cours_Apiculture/Elevage de reine.pdf`, non
versionné). Poids 0-10 par campagne (historisé). Seuils éliminatoires
optionnels. Index = Σ(score×poids)/Σ(poids). Tableau trié par index.

## Calendrier d'élevage
Cascade de dates reflétant la méthode réelle d'Alain (issue #14, révise
l'issue #7 qui avait été calquée à tort sur le cours générique) : pas de
starter séparé (greffage direct dans une ruche orpheline qui élève les
cellules royales jusqu'à operculation et au-delà), pas de couveuse (les
cellules restent sur la colonie orpheline), distribution directe dans
les Apidea (pas de ruchettes), pas de libération ni de contrôle des
naissances séparés. Ponte = jour 0 : mâles -16j (facultatif, activé par
campagne — pas encore pratiqué avec le nombre de ruches actuel), picking
+4j, ruche orpheline +4j, garnir les Apidea +14j, contrôle ponte et pose
de la grille anti-essaimage +25j. Multi-campagnes en parallèle. Vue
calendrier mensuel + liste de tâches. La constitution des Apidea
eux-mêmes (peuplement, confinement) n'a pas de date fixe par campagne et
n'est pas modélisée dans cette cascade.

## Fiches de terrain
Fiche rapide (colonies actives, 4 critères passe rapide, cases 1-4 à
entourer) et fiche approfondie (colonies choisies via formulaire, 5
critères, valeur brute à noter). xhtml2pdf.

## État d'avancement
Conception initiale complète : modèle de données, 3 vues PostgreSQL,
TypeRuche en table (alias éditables), 9 critères peuplés, index
pondéré testé, tableau de résultats, calendrier multi-campagnes,
fiches PDF. Commande globale `apiselect` (lance serveur + navigateur
sur /admin/). Auto-complétion année seule → 01/04/AAAA sur
date_naissance (Reine). Saisie réelle en cours : 2 ruchers (Bovesse,
Anhée), reines A24 et Beelgium_Blanche créées, colonies en cours de
complétion (numéros de ruche à confirmer sur site).
