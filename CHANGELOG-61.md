## Issue #61 — Mettre à jour CONTEXTE.md après le signalement des stocks négatifs

### 17 octobre 2026

## Modifications

Mise à jour de `CONTEXTE.md` pour refléter les évolutions récentes du projet.

### 1. Signalement des stocks négatifs

Ajout d'une section dédiée décrivant le comportement actuel du volet stocks :
- Un stock négatif est signalé sur l'article (badge violet), sur la page des stocks (filtre dédié),
  sur la page d'accueil (bloc dédié), et pendant la saisie d'une sortie (avertissement dynamique).
- Principe retenu : **informer, jamais bloquer** — une sortie supérieure au stock disponible reste
  enregistrable ; le stock négatif est un symptôme à corriger par un inventaire, pas une saisie à refuser.
- Aucun contrôle n'est placé dans la sauvegarde du modèle, afin que les corrections d'inventaire,
  les chargements de catalogue et les migrations ne soient jamais entravés.
- L'avertissement pendant la saisie est géré côté navigateur, le stock étant transmis à la page,
  car un avertissement qui n'empêche pas l'enregistrement ne peut pas être produit par le serveur.

### 2. Règles de travail ajoutées

- **Environnement des tests** : Les tests doivent être lancés depuis l'environnement virtuel du dépôt
  principal, `~/ApiSelect/venv`. Commande à utiliser : `source ~/ApiSelect/venv/bin/activate && python manage.py test selection gestion`
  (ou depuis le répertoire du dépôt : `. ~/ApiSelect/venv/bin/activate && python manage.py test selection gestion`).

- **Convention de changelog** : Chaque issue dépose un fichier de changelog séparé à la racine, nommé
  `CHANGELOG-<N>.md` d'après son numéro, qui est ensuite fusionné dans `CHANGELOG.md`.
  Format des entrées : titre de niveau 2 (`##`), avec la date en sous-titre (niveau 3 ou 4),
  en tête du fichier principal. Les entrées doivent être homogènes en structure.

## Fichiers modifiés

- `CONTEXTE.md` : sections "Règles de travail" et nouvelle section "Stocks" ajoutées.
- `CHANGELOG-61.md` : ce fichier.
