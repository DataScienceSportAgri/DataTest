from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from ...models import Course, ResultatCourse

class Command(BaseCommand):
    help = 'Supprime les courses en double et les résultats orphelins'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Début de l'opération..."))

        # Étape 1: Identifier les doublons
        self.identify_duplicates()

        # Étape 2: Supprimer les doublons
        self.delete_duplicates()

        # Étape 3: Supprimer les résultats orphelins
        self.delete_orphan_results()

        self.stdout.write(self.style.SUCCESS('Opération terminée avec succès'))

    def identify_duplicates(self):
        self.stdout.write('Identification des courses en double...')
        duplicates = Course.objects.values('nom', 'distance').annotate(count=Count('id')).filter(count__gt=1)
        self.stdout.write(f"Nombre de groupes de courses en double trouvés : {len(duplicates)}")
        return duplicates

    def delete_duplicates(self):
        self.stdout.write('Suppression des courses en double...')
        duplicates = self.identify_duplicates()
        deleted_count = 0
        for duplicate in duplicates:
            courses = Course.objects.filter(nom=duplicate['nom'], distance=duplicate['distance']).order_by('id')
            to_delete = courses[1:]  # Garder le premier, supprimer les autres
            for course in to_delete:
                self.stdout.write(f"  Suppression de la course ID {course.id}")
                course.delete()
                deleted_count += 1
        self.stdout.write(self.style.SUCCESS(f"Total des courses en double supprimées : {deleted_count}"))

    def delete_orphan_results(self):
        self.stdout.write('Suppression des résultats de courses orphelins...')
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM graph_resultatcourse
                WHERE course_id NOT IN (
                    SELECT id FROM graph_course
                );
            """)
            orphan_deleted = cursor.rowcount
        self.stdout.write(self.style.SUCCESS(f"Résultats de course orphelins supprimés : {orphan_deleted}"))