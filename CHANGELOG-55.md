# Issue #55 — Stocks, étape 1 : matériel et consommables (catalogue, mouvements, stock bas, catalogue de départ)

## Ajouté

- `gestion/models.py` : `FamilleMateriel` (petit référentiel
  modifiable), `Article` (nom, rubrique, nature matériel durable /
  consommable, unité libre, seuil d'alerte facultatif, actif,
  familles compatibles, notes), `MouvementStock` (article, date,
  quantité signée, motif, note facultative, et — prévus sans être
  exploités à cette étape — numéro de lot et date de péremption pour
  l'étape 2 « Traitements »). Le stock d'un article n'est jamais
  stocké : toujours recalculé comme la somme de ses mouvements
  (`Article.stock`, propriété). `MouvementStock.article` est protégé
  (`on_delete=PROTECT`) : un article avec au moins un mouvement ne
  peut pas être supprimé, y compris depuis l'administration.
- `gestion/migrations/0003_stocks.py` : migration purement additive,
  écrite à la main (aucune commande `makemigrations` lancée, conforme
  à la contrainte « aucune commande `manage.py` autre que `test` »).
  Ne crée aucune donnée.
- `gestion/catalogue_stocks.py` : `CATALOGUE_DEPART` (77 articles,
  transcription de la liste de l'issue) et
  `charger_catalogue_depart()` — crée les articles manquants (reconnus
  par nom + rubrique), ne modifie ni ne supprime jamais un article
  existant, ne crée aucun mouvement, idempotent.
- `gestion/forms.py` : `ArticleForm` (formulaire unique, création et
  modification — `actif` volontairement absent, géré par le bouton
  « Désactiver »), `MouvementForm` (quantité toujours positive, signe
  appliqué dans la vue selon le bouton utilisé), `CorrectionStockForm`
  (quantité réellement comptée).
- `gestion/views.py` : `stocks` (page « Stocks », groupée par
  rubrique, filtres famille / rubrique / stock bas seulement /
  afficher les inactifs), `ajouter_article` / `modifier_article`
  (formulaire unique), `desactiver_article`, `supprimer_article`
  (bloqué s'il existe un mouvement), `ajouter_mouvement` (panneau
  « − » / « + », motif proposé selon le sens, modifiable),
  `corriger_stock` (mouvement de correction = différence avec la
  quantité comptée, aucun mouvement créé si la différence est nulle),
  `historique_mouvements`, `annuler_mouvement` (confirmation
  explicite), `charger_catalogue_depart` (confirmation explicite,
  jamais automatique).
- `gestion/urls.py` : routes `stocks/...` correspondantes.
- `gestion/admin.py` : `FamilleMaterielAdmin` (référentiel modifiable,
  ajout autorisé), `ArticleAdmin` et `MouvementStockAdmin`
  (consultation et correction exceptionnelle, ajout refusé — la
  saisie se fait par l'interface visuelle, cf. `CONTEXTE.md`).
- Gabarits : `stocks.html`, `article_form.html`,
  `confirmer_suppression_article.html`, `mouvement_form.html`,
  `correction_stock_form.html`, `historique_mouvements.html`,
  `confirmer_annulation_mouvement.html`,
  `confirmer_catalogue_depart.html`, `catalogue_depart_resultat.html`.
- Lien « Stocks → » dans l'en-tête de l'accueil ; bloc « Stock bas »
  (articles actifs sous leur seuil, absent s'il n'y en a aucun, avec
  lien vers la page « Stocks » filtrée).
- `gestion/static/gestion/style.css` : styles de la page « Stocks »
  (filtres, liste groupée par rubrique, badge « Stock bas », boutons
  « − » / « + », bouton « Charger le catalogue de départ »).
- Tests (`gestion/tests.py`) : calcul du stock par somme de
  mouvements, mouvements « − » et « + » depuis le panneau, motif
  proposé selon le sens, correction d'inventaire (avec et sans
  différence), badge et bloc « Stock bas » (présent sous le seuil,
  absent au-dessus, absent sans seuil), filtre par famille (pièce
  compatible avec deux familles visible pour chacune), articles
  inactifs masqués par défaut et visibles avec le filtre, suppression
  d'article refusée s'il a un mouvement, annulation d'un mouvement
  derrière confirmation, chargement du catalogue de départ (articles
  manquants créés, article existant jamais modifié, aucun mouvement
  créé, résultat identique relancé deux fois, pièce commune à deux
  familles), formulaire d'article mêmes champs création/modification,
  ajout refusé dans l'admin pour `Article` et `MouvementStock`, ajout
  autorisé pour `FamilleMateriel`.

## Adaptation de la liste de départ

Aucune : la liste de 77 articles transcrite dans
`gestion/catalogue_stocks.py` suit exactement l'énoncé de l'issue
(rubriques, familles, nature matériel durable / consommable, unités
« bobine » / « feuille » / « flacon » précisées, articles Miniplus et
« bigoudi » inactifs). Les formats de pots et de seaux ne sont pas
déclinés, comme demandé — Alain les dupliquera lui-même dans
l'application.

## Non modifié

- Aucune dépendance nouvelle de `gestion` vers `selection` : les
  modèles de stocks n'importent que des types de champs standard de
  l'ORM.
- Pas de SQL propre à PostgreSQL ; stock calculé par agrégation ORM
  (`Sum`).
