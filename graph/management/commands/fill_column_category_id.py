import sqlite3
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Fusionne les données entre deux bases SQLite"

    def handle(self, *args, **kwargs):
        # Connexion aux deux bases
        main_db = sqlite3.connect('db.sqlite3')
        external_db = sqlite3.connect(r'C:\Users\33682\Desktop\Backup\cleanCategorieSansFusion.sqlite3')

        main_cursor = main_db.cursor()
        external_cursor = external_db.cursor()

        try:
            # Récupérer les données depuis la base externe
            external_cursor.execute("SELECT id, categorie_id FROM graph_resultatcourse")
            data = external_cursor.fetchall()

            # Insérer ou mettre à jour les données dans la base principale
            for resultat_course, categorie_id in data:
                main_cursor.execute("""
                    UPDATE graph_resultatcourse
                    SET categorie_id = ?
                    WHERE id = ?;
                """, (categorie_id, resultat_course))

            main_db.commit()
            self.stdout.write(self.style.SUCCESS("Les données ont été fusionnées avec succès !"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur : {e}"))
        finally:
            main_db.close()
            external_db.close()
