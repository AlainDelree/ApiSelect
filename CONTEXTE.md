# Contexte projet — ApiSelect (sélection génétique par élevage de reines)

## Objectif
Outil de gestion d'un rucher orienté élevage de reines et sélection
sur critères mesurables, le plus scientifique possible. Usage bureau
(saisie le soir depuis notes papier — pas de saisie mobile terrain,
propolis/gants). Utilisateur unique.

## Stack
Python/Django, PostgreSQL. Admin Django comme interface de saisie
principale (tableaux éditables, saisie par lot). WeasyPrint (ou
équivalent) pour génération PDF à la volée des fiches de terrain.
FullCalendar ou vue custom pour le calendrier.

## Vocabulaire — distinctions du modèle de données
(l'utilisateur mélange ces termes à l'oral ; la rigueur vient du code)
- **Rucher** : emplacement géographique.
- **Ruche** : boîte physique. Type + numéro = identité unique
  (ex. "Dadant 10 n°3" ≠ "Ruchette 6 n°3"). Types : Dadant 10, ruchette
  6, Apidea (nucléus fécondation), DH (double haussette, hivernage
  improvisé faute de ruchette). Apidea/DH : numérotation réutilisable,
  pas d'identité permanente sur les planches.
- **Colonie** : population vivante à un instant donné, liée à une
  ruche. Mode de création : achat/essaimage naturel/essaim
  artificiel/origine inconnue. Historique de configuration (corps +
  hausses) et de déménagement/remérage à tracer.
- **Reine** : identité généalogique réelle, indépendante de la boîte.
  Liée à sa mère, lignée mâle probable (fécondation en vol =
  probabiliste), station de fécondation, marquage couleur/année.
- Cadres "corps"/"hausse" (2 hausse = 1 corps en hauteur),
  interchangeables Dadant/ruchette selon la hauteur, pas la largeur.
- Hors scope (projets séparés) : inventaire matériel/consommables,
  suivi varroa.

## Documents de référence (locaux, non versionnés)
`Cours_Apiculture/` à la racine du dépôt, gitignoré (droits d'auteur,
dépôt public — doc Bridge_Agent §8) :
- `Elevage_de_reine.pdf` — cours (Maranzan/CRISAB), barème détaillé
  des 9 critères et protocoles de mesure.
- `calendrier_élevage_de_reine.ods` — logique de dates en cascade
  d'origine, base du module calendrier.
Ne jamais committer ce dossier ni le référencer dans une issue.

## Sélection génétique
9 critères du cours, mesurés en deux passes :
- **Passe rapide** (toutes colonies, chaque visite) : santé, propreté,
  agressivité, tenue au cadre.
- **Passe approfondie** (colonies déjà pressenties, moins fréquent,
  nécessite matériel) : nettoyage (temps), couvain (D×d×nb cadres),
  miel (kg), pollen (dm²).
Mesure brute stockée + score 1-4 calculé automatiquement selon barème
du cours (voir `Cours_Apiculture/Elevage_de_reine.pdf`, non versionné).
Poids de critère 0-10, modifiable par année/campagne (ne pas écraser
l'historique : conserver les poids utilisés à chaque calcul). Seuils
éliminatoires optionnels sur certains critères (ex. santé, agressivité)
indépendants du poids. Index = Σ(score×poids) / Σ(poids).
Résultats affichés en tableau trié par index, détail des 9 mesures
visible à côté.

## Calendrier d'élevage
Reprend la logique de l'ODS (dates en cascade depuis une date de ponte
ou de picking : starter, picking, finisseur, couveuse, ruchettes,
libération, contrôle naissance, ponte). Gère plusieurs campagnes en
parallèle (multi-lignées, multi-sites de fécondation), saturation de
mâles (décalage ~16j avant la ponte des reines). Deux vues : calendrier
mois/semaine (campagnes superposées) + liste de tâches toutes campagnes
confondues.

## Fiches de terrain
Bouton dans l'interface générant un PDF imprimable (fiche rapide +
approfondie), header pré-rempli (date, ruchers, colonies + lignée).
Sert de brouillon pour la saisie du soir dans le même écran.

## État d'avancement
Conception fonctionnelle terminée (conversation Claude Chat). Aucun
code encore écrit. Prochaine étape : modèle de données Django (issue
"chef"), puis modules un par un.
