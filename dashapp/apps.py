from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from . import settings

class DashappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashapp'

    def ready(self):
        self._verify_dash_config()
        from . import dash_app # Import APRÈS vérification

    def _verify_dash_config(self):
        """Vérification approfondie de la configuration"""
        required_keys = ['LISTE_DATES', 'LISTE_DATES_BOULINSARD', 'COUNTRIES']

        if not hasattr(settings, 'DASH_CONFIG'):
            raise ImproperlyConfigured("La configuration DASH_CONFIG est manquante dans les paramètres")

        missing = [key for key in required_keys if key not in settings.DASH_CONFIG]
        if missing:
            raise ImproperlyConfigured(
                f"Clés manquantes dans DASH_CONFIG : {', '.join(missing)}"
            )
#yeah