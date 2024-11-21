from django.db import connection
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Arrondit les distances qui ont copié les parties des dates 2018, 2019...'

    def handle(self, *args, **options):
        rounded_count = self.round_distances()
        self.stdout.write(self.style.SUCCESS(f'Nombre de distances arrondies : {rounded_count}'))

    def round_distances(self):
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE graph_course
                SET distance = (distance + (1000 - distance % 1000))
                WHERE distance % 1000 BETWEEN 201 AND 203
            ''')
            return cursor.rowcount