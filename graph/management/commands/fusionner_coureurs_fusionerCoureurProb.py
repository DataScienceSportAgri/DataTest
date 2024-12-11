# Dans un fichier management/commands/fusionner_coureurs.py
from django.core.management.base import BaseCommand
from graph.utils.fusionner_coureurs.FusionCoureurIdentiqueProabiliste import fusion  # Assurez-vous d'importer correctement la fonction

class Command(BaseCommand):
    help = 'Fusionne les coureurs'

    def handle(self, *args, **options):
        fusion()
        self.stdout.write(self.style.SUCCESS('Fusion des coureurs terminée avec succès'))