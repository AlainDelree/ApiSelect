from django.conf import settings


def base_de_test_active(request):
    """Expose BASE_DE_TEST_ACTIVE à tous les templates (admin Django ET
    vues personnalisées), pour le bandeau d'avertissement de la base de
    test (issue #12). Lit settings.BASE_DE_TEST_ACTIVE, calculé une seule
    fois au démarrage à partir du nom de base effectivement ciblé — pas
    une détection fragile côté template.
    """
    return {"BASE_DE_TEST_ACTIVE": settings.BASE_DE_TEST_ACTIVE}
