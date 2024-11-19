from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Commande de test'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('La commande de test fonctionne!'))