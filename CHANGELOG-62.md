## Tests — volet stocks

### 18 oct. 2026

- Ajout de tests pour l'indicateur de stock bas : article sans seuil d'alerte n'est jamais signalé comme en stock bas (quel que soit son stock), et article dont le stock est exactement égal à son seuil n'est pas non plus signalé comme en stock bas (frontière fixée par les tests).
- Ajout de tests pour la validation des quantités dans les formulaires : quantité nulle ou négative refusée dans MouvementForm, quantité comptée négative refusée dans CorrectionStockForm, et vérification que les quantités positives/valides sont acceptées.
