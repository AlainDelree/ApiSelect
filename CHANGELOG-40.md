# Issue #40 — CONTEXTE.md : nouveau périmètre (gestion du rucher d'abord, sélection ensuite)

## Modifié

- `CONTEXTE.md` : nouvelle section « Périmètre : deux parties,
  dépendance à sens unique » qui décrit le découpage cible — gestion
  du rucher (ruchers, ruches, colonies, reines, et à construire :
  visites, récoltes, traitements, stocks) construite d'abord, puis
  sélection des reines (campagnes, cellules royales, critères,
  mesures, calendrier d'élevage, fiches PDF, résultats, diagnostic)
  réservée à Alain et reprise plus tard sans changement. Ajoute la
  règle de dépendance impérative (le code de gestion ne doit jamais
  dépendre d'un modèle/vue/table/gabarit de sélection, seule la
  sélection peut dépendre de la gestion) et la règle de portabilité
  pour tout nouveau code (pas de chemin en dur, pas de SQL propre à
  PostgreSQL, pas de dépendance à un script bash, en vue d'une future
  version Windows/SQLite) ainsi qu'une note précisant que
  l'environnement actuel reste PostgreSQL. Section « Règles de
  travail » conservée intacte. Sections « Sélection génétique »,
  « Calendrier d'élevage » et « Mode diagnostic » fusionnées et
  condensées, Vocabulaire et Stack légèrement raccourcis, pour tenir
  sous la limite de 4000 caractères (3996 caractères au final) tout
  en ajoutant le nouveau contenu. Mention de `Cours_Apiculture/`
  (jamais committé ni référencé dans une issue) conservée.
