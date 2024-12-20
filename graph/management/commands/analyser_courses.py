from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Avg, Max, F, FloatField
from django.db.models.functions import Cast
from graph.models import Course  # Remplacez 'your_app' par le nom de votre application

class Command(BaseCommand):
    help = 'Analyse les courses pour détecter les aberrations de distance et de vitesse'

    def vitesse_moyenne_attendue(self, distance, is_trail=False):
        base_vitesse = 10.5 - (1.5 if is_trail else 0)
        reduction = (distance - 5000) * ((10.5 - 7.8) + (0.5 if is_trail else 0)) / 55000
        return base_vitesse - reduction

    def vitesse_max_attendue(self, distance, is_trail=False):
        base_vitesse = 22 - (1.5 if is_trail else 0)
        reduction = (distance - 5000) * ((22 - 18) + (0.5 if is_trail else 0)) / 55000
        return base_vitesse - reduction

    def vitesse_triathlon(self, distance):
        base_vitesse = 20
        reduction = (distance - 30000) / 30000
        return base_vitesse - reduction

    def handle(self, *args, **options):
        self.stdout.write(f"Base de données utilisée : {connection.settings_dict['NAME']}")
        self.stdout.write("Début de l'analyse des courses")

        courses = Course.objects.annotate(
            vitesse_moyenne=Avg(F('distance') / (Cast(F('resultatcourse__temps'), FloatField()) / 1000000) * 3.6),
            vitesse_max=Max(F('distance') / (Cast(F('resultatcourse__temps'), FloatField()) / 1000000) * 3.6)
        )
        self.stdout.write(self.style.SUCCESS(f'Nombre de courses : {courses.count()}'))

        aberrations = []

        for course in courses:
            is_triathlon = 'triathlon' in course.nom.lower()
            is_trail = 'trail' in course.nom.lower()

            if is_triathlon:
                vitesse_attendue = self.vitesse_triathlon(course.distance)
                vitesse_max_attendue_val = vitesse_attendue * 2

                diff_moyenne = course.vitesse_moyenne - vitesse_attendue
                diff_max_sup = course.vitesse_max - (vitesse_max_attendue_val + 3)
                diff_max_inf = (vitesse_max_attendue_val - 7) - course.vitesse_max

                if abs(diff_moyenne) > 3:
                    aberrations.append((abs(diff_moyenne), f"Course aberrante (triathlon - moyenne): {course.nom}, Distance: {course.distance}m, Écart: {diff_moyenne:.2f} km/h"))

                if diff_max_sup > 0:
                    aberrations.append((diff_max_sup, f"Course aberrante (triathlon - max sup): {course.nom}, Distance: {course.distance}m, Écart: +{diff_max_sup:.2f} km/h"))
                elif diff_max_inf > 0:
                    aberrations.append((diff_max_inf, f"Course aberrante (triathlon - max inf): {course.nom}, Distance: {course.distance}m, Écart: -{diff_max_inf:.2f} km/h"))

            else:
                vitesse_attendue = self.vitesse_moyenne_attendue(course.distance, is_trail)
                vitesse_max_attendue_val = self.vitesse_max_attendue(course.distance, is_trail)

                diff_moyenne = course.vitesse_moyenne - vitesse_attendue
                tolerance = 3 if is_trail else 2
                if abs(diff_moyenne) >= tolerance:
                    aberrations.append((abs(diff_moyenne), f"Course aberrante (moyenne): {course.nom}, Distance: {course.distance}m, Écart: {diff_moyenne:.2f} km/h"))

                diff_max_sup = course.vitesse_max - (vitesse_max_attendue_val + 2)
                if diff_max_sup >= 0:
                    aberrations.append((diff_max_sup, f"Course aberrante (max sup): {course.nom}, Distance: {course.distance}m, Écart: +{diff_max_sup:.2f} km/h"))

                diff_max_inf = (vitesse_max_attendue_val - 5) - course.vitesse_max
                if diff_max_inf > 0:
                    aberrations.append((diff_max_inf, f"Course aberrante (max inf): {course.nom}, Distance: {course.distance}m, Écart: -{diff_max_inf:.2f} km/h"))

        # Trier les aberrations par ordre décroissant d'écart
        aberrations.sort(key=lambda x: x[0], reverse=True)

        # Afficher les aberrations triées
        for _, message in aberrations:
            self.stdout.write(self.style.WARNING(message))

        self.stdout.write(self.style.SUCCESS(f"\nNombre total de courses aberrantes : {len(aberrations)}"))
        self.stdout.write("Fin de l'analyse des courses")
