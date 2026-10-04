## Lanceur apiselect : base de test par défaut, mode --prod avec mot de passe demandé au clavier (issue #46)

- `bin/apiselect` : `apiselect` (sans option) et `apiselect --dev` ciblent
  désormais tous deux la base de test `apiselect_dev` (comportement
  inchangé de `--dev`). `apiselect --prod` cible la vraie base `apiselect`
  avec le rôle `apiselect_prod` ; mot de passe demandé au clavier (saisie
  masquée), jamais écrit sur disque ni journalisé, transmis uniquement au
  process du serveur via variable d'environnement effacée à la sortie du
  script. Échec d'authentification détecté avant lancement du serveur,
  message clair, arrêt propre. `apiselect --prod --migrer` affiche le plan
  de migration, rappelle la nécessité d'une sauvegarde, demande
  confirmation ("oui"), applique les migrations sur la vraie base sans
  lancer de serveur.
- Page ouverte au démarrage : racine du site (`/`) au lieu de `/admin/`.
- Dossier du projet déduit de l'emplacement réel du script (lien
  symbolique résolu), plus de chemin en dur `/home/alain/ApiSelect`.
- `README.md` : usage des trois formes de commande, section dédiée au
  mode `--prod`.
- `CONTEXTE.md` : règle ajoutée (vraie base protégée par un mot de passe
  inconnu de CCL, jamais recherché ni deviné, `--prod`/`--migrer` jamais
  lancés par CCL) ; autres passages condensés pour rester sous 4000
  caractères.
