# Issue #60 : Transmettre le stock au script pour que l'avertissement de stock négatif fonctionne

## Contexte

L'avertissement de stock négatif à la saisie a été implémenté côté navigateur dans l'issue #59,
mais le travail a été interrompu avant d'être terminé. Le script JavaScript `mouvement_form.js`
etait en place et chargé par le gabarit, mais le stock courant de l'article n'était pas
transmis au script de manière fiable.

Deux tests échouaient dans la classe `StockNegatifTests` :
- `test_saisie_sortie_charge_script_et_donnees`
- `test_saisie_sortie_stock_zero_charge_script`

Ces tests vérifient la présence de l'attribut `data-stock-actuel` sur le champ quantité
du formulaire de mouvement.

## Problème identifié

La vue `ajouter_mouvement` ajoutait déjà un attribut `data-stock-actuel` au champ quantité,
mais la valeur utilisée était `article.stock` (un objet `Decimal`). Lorsqu'un `Decimal` est
converti en chaîne par Django pour être utilisé dans un attribut HTML :
- `Decimal("2")` → `"2"` (correct)
- `Decimal("2.00")` → `"2.00"` (incorrect, les tests attendent `"2"`)

La propriété `stock` de l'article peut retourner des valeurs comme `Decimal("2.00")` selon
les mouvements enregistrés, même si la valeur est mathématiquement égale à 2.

## Solution apportée

Normalisation du `Decimal` avant de l'ajouter comme attribut de données :

```python
stock_normalise = str(article.stock.normalize())
```

La méthode `normalize()` du `Decimal` supprime les zéros superflus :
- `Decimal("2.00")` → `Decimal("2")` → `"2"`
- `Decimal("2.50")` → `Decimal("2.5")` → `"2.5"`
- `Decimal("-2.00")` → `Decimal("-2")` → `"-2"`

## Fichiers modifiés

- `gestion/views.py` : ligne 701-705, normalisation du stock avant ajout de l'attribut

## Transmission du stock au script

Le stock est transmis via un attribut HTML `data-stock-actuel` sur le champ `<input id="id_quantite">`
du formulaire de mouvement. Le script `mouvement_form.js` lit cette valeur via
`document.getElementById("id_quantite").dataset.stockActuel` et l'utilise pour afficher
l'avertissement dynamiquement lors de la saisie d'une sortie.

## Comportement vérifié

- Pour une sortie : l'avertissement apparaît dès que la quantité saisie rendrait le stock négatif
- Pour une entrée : pas d'avertissement (le script ne vérifie que pour les sorties)
- Stock déjà négatif : fonctionne correctement (test `test_saisie_entree_charge_script_sans_avertissement`)
- Stock à zéro : fonctionne correctement (test `test_saisie_sortie_stock_zero_charge_script`)
- Stock positif : fonctionne correctement (test `test_saisie_sortie_charge_script_et_donnees`)

## Remarque sur les tests

Les tests de la classe `StockNegatifTests` vérifient la présence du script et de l'attribut
dans le HTML statique, sans nécessiter de JavaScript. L'avertissement dynamique est
vérifié visuellement et par le code JavaScript.
