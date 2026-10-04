# ApiSelect

Outil de gestion d'un rucher orienté élevage de reines et sélection génétique
sur critères mesurables (voir `CONTEXTE.md` pour le détail fonctionnel).

## Lancer le serveur

Depuis n'importe quel répertoire, la commande `apiselect` démarre le serveur
de développement Django et ouvre automatiquement un onglet de navigateur sur
l'accueil du site (`http://127.0.0.1:8000/`). `Ctrl+C` arrête proprement le
serveur.

Le script se trouve dans `bin/apiselect` ; pour le rendre accessible en tapant
simplement `apiselect`, créer un lien symbolique dans un dossier déjà présent
dans le `PATH` (ex. `~/bin`) :

```bash
ln -s /chemin/vers/ApiSelect/bin/apiselect ~/bin/apiselect
```

(nécessite un nouveau terminal si `~/bin` vient d'être ajouté au `PATH`).

**Principe : base de test par défaut.** `apiselect` (sans option) et
`apiselect --dev` sont équivalents et ciblent toujours la base de test
`apiselect_dev`. La vraie base `apiselect` n'est utilisée qu'explicitement,
via `apiselect --prod`, avec son propre rôle PostgreSQL (`apiselect_prod`)
et son propre mot de passe — jamais celui de `apiselect_dev`.

```bash
apiselect              # équivalent à --dev : base de test, sans danger
apiselect --dev        # idem, explicite
apiselect --prod        # vraie base 'apiselect' : demande le mot de passe
apiselect --prod --migrer   # applique les migrations sur la vraie base,
                             # après confirmation ; ne lance pas de serveur
```

## Base de données de test (`--dev`)

Pour tester l'outil de bout en bout (calcul d'index, calendrier, fiches PDF)
avec des données fictives sans jamais risquer de toucher aux vraies données,
`apiselect --dev` (ou `apiselect` sans option) lance le serveur sur une
seconde base PostgreSQL, `apiselect_dev`, séparée de la vraie base
`apiselect`. Le code reste le même (pas de branche Git) : seule la base
ciblée change, selon la variable d'environnement `DJANGO_DB_NAME` (absente
par défaut, jamais utilisée sans ce choix explicite).

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

## Vraie base (`--prod`)

`apiselect --prod` lance le serveur sur la vraie base `apiselect`, avec le
rôle PostgreSQL dédié `apiselect_prod`. Le script demande le mot de passe au
clavier (saisie masquée) : il n'est jamais écrit dans un fichier, jamais
passé en argument, jamais affiché ni journalisé, et il est effacé de
l'environnement à la sortie du script. Si l'authentification échoue, un
message clair s'affiche et le script s'arrête sans lancer le serveur.
Aucune migration n'est appliquée automatiquement en mode `--prod`, et le
bandeau « BASE DE TEST » n'apparaît pas — un avertissement « VRAIE BASE »
est affiché à la place dans le terminal.

Pour appliquer les migrations en attente sur la vraie base (sans lancer de
serveur) :

```bash
apiselect --prod --migrer
```

Le script demande le mot de passe, affiche la liste des migrations qui
seraient appliquées, rappelle qu'une sauvegarde de la vraie base doit
exister, puis demande de taper « oui » pour confirmer avant d'exécuter
`migrate`.

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
