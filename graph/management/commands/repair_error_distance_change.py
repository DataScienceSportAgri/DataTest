from django.db import connection
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Met à jour les distances des courses lorsque la différence est exactement de 1000 mètres'

    def handle(self, *args, **options):
        updated_count = self.update_distances()
        self.stdout.write(self.style.SUCCESS(f'Nombre de distances mises à jour : {updated_count}'))

    def update_distances(self):
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE graph_course
                SET distance = CAST(substr(nom, 1, instr(nom, 'km') - 1) AS INTEGER) * 1000
                WHERE instr(nom, 'km') > 0
                  AND CAST(substr(nom, 1, instr(nom, 'km') - 1) AS INTEGER) * 1000 - distance = -1000;
            ''')
            return cursor.rowcount