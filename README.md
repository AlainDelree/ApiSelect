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
