# Issue #52 — Tuile : signal « reine morte » compact (couronne barrée à la place de la pastille)

## Modifié

- `gestion/templates/gestion/_tuile_ruche.html` : sur la ligne de la
  reine d'une tuile d'accueil, suppression de la redondance signalée
  par l'issue. Il ne reste plus qu'un seul signal pour une reine morte
  confirmée sans remérage depuis (`tuile.observation_reine_morte_confirmee`,
  calculé par `gestion/views.py`, inchangé) : l'icône de couronne
  barrée (SVG inline existant, couleur d'alerte `#c62828`, déjà
  utilisée ailleurs dans le projet pour rester lisible en thème clair
  et sombre) **à la place de la pastille de marquage**, suivie de
  l'identifiant de la reine tel quel. Supprimés : la mention
  « (morte) » après l'identifiant et la ligne séparée « Reine morte »
  (paragraphe `tuile-signal-reine-morte`). Accessibilité conservée sur
  l'icône : `role="img"` + `aria-label="Reine morte confirmée"` et un
  `<title>` SVG (infobulle native au survol). La pastille de marquage
  (pleine/vide, issue #51) continue de s'afficher normalement quand la
  reine n'est pas morte ; la pastille orange des observations ouvertes
  (« Reine morte ? ») et la fiche colonie ne sont pas touchées. La
  tuile retrouve exactement la hauteur d'une tuile normale (une ligne
  de moins qu'avant).
- `gestion/static/gestion/style.css` : suppression des règles devenues
  inutiles (`.tuile-reine-morte .pastille-marquage`, `.etiquette-morte`,
  `.tuile-signal-reine-morte`) ; `.icone-reine-morte` conservée
  (couleur d'alerte de l'icône, désormais utilisée inline sur la ligne
  de la reine).
- `gestion/tests.py`, `SignalReineMorteTests.test_signal_affiche_sur_la_tuile_et_la_fiche` :
  adapté aux nouveaux libellés — vérifie que l'icône n'apparaît
  qu'une seule fois, que le libellé accessible « Reine morte
  confirmée » est présent, et que « (morte) », la ligne séparée et la
  pastille de marquage ont bien disparu de la tuile. Fiche colonie
  inchangée, toujours vérifiée.

Tests : `python manage.py test selection gestion` → 241 tests, OK
(base de test temporaire créée/détruite par Django, aucune base réelle
touchée).
