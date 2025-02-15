import csv
from django.core.management.base import BaseCommand
from graph.models import Categorie


class Command(BaseCommand):
    help = "Met à jour les catégories simplifiées dans la table graph_categorie en utilisant plusieurs fichiers CSV"

    def handle(self, *args, **kwargs):
        # Chemins vers les fichiers CSV
        csv_file_1 = r"D:\Downloads\CategorieCategorieSimplifie.csv"
        csv_file_2 = r"D:\Downloads\Correspondance2.csv"

        try:
            # Étape 1 : Charger les correspondances du premier fichier
            correspondance = self.load_csv(csv_file_1)
            self.update_categories(correspondance)

            # Étape 2 : Charger les correspondances du deuxième fichier pour compléter les id null
            correspondance_2 = self.load_csv(csv_file_2)
            self.update_categories(correspondance_2, only_null=True)

            self.stdout.write(self.style.SUCCESS("Mise à jour terminée avec les deux fichiers CSV."))

        except FileNotFoundError as e:
            self.stderr.write(self.style.ERROR(f"Le fichier est introuvable : {str(e)}"))
        except KeyError as e:
            self.stderr.write(self.style.ERROR(f"Le fichier CSV est mal formaté : colonne manquante {str(e)}."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erreur lors du traitement des fichiers CSV : {str(e)}"))

    def load_csv(self, file_path):
        """
        Charge un fichier CSV et retourne un dictionnaire de correspondances.
        """
        correspondance = {}
        if file_path == r"D:\Downloads\CategorieCategorieSimplifie.csv":
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    code = row['Code']
                    id_simplifie = int(row['ID Categorie Simplifiee'])
                    correspondance[code] = id_simplifie
            return correspondance
        else:
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    code = row['Code']
                    id_simplifie = int(row['ID_Categorie_Simplifiee'])
                    correspondance[code] = id_simplifie
            return correspondance

    def update_categories(self, correspondance, only_null=False):
        """
        Met à jour les catégories dans la base de données en fonction des correspondances.
        Si `only_null` est True, seules les catégories avec `id_categoriesimplifie` null seront mises à jour.
        """
        print('correspondance', correspondance)
        for categorie in Categorie.objects.all():
            if only_null:
                code = str(categorie.id)
            else:
                code = categorie.nom  # Assurez-vous que 'nom' est le champ correspondant au Code dans le CSV
            print(type(code))
            if code in correspondance:
                id_simplifie = correspondance[code]

                # Vérifier si on doit mettre à jour uniquement les champs null
                if only_null and categorie.id_categoriesimplifie is not None:
                    print(f'already done for {code}')
                    continue

                try:
                    categorie.id_categoriesimplifie = id_simplifie
                    categorie.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Catégorie {code} mise à jour avec ID simplifié {id_simplifie}."
                    ))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(
                        f"Erreur lors de la mise à jour de la catégorie {code}: {str(e)}"
                    ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Aucune correspondance trouvée pour le code {code}."
                ))