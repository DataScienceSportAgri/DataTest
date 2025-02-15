from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from graph.models import Categorie, CoureurCategorie


class Command(BaseCommand):
    help = 'Met à jour les catégories, supprime les doublons et met à jour les références'

    @transaction.atomic
    def handle(self, *args, **options):
        categories_to_update = {
            ' SEM': {'nom': 'SEM', 'age': '23-34', 'sexe': 'M', 'type': 'Personne'},
            ' M0M': {'nom': 'M0M', 'age': '35-39', 'sexe': 'M', 'type': 'Personne'},
            ' ESM': {'nom': 'ESM', 'age': '20-22', 'sexe': 'M', 'type': 'Personne'},
            ' M1M': {'nom': 'M1M', 'age': '40-44', 'sexe': 'M', 'type': 'Personne'},
            ' M3M': {'nom': 'M3M', 'age': '50-54', 'sexe': 'M', 'type': 'Personne'},
            ' M2M': {'nom': 'M2M', 'age': '45-49', 'sexe': 'M', 'type': 'Personne'},
            ' M5M': {'nom': 'M5M', 'age': '60-64', 'sexe': 'M', 'type': 'Personne'},
            ' M4M': {'nom': 'M4M', 'age': '55-59', 'sexe': 'M', 'type': 'Personne'},
            ' SEF': {'nom': 'SEF', 'age': '23-34', 'sexe': 'F', 'type': 'Personne'},
            ' ESF': {'nom': 'ESF', 'age': '20-22', 'sexe': 'F', 'type': 'Personne'},
            ' M0F': {'nom': 'M0F', 'age': '35-39', 'sexe': 'F', 'type': 'Personne'},
            ' M3F': {'nom': 'M3F', 'age': '50-54', 'sexe': 'F', 'type': 'Personne'},
            ' M1F': {'nom': 'M1F', 'age': '40-44', 'sexe': 'F', 'type': 'Personne'},
            ' JUM': {'nom': 'JUM', 'age': '18-19', 'sexe': 'M', 'type': 'Personne'},
            ' M2F': {'nom': 'M2F', 'age': '45-49', 'sexe': 'F', 'type': 'Personne'},
            ' M7M': {'nom': 'M7M', 'age': '70-74', 'sexe': 'M', 'type': 'Personne'},
            ' M5F': {'nom': 'M5F', 'age': '60-64', 'sexe': 'F', 'type': 'Personne'},
            ' M8M': {'nom': 'M8M', 'age': '75-79', 'sexe': 'M', 'type': 'Personne'},
            ' M6M': {'nom': 'M6M', 'age': '65-69', 'sexe': 'M', 'type': 'Personne'},
            ' M4F': {'nom': 'M4F', 'age': '55-59', 'sexe': 'F', 'type': 'Personne'},
            ' JUF': {'nom': 'JUF', 'age': '18-19', 'sexe': 'F', 'type': 'Personne'},
            ' M6F': {'nom': 'M6F', 'age': '65-69', 'sexe': 'F', 'type': 'Personne'},
            ' M7F': {'nom': 'M7F', 'age': '70-74', 'sexe': 'F', 'type': 'Personne'},
            ' M9M': {'nom': 'M9M', 'age': '80+', 'sexe': 'M', 'type': 'Personne'},
        }

        for old_nom, new_data in categories_to_update.items():
            try:
                # Essayer de trouver la catégorie avec l'espace
                categorie = Categorie.objects.get(nom=old_nom)

                # Vérifier si une catégorie sans espace existe déjà
                existing_categorie = Categorie.objects.filter(nom=new_data['nom']).first()

                if existing_categorie:
                    # Mettre à jour les références dans CategorieCoureur
                    CoureurCategorie.objects.filter(categorie=categorie).update(categorie=existing_categorie)

                    # Supprimer la catégorie avec l'espace
                    categorie.delete()
                    self.stdout.write(self.style.SUCCESS(f"Catégorie '{old_nom}' supprimée et références mises à jour"))
                else:
                    # Mettre à jour la catégorie existante
                    Categorie.objects.filter(nom=old_nom).update(**new_data)
                    self.stdout.write(self.style.SUCCESS(f"Catégorie '{old_nom}' mise à jour"))

            except Categorie.DoesNotExist:
                # Si la catégorie n'existe pas, la créer
                Categorie.objects.create(**new_data)
                self.stdout.write(self.style.SUCCESS(f"Nouvelle catégorie '{new_data['nom']}' créée"))

        self.stdout.write(self.style.SUCCESS('Mise à jour des catégories terminée'))