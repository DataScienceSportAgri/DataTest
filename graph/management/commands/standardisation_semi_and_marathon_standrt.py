from django.db import connection
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Ajuste les distances spécifiques des courses non-trail'

    def handle(self, *args, **options):
        updated_count = self.adjust_specific_distances()
        self.stdout.write(self.style.SUCCESS(f'Nombre de distances ajustées : {updated_count}'))

    def adjust_specific_distances(self):
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE graph_course
                SET distance = CASE
                    WHEN distance = 21000 THEN 21097
                    WHEN distance = 42000 THEN 42195
                    ELSE distance
                END
                WHERE lower(nom) NOT LIKE '%trail%'
                  AND (distance = 21000 OR distance = 42000);
            ''')
            return cursor.rowcount