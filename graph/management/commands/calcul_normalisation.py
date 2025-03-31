from django.db.models import F, Avg, Case, When, Value, FloatField
from django.db import models
from django.db.models.functions import Cast
import pandas as pd
from ...models import ResultatCourse, CategorieSimplifiee, NormalisateurDistancesCategories, CourseType
import logging
from django.core.management.base import BaseCommand, CommandError
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calcule et enregistre les coefficients de normalisation par distance et catégorie"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer le recalcul complet même si des données existent'
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 Démarrage du calcul de normalisation...")

        if not options['force'] and NormalisateurDistancesCategories.objects.exists():
            self.stdout.write(
                self.style.WARNING("ℹ️ Des données existent déjà. Utilisez --force pour écraser.")
            )
            return

        self._clear_existing_data()
        df = self._calculate_speeds()
        self._save_results(df)

        self.stdout.write(self.style.SUCCESS("✅ Calcul terminé avec succès !"))

    def _clear_existing_data(self):
        """Vide les données existantes de manière sécurisée"""
        count, _ = NormalisateurDistancesCategories.objects.all().delete()
        self.stdout.write(f"♻️ Données existantes supprimées : {count} entrées")

    def _calculate_speeds(self):
        """Version avec extraction brute, traitement pandas et filtrage par type de course"""
        self.stdout.write("📊 Extraction des données brutes...")

        # Récupération des types depuis la table CourseType
        course_types = CourseType.objects.filter(
            nom__in=['Cross', 'Course sur route', 'Foulee', 'Boucle', 'Trail']
        )

        if not course_types.exists():
            raise CommandError("❌ Aucun type de course correspondant trouvé dans CourseType")

        # Annotation des plages de distance
        distance_cases = [
            When(course__distance__lte=7500.0, then=Value('0-7500')),
            When(course__distance__gt=7500.0, course__distance__lte=15000.0, then=Value('7500-15000')),
            When(course__distance__gt=15000.0, course__distance__lte=30000.0, then=Value('15000-30000')),
            When(course__distance__gt=30000.0, course__distance__lte=45000.0, then=Value('30000-45000')),
            When(course__distance__gt=45000.0, then=Value('45000+'))
        ]

        # Requête avec filtrage sur les types de courses
        queryset = ResultatCourse.objects.filter(course__type__in=course_types).annotate(
            distance_range=Case(*distance_cases, output_field=models.CharField())
        ).values(
            'distance_range',
            'categorie__categoriesimplifiee',
            'course__distance',
            'temps'
        )

        # Conversion en DataFrame
        df = pd.DataFrame.from_records(queryset)

        # Le reste du traitement reste inchangé
        df['temps'] = pd.to_timedelta(df['temps'])
        df['course__distance'] = pd.to_numeric(df['course__distance'])

        df['temps_total_seconds'] = df['temps'].dt.total_seconds()
        df = df[df['temps_total_seconds'] > 0]  # Filtrage des temps nuls

        df['vitesse'] = (df['course__distance'] / df['temps_total_seconds']) * 3.6  # Conversion m/s → km/h
        # Nouveau filtre de vélocité
        upper_limit = 26  # 26 km/h
        lower_limit = 3  # 3 km/h (à ajuster selon vos besoins)
        # Filtrage des vitesses extrêmes
        initial_count = len(df)
        df = df[(df['vitesse'] <= upper_limit) & (df['vitesse'] >= lower_limit)]

        # Log des données filtrées
        filtered_count = initial_count - len(df)
        self.stdout.write(
            self.style.WARNING(
                f"✂️ {filtered_count} résultats filtrés "
                f"({lower_limit}-{upper_limit} km/h conservés)"
            )
        )
        # Agrégation des moyennes
        df_agg = df.groupby(['distance_range', 'categorie__categoriesimplifiee']).agg(
            vitesse_moyenne=('vitesse', 'mean')
        ).reset_index()

        return self._process_dataframe(df_agg)

    def _process_dataframe(self, df):
        """Traite le dataframe et calcule les coefficients"""
        self.stdout.write("🧮 Traitement des données...")

        # Création de toutes les combinaisons possibles
        categories = CategorieSimplifiee.objects.values_list('id', flat=True)
        distances = ['0-7500', '7500-15000', '15000-30000', '30000-45000', '45000+']

        full_index = pd.MultiIndex.from_product(
            [distances, categories],
            names=['distance_range', 'categorie__categoriesimplifiee']
        )

        final_df = full_index.to_frame(index=False).merge(
            df,
            how='left',
            on=['distance_range', 'categorie__categoriesimplifiee']
        )

        # Calcul des coefficients
        moyenne_globale = final_df['vitesse_moyenne'].mean(skipna=True)
        final_df['multiplicateur'] = (1/(final_df['vitesse_moyenne'] / moyenne_globale)).fillna(1.0)

        # Log des données manquantes
        missing = final_df[final_df['vitesse_moyenne'].isna()]
        for _, row in missing.iterrows():
            logger.warning(
                f"Données manquantes pour {row['distance_range']} - "
                f"Catégorie ID {row['categorie__categoriesimplifiee']}"
            )

        return final_df

    def _save_results(self, df):
        """Sauvegarde les résultats en base"""
        self.stdout.write("💾 Sauvegarde des résultats...")

        total = len(df)
        batch_size = 100
        created = 0

        for i in range(0, total, batch_size):
            batch = df.iloc[i:i + batch_size]
            objs = [
                NormalisateurDistancesCategories(
                    distance_range=row['distance_range'],
                    categorie_id=row['categorie__categoriesimplifiee'],
                    vitesse_moyenne=row['vitesse_moyenne'],
                    multiplicateur=row['multiplicateur']
                )
                for _, row in batch.iterrows()
            ]

            NormalisateurDistancesCategories.objects.bulk_create(objs)
            created += len(objs)
            self.stdout.write(f"⏳ Progression : {created}/{total} ({created / total:.1%})")

        self.stdout.write(f"📥 {created} entrées créées/actualisées")
