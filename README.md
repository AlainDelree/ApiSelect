# ApiSelect

Outil de gestion d'un rucher orienté élevage de reines et sélection génétique
sur critères mesurables (voir `CONTEXTE.md` pour le détail fonctionnel).

## Lancer le serveur

Depuis n'importe quel répertoire, la commande `apiselect` démarre le serveur
de développement Django et ouvre automatiquement un onglet de navigateur sur
`http://127.0.0.1:8000/admin/`. `Ctrl+C` arrête proprement le serveur.

Le script se trouve dans `bin/apiselect` ; pour le rendre accessible en tapant
simplement `apiselect`, créer un lien symbolique dans un dossier déjà présent
dans le `PATH` (ex. `~/bin`) :

```bash
ln -s /home/alain/ApiSelect/bin/apiselect ~/bin/apiselect
```

(nécessite un nouveau terminal si `~/bin` vient d'être ajouté au `PATH`).

## Base de données de test (`--dev`)

Pour tester l'outil de bout en bout (calcul d'index, calendrier, fiches PDF)
avec des données fictives sans jamais risquer de toucher aux vraies données,
`apiselect --dev` lance le serveur sur une seconde base PostgreSQL,
`apiselect_dev`, séparée de la vraie base `apiselect`. Le code reste le
même (pas de branche Git) : seule la base ciblée change, selon la variable
d'environnement `DJANGO_DB_NAME` (absente par défaut, jamais utilisée sans
ce choix explicite).

**Créer la base une seule fois** (le rôle `apiselect` existe déjà, utilisé
par la vraie base — voir `.env`) :

```bash
sudo -u postgres createdb --owner=apiselect apiselect_dev
```

Ensuite, à chaque lancement :

```bash
apiselect --dev
```

Les tables sont créées/mises à jour automatiquement (`migrate`) au premier
lancement. Un bandeau rouge « ⚠️ BASE DE TEST — données fictives » apparaît
alors en haut de toutes les pages (admin Django et vues du projet), pour ne
jamais confondre les deux bases pendant la manipulation.

### Peupler / purger le jeu de données fictif

Deux commandes de gestion, à lancer sur la base de test uniquement (elles
refusent explicitement de s'exécuter si la base active est la vraie base
`apiselect`) :

```bash
apiselect --dev &          # lance le serveur en tâche de fond, ou dans un autre terminal
DJANGO_DB_NAME=apiselect_dev python manage.py peupler_donnees_test
# ... tests, manipulations ...
DJANGO_DB_NAME=apiselect_dev python manage.py purger_donnees_test
```

`peupler_donnees_test` crée un rucher fictif (« Rucher Test »), 3 colonies
avec ruches et reines préfixées `TEST-` (une avec des mesures normales, une
exclue par seuil éliminatoire, une sans aucune mesure), une campagne
d'élevage fictive avec date de référence et des poids de critères.

`purger_donnees_test` supprime uniquement ces données (via le rucher
« Rucher Test » et le préfixe `TEST-`), sans toucher au reste de la base.

### Tout réinitialiser en une commande (`purgetest`)

Pour repartir d'un jeu de données fictif fraîchement recréé sans taper les
deux commandes ci-dessus ni définir `DJANGO_DB_NAME` à la main, la commande
`purgetest` enchaîne purge puis peuplement sur la base `apiselect_dev`,
depuis n'importe quel répertoire :

```bash
purgetest
```

Comme `apiselect`, le script se trouve dans `bin/purgetest` ; pour le rendre
accessible en tapant simplement `purgetest`, créer un lien symbolique dans
un dossier déjà présent dans le `PATH` (ex. `~/bin`) :

```bash
ln -s /home/alain/ApiSelect/bin/purgetest ~/bin/purgetest
```

`purgetest` ne lance pas de serveur : il purge puis repeuple la base de
test, affiche le résultat (rucher, colonies, campagne créés) puis se
termine.
