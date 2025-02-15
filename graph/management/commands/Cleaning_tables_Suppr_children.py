from django.core.management.base import BaseCommand
from django.db import transaction
from graph.models import Coureur, CoureurCategorie, Categorie

class Command(BaseCommand):
    help = 'Nettoie les données des coureurs, leurs catégories et les catégories vides'

    @transaction.atomic
    def handle(self, *args, **options):
        # Suppression des coureurs sans résultats
        runners_to_delete = Coureur.objects.filter(resultatcourse__isnull=True)
        deleted_runners_count = runners_to_delete.count()
        runners_to_delete.delete()
        self.stdout.write(self.style.SUCCESS(f'Coureurs supprimés : {deleted_runners_count}'))

        # Suppression des entrées dans coureurscategorie
        # (se fait automatiquement grâce aux relations en cascade)

        # Suppression des catégories sans coureurs
        empty_categories = Categorie.objects.filter(coureurcategorie__isnull=True)
        deleted_categories_count = empty_categories.count()
        empty_categories.delete()
        self.stdout.write(self.style.SUCCESS(f'Catégories vides supprimées : {deleted_categories_count}'))

        self.stdout.write(self.style.SUCCESS('Nettoyage des données terminé avec succès'))