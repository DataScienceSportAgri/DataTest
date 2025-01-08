from django.core.management.base import BaseCommand
from graph.models import Course, Coureur
from django.db.models import F
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Met en forme les noms marsiens des courses et des coureurs'

    def handle(self, *args, **options):
        self.format_courses()
        self.format_coureurs()
        self.stdout.write(self.style.SUCCESS('Mise en forme terminée avec succès'))

    def format_courses(self):
        courses = Course.objects.all()
        with tqdm(total=courses.count(), desc="Formatage des noms de courses") as pbar:
            for course in courses:
                if course.nom_marsien:
                    course.nom_marsien = course.nom_marsien.capitalize()
                    course.save(update_fields=['nom_marsien'])
                pbar.update(1)

    def format_coureurs(self):
        coureurs = Coureur.objects.all()
        with tqdm(total=coureurs.count(), desc="Formatage des noms de coureurs") as pbar:
            for coureur in coureurs:
                if coureur.nom_marsien:
                    coureur.nom_marsien = coureur.nom_marsien.upper()
                if coureur.prenom_marsien:
                    coureur.prenom_marsien = coureur.prenom_marsien.capitalize()
                coureur.save(update_fields=['nom_marsien', 'prenom_marsien'])
                pbar.update(1)
