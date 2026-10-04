"""
URL configuration for apiselect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from selection.views import admin_index_avec_tableau

urlpatterns = [
    # Écran d'accueil visuel de gestion du rucher (issue #41), à la
    # place de l'ancienne redirection directe vers l'admin.
    path('', include('gestion.urls')),
    # Intercepte uniquement l'URL exacte 'admin/' pour y afficher le
    # tableau de résultats de sélection (issue #38) ; toutes les autres
    # URL admin/... retombent sur admin.site.urls juste après, inchangé.
    path('admin/', admin.site.admin_view(admin_index_avec_tableau)),
    path('admin/', admin.site.urls),
    path('selection/', include('selection.urls')),
]
