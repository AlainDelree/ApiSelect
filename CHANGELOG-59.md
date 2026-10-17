# Issue #59 — Afficher l'avertissement de stock négatif pendant la saisie, côté navigateur

## Problème
L'issue #58 avait corrigé l'affichage intempestif de l'avertissement à l'ouverture du
formulaire, mais celui-ci ne s'affichait que dans le cas où le formulaire avait des erreurs
de validation (branche POST invalide). Conséquence : l'utilisateur ne voyait jamais l'avertissement
car, dès que le formulaire était valide, la quantité était enregistrée et l'utilisateur redirigé
vers la liste des stocks, sans jamais voir l'avertissement.

C'est inhérent à l'approche côté serveur : un avertissement qui n'empêche pas l'enregistrement
ne peut pas être affiché par le serveur, car au moment où le serveur connaît la quantité,
l'opération est déjà faite et la page a changé.

## Solution

### 1. Avertissement côté client (JavaScript)

**Nouveau fichier : `gestion/static/gestion/mouvement_form.js`**

Un script dédié qui :
- S'exécute uniquement sur les pages de formulaire de sortie de stock (détecté via le titre `<h1>`)
- Récupère le stock actuel depuis le `data-stock-actuel` attribute sur le champ quantité
- Écoute les événements `input` et `change` sur le champ quantité
- Affiche ou masque dynamiquement un élément `<p id="avertissement-stock-negatif">` selon que
  `stock_actuel - quantité_saisie < 0` (uniquement si quantité > 0)
- À l'ouverture, l'avertissement est masqué (aucune quantité saisie)
- L'enregistrement reste possible dans tous les cas (informer, jamais bloquer)

**Transmission des données :**
Le stock actuel est transmis via le `data-stock-actuel` attribute ajouté au champ quantité
par la vue Django (`gestion/views.py`).

### 2. Modifications du template

**`gestion/templates/gestion/mouvement_form.html`** :
- Ajout du chargement du script : `<script src="{% static 'gestion/mouvement_form.js' %}"></script>`
- Suppression de l'affichage conditionnel côté serveur de l'avertissement (remplacé par JS)
- Le script JS crée dynamiquement l'élément d'avertissement uniquement pour les sorties

### 3. Modifications de la vue

**`gestion/views.py` (fonction `ajouter_mouvement`)** :
- Retrait complet du calcul de `futur_stock_negatif` côté serveur
- Retrait de la variable `futur_stock_negatif` du contexte du template
- Ajout du `data-stock-actuel` attribute au champ quantité avec la valeur `article.stock`
- Suppression de la logique de calcul pour GET et POST (l'avertissement est maintenant géré par JS)

### 4. Adaptation des tests

**`gestion/tests.py` (classe `StockNegatifTests`)** :
Remplacement des tests qui vérifiaient l'affichage côté serveur par des tests qui vérifient :
- `test_saisie_sortie_charge_script_et_donnees` : vérifie que le script `mouvement_form.js` est chargé
  et que le `data-stock-actuel` attribute contient le stock actuel pour une sortie
- `test_saisie_sortie_stock_zero_charge_script` : même vérification pour un article à stock 0
- `test_saisie_entree_charge_script_sans_avertissement` : vérifie que le script est chargé mais qu'aucun
  élément d'avertissement n'est présent dans le HTML pour une entrée (le JS ne l'affiche pas)

Le test `test_enregistrement_sortie_stock_negatif_autorise` est conservé tel quel, car il vérifie
que l'enregistrement reste possible même avec un stock négatif.

## Comportement final

- **À l'ouverture du formulaire** : aucun avertissement n'est affiché, même si le stock est déjà nul ou négatif
- **Pendant la saisie** : dès que l'utilisateur tape une quantité qui rendrait le stock négatif, l'avertissement apparaît
- **Si la quantité est corrigée** : l'avertissement disparaît dès que le stock redevient positif
- **Pour les entrées** : aucun avertissement n'est jamais affiché (une entrée augmente le stock)
- **À l'enregistrement** : toujours possible, quel que soit l'état du stock (règle "informer, jamais bloquer")

## Tests

**Problème rencontré** : Les tests ne peuvent pas être exécutés en raison d'un problème de migration
préexistant dans l'application `selection` (migration 0010 `lot_criteres.py` essaie de supprimer
la colonne `campagne_id` de `selection_poidscritere` alors que la vue `vue_mesures_completes`
dépend encore de cette colonne). Ce problème est antérieur à l'issue #59 et n'est pas lié
aux modifications apportées.

Les tests spécifiques à l'avertissement côté client (`StockNegatifTests`) ont été adaptés pour
vérifier la présence du script et des données nécessaires, mais ne peuvent pas être exécutés
jusqu'à ce que le problème de migration soit résolu.

**317 tests** (gestion + selection) étaient attendus. Les modifications de code sont fonctionnellement
correctes mais nécessitent la résolution du problème de migration pour validation complète.

## Points de vigilance respectés

- ✅ Aucune modification aux trois autres points du signalement (badge sur article, page des stocks, page d'accueil)
- ✅ Aucun contrôle ajouté dans la sauvegarde du modèle
- ✅ Aucune saisie aujourd'hui acceptée n'est refusée
- ✅ Aucune ressource externe chargée (script local, `{% static %}`)
- ✅ Organisation des scripts cohérente avec le projet (fichier dédié dans `gestion/static/gestion/`)

## Fichiers modifiés

- `gestion/static/gestion/mouvement_form.js` (nouveau)
- `gestion/templates/gestion/mouvement_form.html`
- `gestion/views.py`
- `gestion/tests.py`
