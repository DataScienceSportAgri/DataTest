from django.core.management.base import BaseCommand
from django.db import transaction
from graph.models import Categorie

class Command(BaseCommand):
    help = 'Met à jour les catégories avec les nouvelles informations'

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {
            'BAF': {'age': '0-6', 'sexe': 'F', 'type': 'Personne'},
            'BAG': {'age': '0-6', 'sexe': 'Mixte', 'type': 'Équipe'},
            'BBF': {'age': '0-6', 'sexe': 'F', 'type': 'Personne'},
            'BBM': {'age': '0-6', 'sexe': 'M', 'type': 'Personne'},
            'BEF': {'age': '12-13', 'sexe': 'F', 'type': 'Personne'},
            'BEM': {'age': '12-13', 'sexe': 'M', 'type': 'Personne'},
            'CAF': {'age': '16-17', 'sexe': 'F', 'type': 'Personne'},
            'CAH': {'age': '16-17', 'sexe': 'M', 'type': 'Personne'},
            'CAM': {'age': '16-17', 'sexe': 'M', 'type': 'Personne'},
            'EAF': {'age': '7-9', 'sexe': 'F', 'type': 'Personne'},
            'EAG': {'age': '7-9', 'sexe': 'Mixte', 'type': 'Équipe'},
            'EAM': {'age': '7-9', 'sexe': 'M', 'type': 'Personne'},
            'MIF': {'age': '14-15', 'sexe': 'F', 'type': 'Personne'},
            'MIM': {'age': '14-15', 'sexe': 'M', 'type': 'Personne'},
            'POF': {'age': '10-11', 'sexe': 'F', 'type': 'Personne'},
            'POM': {'age': '10-11', 'sexe': 'M', 'type': 'Personne'},
            'MAF': {'age': '35+', 'sexe': 'F', 'type': 'Personne'},
            'MAM': {'age': '35+', 'sexe': 'M', 'type': 'Personne'},
            'V1F': {'age': '35-39', 'sexe': 'F', 'type': 'Personne'},
            'V1M': {'age': '35-39', 'sexe': 'M', 'type': 'Personne'},
            'V2F': {'age': '40-44', 'sexe': 'F', 'type': 'Personne'},
            'V2M': {'age': '40-44', 'sexe': 'M', 'type': 'Personne'},
            'V3F': {'age': '45-49', 'sexe': 'F', 'type': 'Personne'},
            'V3M': {'age': '45-49', 'sexe': 'M', 'type': 'Personne'},
            'V4F': {'age': '50-54', 'sexe': 'F', 'type': 'Personne'},
            'V4M': {'age': '50-54', 'sexe': 'M', 'type': 'Personne'},
            'V5F': {'age': '55-59', 'sexe': 'F', 'type': 'Personne'},
            'V5M': {'age': '55-59', 'sexe': 'M', 'type': 'Personne'},
            'V6M': {'age': '60-64', 'sexe': 'M', 'type': 'Personne'},
            'V7F': {'age': '65-69', 'sexe': 'F', 'type': 'Personne'},
            'V7M': {'age': '65-69', 'sexe': 'M', 'type': 'Personne'},
            'V8M': {'age': '70-74', 'sexe': 'M', 'type': 'Personne'},
            'Unknown': {'age': 'Inconnu', 'sexe': 'Inconnu', 'type': 'Inconnu'},
            'REF': {'age': 'Inconnu', 'sexe': 'F', 'type': 'Personne'},
            'REH': {'age': 'Inconnu', 'sexe': 'H', 'type': 'Personne'},
            'REM': {'age': 'Inconnu', 'sexe': 'M', 'type': 'Personne'},
            'S3M': {'age': 'Inconnu', 'sexe': 'M', 'type': 'Personne'},
            'S4M': {'age': 'Inconnu', 'sexe': 'M', 'type': 'Personne'},
            'S2M': {'age': 'Inconnu', 'sexe': 'M', 'type': 'Personne'},
            'S1F': {'age': 'Inconnu', 'sexe': 'F', 'type': 'Personne'},
            'S1M': {'age': 'Inconnu', 'sexe': 'M', 'type': 'Personne'},
            'S3F': {'age': 'Inconnu', 'sexe': 'F', 'type': 'Personne'},
            'S2F': {'age': 'Inconnu', 'sexe': 'F', 'type': 'Personne'},
            'SEH': {'age': '23-34', 'sexe': 'H', 'type': 'Personne'},
            'MOM': {'age': '35-39', 'sexe': 'M', 'type': 'Personne'},
            'MOF': {'age': '35-39', 'sexe': 'F', 'type': 'Personne'},
            'S4F': {'age': 'Inconnu', 'sexe': 'F', 'type': 'Personne'},
            'DUH': {'age': 'Inconnu', 'sexe': 'H', 'type': 'Équipe'},
            'HAN': {'age': 'Inconnu', 'sexe': 'Inconnu', 'type': 'Personne'},
            'DUO': {'age': 'Inconnu', 'sexe': 'Mixte', 'type': 'Équipe'},
            'V5H': {'age': '55-59', 'sexe': 'H', 'type': 'Personne'},
            'ENF': {'age': '7-11', 'sexe': 'Mixte', 'type': 'Personne'},
            'MHO': {'age': 'Inconnu', 'sexe': 'H', 'type': 'Équipe'},
            'MFE': {'age': 'Inconnu', 'sexe': 'F', 'type': 'Équipe'},
            'IND': {'age': 'Inconnu', 'sexe': 'Inconnu', 'type': 'Personne'},
            'DUM': {'age': 'Inconnu', 'sexe': 'M', 'type': 'Équipe'},
            'nan': {'age': 'Inconnu', 'sexe': 'Inconnu', 'type': 'Inconnu'},

            'SEM': { 'age': '23-34', 'sexe': 'M', 'type': 'Personne'},
            'M0M': {'age': '35-39', 'sexe': 'M', 'type': 'Personne'},
            'ESM': {'age': '20-22', 'sexe': 'M', 'type': 'Personne'},
            'M1M': { 'age': '40-44', 'sexe': 'M', 'type': 'Personne'},
            'M3M': {'age': '50-54', 'sexe': 'M', 'type': 'Personne'},
            'M2M': {'age': '45-49', 'sexe': 'M', 'type': 'Personne'},
            'M5M': {'age': '60-64', 'sexe': 'M', 'type': 'Personne'},
            'M4M': {'age': '55-59', 'sexe': 'M', 'type': 'Personne'},
            'SEF': {'age': '23-34', 'sexe': 'F', 'type': 'Personne'},
            'ESF': {'age': '20-22', 'sexe': 'F', 'type': 'Personne'},
            'M0F': {'age': '35-39', 'sexe': 'F', 'type': 'Personne'},
            'M3F': {'age': '50-54', 'sexe': 'F', 'type': 'Personne'},
            'M1F': {'age': '40-44', 'sexe': 'F', 'type': 'Personne'},
            'JUM': {'age': '18-19', 'sexe': 'M', 'type': 'Personne'},
            'M2F': {'age': '45-49', 'sexe': 'F', 'type': 'Personne'},
            'M7M': {'age': '70-74', 'sexe': 'M', 'type': 'Personne'},
            'M5F': {'age': '60-64', 'sexe': 'F', 'type': 'Personne'},
            'M8M': {'age': '75-79', 'sexe': 'M', 'type': 'Personne'},
            'M6M': {'age': '65-69', 'sexe': 'M', 'type': 'Personne'},
            'M4F': {'age': '55-59', 'sexe': 'F', 'type': 'Personne'},
            'JUF': {'age': '18-19', 'sexe': 'F', 'type': 'Personne'},
            'M6F': {'age': '65-69', 'sexe': 'F', 'type': 'Personne'},
            'M7F': {'age': '70-74', 'sexe': 'F', 'type': 'Personne'},
            'M9M': {'age': '80+', 'sexe': 'M', 'type': 'Personne'},
        }


        updated_count = 0
        for nom, info in categories.items():
            categorie, created = Categorie.objects.update_or_create(
                nom=nom,
                defaults={
                    'age': info['age'],
                    'sexe': info['sexe'],
                    'type': info['type']
                }
            )
            if not created:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Catégories mises à jour : {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'Nouvelles catégories créées : {len(categories) - updated_count}'))
