import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Count
import statistics
from graph.models import ResultatCourse, Course, NormalisateurDistancesCategories, \
    NormalisateurTypeDeCourseNbParticipants
from django.db.models import F, Func, IntegerField, Value, CharField, Q
from django.db.models.functions import Cast, Substr
# Par ceci :
from django.forms import model_to_dict
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Calcule les scores de performance avec gestion individuelle des catégories'

    def get_multiplicateur_participants(self, course, nb_participants):
        return NormalisateurTypeDeCourseNbParticipants.objects.filter(
            course_type_id=course.type_id,
            seuil_participants__lte=nb_participants
        ).order_by('-seuil_participants').first().multiplicateur


    def handle(self, *args, **kwargs):
        # Étape 1 : Préchargement de tous les normalisateurs
        norm_data = NormalisateurDistancesCategories.objects.values_list(
            'id',
            'categorie_id',
            'distance_range',
            'multiplicateur',
            named=True
        )
        t = 0
        # Conversion en DataFrame avec parsing des distances
        norm_df = pd.DataFrame([
            {
                'id': nd.id,
                'categorie_id': nd.categorie_id,
                'min': int(nd.distance_range.split('-')[0]),
                'max': int(nd.distance_range.split('-')[1]),
                'multiplicateur': nd.multiplicateur
            }
            for nd in norm_data
            if '-' in nd.distance_range
        ])

        # Étape 2 : Traitement des courses
        courses = Course.objects.filter(type_id__in=[1, 7, 8, 9, 11])
        for course in tqdm(courses, desc="Traitement des courses"):
            resultats = list(course.resultatcourse_set.all())

            # Création du DataFrame avec catégorie simplifiée et sexe
            resultats_df = pd.DataFrame([{
                'id': r.id,
                'temps': r.temps,
                'categorie_precise': r.categorie_id,
                'categorie_id': r.categorie.categoriesimplifiee_id,
                'distance': course.distance,
                'sexe': r.categorie.sexe  # Ajout du sexe depuis la catégorie
            } for r in resultats])

            # Calcul des vitesses
            resultats_df['temps_seconds'] = pd.to_timedelta(resultats_df['temps']).dt.total_seconds()
            resultats_df = resultats_df[resultats_df['temps_seconds'] > 0]
            resultats_df['vitesse'] = (resultats_df['distance'] / resultats_df['temps_seconds']) * 3.6
            # Filtrage des normalisateurs pour cette course
            filtered_norm = norm_df[
                (norm_df['min'] <= course.distance) &
                (norm_df['max'] >= course.distance)
                ]

            # Calcul des effectifs par catégorie
            category_counts = resultats_df['categorie_id'].value_counts()

            # Détermination des catégories valides (>=6 participants)
            valid_categories = category_counts[category_counts >= 6].index
            invalid_categories = category_counts[category_counts < 6].index

            # Calcul des médianes conditionnelles
            median_by_category = resultats_df[resultats_df['categorie_id'].isin(valid_categories)] \
                .groupby('categorie_id')['vitesse'].median()

            median_by_sex = resultats_df[resultats_df['categorie_id'].isin(invalid_categories)] \
                .groupby('sexe')['vitesse'].median()

            # Médiane globale de secours
            overall_median = resultats_df['vitesse'].median()

            # Application des médianes
            resultats_df['median_vitesse'] = resultats_df.apply(
                lambda row: (
                    median_by_category[row['categorie_id']]
                    if row['categorie_id'] in valid_categories
                    else median_by_sex.get(row['sexe'], overall_median)
                ),
                axis=1
            )

            # Filtrage des normalisateurs pour cette course
            filtered_norm = norm_df[
                (norm_df['min'] <= course.distance) &
                (norm_df['max'] >= course.distance)
                ]

            # Jointure finale avec vérification
            merged_df = pd.merge(
                resultats_df,
                filtered_norm,
                on='categorie_id',
                how='left'
            ).fillna({'multiplicateur': 1.0})
            # Calcul des scores
            merged_df['score_de_performance_vitesse'] = (
                (0.5 * (merged_df['vitesse'] / merged_df['vitesse'].mean()) * merged_df['multiplicateur'] +
                    0.5 * (merged_df['vitesse'] / merged_df['median_vitesse']) * self.get_multiplicateur_participants(
                course, len(resultats)))*100
            )
            merged_df['score_de_performance_global'] = (
                (0.8 *( (merged_df['vitesse'] / merged_df['vitesse'].mean()) * merged_df['multiplicateur'] ) +
                    0.2 * (((merged_df['vitesse'] / merged_df['median_vitesse'])** 2) * (merged_df['temps_seconds'] / 10800) ) )*100
            )

            # Ajout de logs périodiques tous les 1000 résultats
            for idx, row in merged_df.iterrows():
                if t % 10000 == 0:
                    print(f"""
                                Vérification ID {row['id_x']}:
                                - Catégorie: {row['categorie_id']} ({'valide' if row['categorie_id'] in valid_categories else 'non valide'})
                                - Sexe: {row['sexe']}
                                - Vitesse: {row['vitesse']:.2f} km/h
                                - Médiane utilisée: {row['median_vitesse']:.2f}
                                - Multiplicateur: {row['multiplicateur']}
                                """)

                t+=1

            # Mise à jour des instances
            for _, row in merged_df.iterrows():
                resultat = next(r for r in resultats if r.id == row['id_x'])
                resultat.score_de_performance_vitesse = row['score_de_performance_vitesse']
                resultat.score_de_performance_global = row['score_de_performance_global']

            # Sauvegarde
            ResultatCourse.objects.bulk_update(
                resultats,
                ['score_de_performance_vitesse', 'score_de_performance_global'],
                batch_size=1000
            )

        self.stdout.write(self.style.SUCCESS('Mise à jour terminée avec succès'))