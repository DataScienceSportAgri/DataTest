from django.core.management.base import BaseCommand
from django.db import connection, transaction
from ...models import Course


class Command(BaseCommand):
    help = 'Nettoie et met à jour les données des courses'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Début du nettoyage des données...'))

        self.delete_long_courses()
        self.update_distances()

        self.stdout.write(self.style.SUCCESS('Nettoyage des données terminé avec succès'))

    def delete_long_courses(self):
        with connection.cursor() as cursor:
            # Supprimez d'abord les enregistrements liés
            cursor.execute(
                "DELETE FROM graph_resultatcourse WHERE course_id IN (SELECT id FROM graph_course WHERE distance > 60000);")

            # Ensuite, supprimez les courses
            cursor.execute("DELETE FROM graph_course WHERE distance > 60000;")
            self.stdout.write(self.style.SUCCESS(f"Courses supprimées (distance > 60000) : {cursor.rowcount}"))

    # Le reste de votre code reste inchangé

    def update_distances(self):
        with connection.cursor() as cursor:
            # Mise à jour des distances dans graph_course
            cursor.execute("""
                UPDATE graph_course
                SET distance = 
                    CASE 
                        WHEN distance = 0 AND instr(nom, 'km') > 0 THEN
                            CAST(substr(nom, 1, instr(nom, 'km') - 1) AS INTEGER) * 1000
                        WHEN instr(nom, 'km') > 0 THEN
                            CASE
                                WHEN ABS(CAST(substr(nom, 1, instr(nom, 'km') - 1) AS INTEGER) - (distance / 1000)) <= 1 THEN
                                    CASE
                                        WHEN length(substr(substr(nom, instr(nom, 'km') + 2), 1, instr(substr(nom, instr(nom, 'km') + 2), ' ') - 1)) >= 3 THEN
                                            CAST(substr(nom, 1, instr(nom, 'km') - 1) AS INTEGER) * 1000 +
                                            CAST(substr(substr(substr(nom, instr(nom, 'km') + 2), 1, instr(substr(nom, instr(nom, 'km') + 2), ' ') - 1), 1, 3) AS INTEGER)
                                        ELSE
                                            CAST(substr(nom, 1, instr(nom, 'km') - 1) AS INTEGER) * 1000
                                    END
                                ELSE
                                    distance
                            END
                        ELSE distance
                    END,
                nom = 
                    CASE
                        WHEN instr(nom, 'km') > 0 AND ABS(CAST(substr(nom, 1, instr(nom, 'km') - 1) AS INTEGER) - (distance / 1000)) > 1 THEN
                            replace(nom, substr(nom, 1, instr(nom, 'km') - 1), CAST(distance / 1000 AS INTEGER))
                        ELSE nom
                    END
                WHERE instr(nom, 'km') > 0;
            """)
            self.stdout.write(self.style.SUCCESS(f"Courses mises à jour : {cursor.rowcount}"))

            # Suppression des résultats de courses liés aux courses avec une distance de 0
            cursor.execute("""
                DELETE FROM graph_resultatcourse
                WHERE course_id IN (SELECT id FROM graph_course WHERE distance = 0);
            """)
            self.stdout.write(self.style.SUCCESS(f"Résultats de courses supprimés (distance = 0) : {cursor.rowcount}"))

            # Suppression des courses avec une distance de 0
            cursor.execute("DELETE FROM graph_course WHERE distance = 0;")
            self.stdout.write(self.style.SUCCESS(f"Courses supprimées (distance = 0) : {cursor.rowcount}"))