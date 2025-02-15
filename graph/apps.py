from django.apps import AppConfig

class GraphConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'graph'

    def ready(self):
        print("GraphConfig is ready!")  # Ajoutez cette ligne pour le débogage