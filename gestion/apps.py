from django.apps import AppConfig


class GestionConfig(AppConfig):
    """Pages visuelles de gestion du rucher (issue #41) : lit uniquement
    les modèles de gestion (Rucher, TypeRuche, Ruche, Colonie, Reine,
    ConfigurationColonie, EvenementColonie), définis dans `selection`
    pour l'instant. Ne doit jamais importer ni référencer un modèle, une
    vue, une table ou un gabarit propre à la sélection génétique
    (campagnes, mesures, cellules royales, critères, calendrier, vues
    SQL) — cf. CONTEXTE.md, règle de dépendance à sens unique."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'
    verbose_name = "Gestion du rucher"
