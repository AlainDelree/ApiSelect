# Issue #57 : Signaler visuellement un stock négatif, sans jamais bloquer la saisie

## Signalement visuel des stocks négatifs

### Modifications apportées

1. **Modèle `Article`** (`gestion/models.py`)
   - Ajout de la propriété `stock_negatif` : retourne `True` si `stock < 0`
   - Distinction claire avec `stock_bas` (qui dépend du seuil d'alerte)

2. **Signalement sur les articles** (`gestion/templates/gestion/stocks.html`, `gestion/static/gestion/style.css`)
   - Nouveau badge `badge-stock-negatif` avec fond violet (`#9c27b0`) et texte blanc
   - Affiché sur chaque article ayant un stock négatif dans la page Stocks
   - Coexiste avec le badge de stock bas si les deux conditions sont vraies

3. **Page d'accueil** (`gestion/views.py`, `gestion/templates/gestion/accueil.html`, `gestion/static/gestion/style.css`)
   - Nouveau bloc `bloc-stock-negatif` affichant tous les articles avec stock négatif
   - Style cohérent avec le bloc `bloc-stock-bas` existant
   - Lien vers la page Stocks filtrée sur les articles négatifs

4. **Page Stocks** (`gestion/views.py`, `gestion/templates/gestion/stocks.html`)
   - Ajout d'un filtre « Stock négatif seulement » pour n'afficher que les articles concernés
   - Le filtre est compatible avec les autres filtres (famille, rubrique, inactifs)

5. **Saisie des sorties** (`gestion/views.py`, `gestion/templates/gestion/mouvement_form.html`, `gestion/static/gestion/style.css`)
   - Avertissement affiché lors de l'ouverture du formulaire de sortie si celle-ci rendrait le stock négatif
   - Message clair : « Ce mouvement rendrait le stock négatif. L'enregistrement reste possible, mais une correction d'inventaire sera nécessaire. »
   - Style : fond jaune (`#ffc107`) avec bordure violette à gauche
   - **Aucun blocage** : la saisie est toujours autorisée

6. **Tests** (`gestion/tests.py`)
   - Nouvelle classe `StockNegatifTests` avec 15 tests couvrant :
     - La propriété `stock_negatif`
     - L'affichage des badges
     - Le bloc sur l'accueil
     - Le filtre dédié
     - L'avertissement à la saisie
     - L'autorisation d'enregistrement même avec stock négatif

## Choix techniques

- **Couleur du badge** : Violet (`#9c27b0`) pour se distinguer du rouge du stock bas (`#d9534f`)
- **Emplacement des signalements** :
  - Badge sur l'article : à côté du badge stock bas dans le template `stocks.html`
  - Bloc sur l'accueil : après le bloc stock bas, avant le bloc « À revérifier »
  - Avertissement : entre le stock actuel et le formulaire de mouvement
- **Pas de modification du modèle de données** : comme demandé, le signalement est purement visuel et ne bloque aucune opération
- **Compatibilité** : toutes les fonctionnalités existantes restent inchangées

## Rappel de la demande

Issue #57 demandait :
- Un indicateur sur l'article, distinct du signalement de stock bas ✅
- Sur la page des stocks, faire apparaître clairement les articles concernés ✅
- Sur la page d'accueil, les signaler au même titre que les stocks bas ✅
- Au moment de la saisie d'une sortie, informer que l'opération rend le stock négatif — sans empêcher l'enregistrement ✅
- Ne rien placer dans la sauvegarde du modèle ✅
- Ajouter des tests ✅
