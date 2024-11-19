import os
from tqdm import tqdm
from django.db import migrations, transaction
from django.apps import apps
from graph.Nom_Prenoms import separer_noms_prenoms
import pandas as pd
from graph.models import Course, ResultatCourse, Categorie, Coureur, CoureurCategorie
import re
from datetime import datetime, timedelta

from datetime import timedelta


def parse_duration(value):
    if not value or value.strip() == '':
        return None  # ou timedelta(0) si vous préférez une durée nulle

    # Supprimez '0 days ' si présent
    value = re.sub(r'^\d+ days? ', '', value)

    try:
        time_parts = list(map(int, value.split(':')))
        if len(time_parts) == 3:
            hours, minutes, seconds = time_parts
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        else:
            return None  # ou gérer d'autres formats si nécessaire
    except ValueError:
        return None  # En cas d'erreur de parsing


@transaction.atomic
def import_csv_files(directory_path, Course, ResultatCourse, Categorie, Coureur, CoureurCategorie):
    csv_files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
    print(f"Début de l'importation des fichiers CSV depuis : {directory_path}")
    for filename in tqdm(csv_files, desc="Traitement des fichiers"):
        if filename.endswith('.csv'):
            nom_course = os.path.splitext(filename)[0]
            file_path = os.path.join(directory_path, filename)
            
            df = pd.read_csv(file_path,on_bad_lines='skip')
            df.iloc[:, 0] += 1
            
            distance = int(df.iloc[0]['Distance'])
            annee = int(df.iloc[0]['annee'])
            course, _ = Course.objects.get_or_create(
                nom=nom_course,
                annee=annee,
                distance=distance
            )

            for _, row in df.iterrows():
                nom_complet = row['Nom']
                try:
                    prenom, nom = separer_noms_prenoms(nom_complet)
                except:
                    break
                categorie, _ = Categorie.objects.get_or_create(nom=row['Categ'])

                # Créer le coureur avec gestion des doublons
                suffix = 0
                while True:
                    coureur_nom = f"{nom}{suffix if suffix else ''}"
                    coureur, created = Coureur.objects.get_or_create(
                        prenom=prenom,
                        nom=coureur_nom
                    )
                    if created:
                        break
                    suffix += 1

                categoriecoureur, _ = CoureurCategorie.objects.get_or_create(
                    coureur=coureur,
                    categorie=categorie,
                    annee=annee
                )

                temps = parse_duration(str(row['Temps']))
                temps2 = parse_duration(str(row['Temps2']))

                # Créer le résultat de course avec gestion des erreurs d'intégrité
                try:
                    with transaction.atomic():
                        resultatcourse, _ = ResultatCourse.objects.get_or_create(
                            course=course,
                            coureur=coureur,
                            defaults={
                                'position': row.iloc[0],
                                'temps': temps,
                                'temps2': temps2
                            }
                        )
                except:
                    # Si une erreur d'intégrité se produit, on incrémente le suffixe et on réessaie
                    suffix += 1
                    continue
    print("Importation terminée.")



def import_data(Course, ResultatCourse, Categorie, Coureur, CoureurCategorie):
    directory_path = 'D:/Users/33682/Résultats/Partie5/Partie5d'
    import_csv_files(directory_path, Course, ResultatCourse, Categorie, Coureur, CoureurCategorie)
