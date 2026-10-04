"""Connexion automatique en usage strictement local (issue #35).

ApiSelect est mono-utilisateur et n'est accessible qu'en local (127.0.0.1
/ ::1) via `apiselect` ou `apiselect --dev`. Le formulaire de connexion de
l'admin Django n'apporte aucune sécurité utile dans ce contexte et crée de
la friction à chaque ouverture : ce middleware connecte automatiquement un
compte existant quand la requête n'est pas déjà authentifiée et provient
de la machine locale. Toute autre provenance garde le comportement Django
normal (page de login).
"""
from django.contrib.auth import get_user_model, login

ADRESSES_LOCALES = ('127.0.0.1', '::1')

NOM_UTILISATEUR_LOCAL = 'local'


class ConnexionAutomatiqueLocaleMiddleware:
    """Doit être placé juste après AuthenticationMiddleware dans
    MIDDLEWARE : s'appuie sur request.user déjà résolu par celui-ci."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            not request.user.is_authenticated
            and request.META.get('REMOTE_ADDR') in ADRESSES_LOCALES
        ):
            utilisateur = self._obtenir_ou_creer_utilisateur_local()
            login(
                request, utilisateur,
                backend='django.contrib.auth.backends.ModelBackend',
            )
        return self.get_response(request)

    @staticmethod
    def _obtenir_ou_creer_utilisateur_local():
        UserModel = get_user_model()
        superutilisateur = UserModel.objects.filter(
            is_superuser=True, is_active=True,
        ).order_by('pk').first()
        if superutilisateur is not None:
            return superutilisateur

        # Aucun superutilisateur dans cette base : on en crée un, sans
        # mot de passe utilisable (aucune connexion par formulaire
        # possible avec ce compte, seule la connexion auto locale marche).
        utilisateur = UserModel.objects.create(
            username=NOM_UTILISATEUR_LOCAL,
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )
        utilisateur.set_unusable_password()
        utilisateur.save(update_fields=['password'])
        return utilisateur
