from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, OuterRef
from graph.models import Coureur, CoureurCategorie, ResultatCourse, Course

class Command(BaseCommand):
    help = 'Nettoie la base de données en supprimant les coureurs sans catégorie et les résultats de course orphelins'

    @transaction.atomic
    def handle(self, *args, **options):
        # Suppression des coureurs sans catégorie
        coureurs_sans_categorie = Coureur.objects.filter(
            ~Exists(CoureurCategorie.objects.filter(coureur=OuterRef('pk')))
        )
        nombre_coureurs_supprimes = coureurs_sans_categorie.delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Coureurs supprimés : {nombre_coureurs_supprimes}'))

        # Suppression des ResultatsCourse sans Coureur
        resultats_sans_coureur = ResultatCourse.objects.filter(coureur__isnull=True)
        nombre_resultats_sans_coureur = resultats_sans_coureur.delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Résultats sans coureur supprimés : {nombre_resultats_sans_coureur}'))

        # Suppression des ResultatsCourse sans Course
        resultats_sans_course = ResultatCourse.objects.filter(course__isnull=True)
        nombre_resultats_sans_course = resultats_sans_course.delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Résultats sans course supprimés : {nombre_resultats_sans_course}'))
        # Suppression des Courses sans ResultatCourse
        courses_sans_resultats = Course.objects.filter(
            ~Exists(ResultatCourse.objects.filter(course=OuterRef('pk')))
        )
        nombre_courses_supprimees = courses_sans_resultats.delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Courses sans résultats supprimées : {nombre_courses_supprimees}'))

        self.stdout.write(self.style.SUCCESS('Nettoyage de la base de données terminé avec succès.'))