# Dans un fichier management/commands/fusionner_coureurs.py
from django.core.management.base import BaseCommand
from graph.utils.fusionner_coureurs.FusionCoureurPremiereEtape import fusionner_et_defusionner_coureurs  # Assurez-vous d'importer correctement la fonction

class Command(BaseCommand):
    help = 'Fusionne les coureurs avec des prénoms numérotés'

    def handle(self, *args, **options):
        fusionner_et_defusionner_coureurs()
        self.stdout.write(self.style.SUCCESS('Fusion des coureurs terminée avec succès'))