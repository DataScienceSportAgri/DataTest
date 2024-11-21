from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from ...models import ResultatCourse, Course


class Command(BaseCommand):
    help = 'Supprime les résultats de courses orphelins'

    def handle(self, *args, **options):
        # Compter le nombre initial de résultats
        initial_count = ResultatCourse.objects.count()

        with connection.cursor() as cursor:
            # Supprimer les résultats de courses orphelins
            cursor.execute('''
                DELETE FROM graph_resultatcourse
                WHERE course_id NOT IN (
                    SELECT id FROM graph_course
                );
            ''')

        # Compter le nombre de résultats restants
        remaining_count = ResultatCourse.objects.count()

        # Calculer le nombre de résultats supprimés
        deleted_count = initial_count - remaining_count

        self.stdout.write(
            self.style.SUCCESS(f'Nombre de résultats de courses orphelins supprimés : {deleted_count}')
        )

        # Vérification supplémentaire
        orphan_count = ResultatCourse.objects.exclude(course_id__in=Course.objects.values_list('id', flat=True)).count()
        if orphan_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Attention : {orphan_count} résultats orphelins restants.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Tous les résultats orphelins ont été supprimés avec succès.')
            )