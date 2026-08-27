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
  ruche. Mode de création : achat/essaimage naturel/artificiel/origine
  inconnue. Historique de configuration (corps + hausses) et de
  déménagement/remérage à tracer.
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
Cascade de dates depuis l'ODS (ponte = jour 0 : mâles -16j, picking/
starter +4j, finisseur +5j, couveuse +9j, ruchettes +14j, libération
+17j, contrôle naissance +19j, début ponte +25j, contrôle ponte +26j).
Multi-campagnes en parallèle. Vue calendrier mensuel + liste de tâches.

## Fiches de terrain
Fiche rapide (toutes colonies actives, 4 critères passe rapide, cases
1-4 à entourer) et fiche approfondie (colonies choisies via
formulaire, 5 critères, valeur brute à noter). xhtml2pdf.

## État d'avancement
Conception initiale complète et implémentée : modèle de données,
3 vues PostgreSQL, TypeRuche en table (alias éditables), 9 critères
peuplés, index pondéré testé, tableau de résultats, calendrier
multi-campagnes, fiches PDF. Aucune donnée réelle saisie (2 colonies
en attente de visite terrain). Suite : à définir après saisie réelle.
