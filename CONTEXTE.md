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
- `Elevage_de_reine.pdf` — cours (Maranzan/CRISAB), barème détaillé
  des 9 critères et protocoles de mesure.
- `calendrier_élevage_de_reine.ods` — logique de dates en cascade
  d'origine, base du module calendrier.
Ne jamais committer ni référencer dans une issue.

## Sélection génétique
9 critères du cours, deux passes : **rapide** (toutes colonies,
chaque visite) santé/propreté/agressivité/tenue au cadre ;
**approfondie** (colonies pressenties, matériel requis) nettoyage
(temps)/récolte (kg vs moyenne rucher)/couvain (D×d×nb cadres)/miel
(kg)/pollen (dm²). Mesure brute + score 1-4 selon barème du cours
(`Cours_Apiculture/Elevage_de_reine.pdf`, non versionné). Poids 0-10
par année/campagne (historisé). Seuils éliminatoires optionnels (ex.
santé, agressivité), indépendants du poids.
Index = Σ(score×poids)/Σ(poids). Tableau trié par index, détail des
9 mesures à côté.

## Calendrier d'élevage
Reprend la logique de l'ODS (dates en cascade depuis une ponte ou un
picking : starter, picking, finisseur, couveuse, ruchettes,
libération, contrôle naissance, ponte). Plusieurs campagnes en
parallèle (multi-lignées, multi-sites), saturation de mâles (~16j
avant ponte des reines). Deux vues : calendrier mois/semaine
(campagnes superposées) + liste de tâches toutes campagnes confondues.

## Fiches de terrain
Bouton générant un PDF imprimable (fiche rapide + approfondie),
header pré-rempli (date, ruchers, colonies + lignée). Brouillon pour
la saisie du soir.

## État d'avancement
Django initialisé (modèle, admin, 3 vues PostgreSQL en lecture, index
pondéré testé). CritereSelection vide (9 critères à peupler). Aucune
donnée réelle saisie (2 colonies en attente de visite). Issue en
cours : table TypeRuche + alias. Suite : tableau de résultats trié,
calendrier, fiches PDF (xhtml2pdf).
