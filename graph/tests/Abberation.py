from django.db import connection
from django.db.models import Avg, Max, F
from django.db.models.functions import Cast
from django.db.models import FloatField
from graph.models import Course, ResultatCourse

def analyser_courses():
    # Fonction pour calculer la vitesse moyenne attendue
    def vitesse_moyenne_attendue(distance):
        return 10.5 - (distance - 5000) * (10.5 - 7.8) / 55000

    # Fonction pour calculer la vitesse maximale attendue
    def vitesse_max_attendue(distance):
        return 22 - (distance - 5000) * (22 - 18) / 55000

    # Récupérer toutes les courses avec leur vitesse moyenne
    courses = Course.objects.annotate(
        vitesse_moyenne=Avg(F('resultatcourse__distance') / Cast('resultatcourse__temps', FloatField()) * 3.6),
        vitesse_max=Max(F('resultatcourse__distance') / Cast('resultatcourse__temps', FloatField()) * 3.6)
    )

    # Analyser chaque course
    for course in courses:
        vitesse_attendue = vitesse_moyenne_attendue(course.distance)
        vitesse_max_attendue_val = vitesse_max_attendue(course.distance)

        # Vérifier la vitesse moyenne
        if abs(course.vitesse_moyenne - vitesse_attendue) > 2:
            mention = "sup" if course.vitesse_moyenne > vitesse_attendue else "inf"
            print(f"Course aberrante (moyenne): {course.nom}, Distance: {course.distance}m, Mention: {mention} moyenne")

        # Vérifier la vitesse maximale
        if course.vitesse_max > vitesse_max_attendue_val + 2 or course.vitesse_max < vitesse_max_attendue_val - 5:
            mention = "sup" if course.vitesse_max > vitesse_max_attendue_val + 2 else "inf"
            print(f"Course aberrante (max): {course.nom}, Distance: {course.distance}m, Mention: {mention} max")

            # Récupérer les résultats concernés
            resultats_aberrants = ResultatCourse.objects.filter(
                course=course,
                distance=F('course__distance'),
                temps__lt=F('distance') / (vitesse_max_attendue_val * 1000 / 3600)
            ) if mention == "sup" else ResultatCourse.objects.filter(
                course=course,
                distance=F('course__distance'),
                temps__gt=F('distance') / ((vitesse_max_attendue_val - 5) * 1000 / 3600)
            ).order_by('temps')[:1]

            for resultat in resultats_aberrants:
                print(f"  Résultat aberrant: ID: {resultat.id}, Temps: {resultat.temps}s")

if __name__ == "__main__":
    analyser_courses()
