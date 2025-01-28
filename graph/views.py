from django.shortcuts import render
from scipy.stats import skew, kurtosis
from django.db.models import Subquery, OuterRef
from .models import Course, Categorie, CoureurCategorie, Coureur, ResultatCourse, CourseType
from django.views import generic
import plotly.graph_objects as go
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from random import sample
from django.template.loader import render_to_string
from django.views import generic
from django.db.models import F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
from django.views.generic import DetailView
from django.db.models import Prefetch
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db.models import F, ExpressionWrapper, DurationField, FloatField
from django.views.decorators.csrf import csrf_exempt
import ast



class CourseList(generic.ListView):
    template_name = 'graph/index.html'
    context_object_name = 'nom_list'
    paginate_by = 50  # Si vous voulez la pagination

    def get_queryset(self):
        """Return all finishers, ordered by their finish time."""
        return Course.objects.all().order_by('nom_marsien').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object_list:
            context['field_names'] = ['Nom', 'Année', 'Distance', 'Type']
        return context


class ResultatsCourseView(generic.ListView):
    template_name = 'graph/resultats_course.html'
    context_object_name = 'resultats_list'
    paginate_by = 50

    def get_queryset(self):
        course_id = self.kwargs['pk']
        return ResultatCourse.objects.filter(course_id=course_id).annotate(
            total_seconds=ExpressionWrapper(Cast(F('temps'), FloatField()) / 1000000.0, output_field=FloatField()),
            total_seconds2=ExpressionWrapper(Cast(F('temps2'), FloatField()) / 1000000.0, output_field=FloatField()),
            vitesse=ExpressionWrapper(
                (F('course__distance') / (F('total_seconds') + 0.000001))*3.6,  # Ajout d'une petite valeur pour éviter la division par zéro
                output_field=FloatField()
            ),
            vitesse2=ExpressionWrapper(
                (F('course__distance') / (F('total_seconds2') + 0.000001))*3.6,  # Ajout d'une petite valeur pour éviter la division par zéro
                output_field=FloatField()
            )
        ).order_by('position')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = Course.objects.get(pk=self.kwargs['pk'])
        return context


class CoureurDetailView(DetailView):
    model = Coureur
    template_name = 'graph/coureur_detail.html'
    context_object_name = 'coureur'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coureur = self.object

        # Récupérer tous les résultats de course pour ce coureur, avec les informations de course préchargées
        resultats = ResultatCourse.objects.filter(coureur=coureur).select_related('course').order_by('-course__annee', 'course__nom_marsien')

        # Récupérer toutes les catégories du coureur, groupées par année
        categories = CoureurCategorie.objects.filter(coureur=coureur).select_related('categorie').order_by('-annee')

        # Créer un dictionnaire des catégories par année
        categories_par_annee = {}
        for cat in categories:
            if cat.annee not in categories_par_annee:
                categories_par_annee[cat.annee] = []
            categories_par_annee[cat.annee].append(cat.categorie)

        # Ajouter les catégories à chaque résultat de course
        for resultat in resultats:
            resultat.categories = categories_par_annee.get(resultat.course.annee, [])

        context['resultats'] = resultats
        context['categories_par_annee'] = categories_par_annee
        return context



class VitesseDistributionView(TemplateView):
    template_name = 'graph/vitesse_distribution.html'

    def filter_by_series(self, data, series_categories):
        dataframes_by_series = {}

        for series_name, filters in series_categories.items():
            sexe_filter = filters.get('sexe', [])
            nom_filter = filters.get('nom', [])

            filtered_data = data[
                (data['sexe'].apply(
                    lambda x: not sexe_filter or (x is not None and any(sexe in sexe_filter for sexe in [x])))) &
                (data['nom_categorie'].apply(
                    lambda x: not nom_filter or (x is not None and any(cat in nom_filter for cat in [x]))))
                ]

            dataframes_by_series[series_name] = filtered_data

        return dataframes_by_series

    def calculate_stats(self, dataframes_by_series):
        stats = {
            'distances': {},
            'vitesses': {}
        }

        # Calculer les statistiques globales pour les distances
        all_distances = []
        for df in dataframes_by_series.values():
            if not df.empty:
                all_distances.extend(df['distance'].tolist())

        if all_distances:
            all_distances = np.array(all_distances)
            stats['distances'] = {
                'n': len(all_distances),
                'mediane': np.median(all_distances),
                'ecart_type': np.std(all_distances),
                'variance': np.var(all_distances),
                'pourcentage_ecart_type': (np.std(all_distances) / np.mean(all_distances)) * 100 if np.mean(
                    all_distances) != 0 else 0,
                'skewness': skew(all_distances) if len(np.unique(all_distances)) > 1 else 0,
            }

        # Calculer les statistiques pour les vitesses par série
        for series_name, df in dataframes_by_series.items():
            if not df.empty:
                vitesses = df['vitesse']
                mean = np.mean(vitesses)
                std = np.std(vitesses)
                var = np.var(vitesses)
                skewness = skew(vitesses) if len(vitesses.unique()) > 1 else 0
                kurt = kurtosis(vitesses) if len(vitesses.unique()) > 1 else -3
                # Calcul des pourcentages d'écart-type droit et gauche
                pct_ecart_type_droit = (np.sum(vitesses > mean) / len(vitesses)) * 100
                pct_ecart_type_gauche = (np.sum(vitesses < mean) / len(vitesses)) * 100
                decile_1 = np.percentile(vitesses, 10)
                decile_10 = np.percentile(vitesses, 90)

                stats['vitesses'][series_name] = {
                    'n': len(df),
                    'moyenne': mean,
                    'mediane': np.median(vitesses),
                    'ecart_type': std,
                    'variance': var,
                    'pourcentage_variance': (var / mean) * 100 if mean != 0 else 0,
                    'pourcentage_ecart_type': (std / mean) * 100 if mean != 0 else 0,
                    'pourcentage_ecart_type_droit': pct_ecart_type_droit,
                    'pourcentage_ecart_type_gauche': pct_ecart_type_gauche,
                    'decile_1': decile_1,
                    'decile_10': decile_10,
                    'skewness': skewness,
                    'kurtosis': kurt
                }
            else:
                stats['vitesses'][series_name] = None

        return stats

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.GET.get('action') == 'submit':
                context = self.handle_submit(request)
                return context  # Retourne directement le contexte
            else:
                return self.get_updated_data(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Charger les données JSON du corps de la requête
                data = json.loads(request.body)

                # Extraire la valeur de 'action'
                action = data.get('action')

                if action == 'submit':
                    return self.handle_submit(request)
                else:
                    return self.get_updated_data(request)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        return JsonResponse({'error': 'Invalid request'}, status=400)

    def handle_submit(self, request):
        request.session['user_data'] = {}
        context = self.get_context_data(request)
        html = render_to_string('graph/partial_vitesse_distribution.html', context, request=request)

        response_data = {
            'html': html,
            'chartData': {
                'stats': context['stats'],
            }
        }

        return JsonResponse(response_data)

    @csrf_exempt
    def get_context_data(self, request=None, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = Categorie.objects.values('nom', 'sexe').distinct()
        min_distance = 5000
        max_distance = 10000
        # Convertir en liste de dictionnaires
        categories_list = [{'nom': cat['nom'], 'sexe': cat['sexe'] or 'Unknown'} for cat in categories]
        type_list = ['Course sur route', 'Foulee']
        colors = [('M','blue'),('F','pink')]
        series_categories = {'F': {'sexe':['F'],'nom':[]},'M':{'sexe':['M'],'nom':[]}}
        if request and request.method == 'POST':
            try:
                post_data = json.loads(request.body)

                min_distance = int(post_data.get('min_distance', 5000))
                max_distance = int(post_data.get('max_distance', 10000))
                type_list = ast.literal_eval(post_data.get("course_types", "['Course sur route', 'Foulee']"))
                colors = post_data.get('colors', [('M', 'blue'), ('F', 'pink')])
                series_categories = post_data.get('seriesCategories',
                                                  {"F": {"sexe": ["F"], "nom": []}, "M": {"sexe": ["M"], "nom": []}})
                print('used new arg :', min_distance, max_distance, type_list, colors, series_categories)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        print('type de liste', type(type_list))
        course_type_ids = list(CourseType.objects.filter(nom__in=type_list).values_list('id', flat=True))
        print('course type ids',course_type_ids)
        initial_results = ResultatCourse.objects.filter(
            Q(course__type__in=course_type_ids) &
            Q(course__distance__gte=min_distance) &
            Q(course__distance__lte=max_distance)
        ).annotate(
            annee_course=F('course__annee'),
            distance_course = F('course__distance')
        ).values('id', 'temps', 'annee_course', 'distance_course','coureur_id').order_by('?')[:1000]
        print('len de initial_results', len(initial_results))
        # Conversion en DataFrame
        results_df = pd.DataFrame(list(initial_results))
        print('results_df', results_df)
        # Sous-requête pour obtenir la catégorie correspondante
        categories_data = CoureurCategorie.objects.filter(
            coureur_id__in=results_df['coureur_id'],
            annee__in=results_df['annee_course']
        ).values('coureur_id', 'annee', 'categorie__nom', 'categorie__sexe')

        categories_df = pd.DataFrame(list(categories_data))

        merged_data = results_df.merge(
            categories_df,
            left_on=['coureur_id', 'annee_course'],
            right_on=['coureur_id', 'annee'],
            how='left'
        )

        total_count = ResultatCourse.objects.filter(
            Q(course__type__in=course_type_ids) &
            Q(course__distance__gte=min_distance) &
            Q(course__distance__lte=max_distance)
        ).count()

        initial_ids = []
        vitesses = []
        distances = []
        sexes = []
        noms_categories = []
        print('là',merged_data)
        for index, row in merged_data.iterrows():
            # Accéder aux valeurs de chaque colonne
            initial_ids.append(row['id'])
            noms_categories.append(row['categorie__nom'])
            sexes.append(row['categorie__sexe'])
            distances.append(row['distance_course'])
            vitesse = row['distance_course'] / row['temps'].total_seconds() * 3.6
            vitesses.append(vitesse)


        df = pd.DataFrame({
            'id': initial_ids,
            'vitesse': vitesses,
            'distance': distances,
            'sexe': sexes,
            'nom_categorie': noms_categories
        })

        print(df)

        # Utilisation des fonctions
        filtered_dataframes = self.filter_by_series(df, series_categories)
        stats = self.calculate_stats(filtered_dataframes)

        # Stocker ces données dans la session
        self.request.session['loaded_ids'] = initial_ids
        self.request.session['vitesses'] = vitesses
        self.request.session['distances'] = distances

        # Générer le graphique
        context['plot'] = self.generate_plot_dynamic(filtered_dataframes, colors)
        context['initialData'] = self.generate_plot_data_dynamic(filtered_dataframes, colors)
        context['total_count'] = total_count
        context['loaded_count'] = len(initial_results)
        context['min_distance'] = min_distance
        context['max_distance'] = max_distance
        context['refresh_interval'] = 25000
        print('stats',stats)
        context['stats'] = stats
        context['series_categories'] = series_categories
        context['categories'] = json.dumps(categories_list)

        return context

    def create_countdown(self, seconds):
        return {
            'countdown': seconds,
            'message': f"Prochaine mise à jour dans {seconds} secondes"
        }

    @csrf_exempt
    def get_updated_data(self, request):
        print("Received update request from client")

        if request.method == 'POST':
            try:
                post_data = json.loads(request.body)

                min_distance = int(post_data.get('minDistance', 5000))
                max_distance = int(post_data.get('maxDistance', 10000))
                loaded_count = int(post_data.get('loaded_count', 0))
                type_list = ast.literal_eval(post_data.get("course_types", "['Course sur route', 'Foulee']"))
                colors = post_data.get('colors', [('M', 'blue'), ('F', 'pink')])
                series_categories = post_data.get('seriesCategories',
                                                  {"F": {"sexe": ["F"], "nom": []}, "M": {"sexe": ["M"], "nom": []}})
                print(type(series_categories))
                print(series_categories)
                course_type_ids = list(CourseType.objects.filter(nom__in=type_list).values_list('id', flat=True))
                selected_categories = request.GET.getlist('categories')
                print('min distance : ', min_distance)
                print('max distance : ', max_distance)
                print('loaded count : ', loaded_count)
                # Obtenir le nombre total de résultats correspondant aux filtres
                total_count = ResultatCourse.objects.filter(
                    Q(course__type__in=course_type_ids) &
                    Q(course__distance__gte=min_distance) &
                    Q(course__distance__lte=max_distance)
                ).count()
                print(total_count)
                # Récupérer les IDs déjà chargés
                loaded_ids = set(request.session.get('loaded_ids', []))
                # Filtrer les résultats déjà chargés qui correspondent toujours aux critères
                still_valid_ids = set(ResultatCourse.objects.filter(
                    Q(course__type__in=course_type_ids) &
                    Q(course__distance__gte=min_distance) &
                    Q(course__distance__lte=max_distance) &
                    Q(id__in=loaded_ids)
                ).values_list('id', flat=True))

                # Calculer le nombre de nouveaux résultats à charger
                remaining_count = min(1000, total_count - len(still_valid_ids))

                # Sélectionner aléatoirement de nouveaux résultats
                new_results = ResultatCourse.objects.filter(
                    Q(course__type__in=course_type_ids) &
                    Q(course__distance__gte=min_distance) &
                    Q(course__distance__lte=max_distance)
                ).exclude(id__in=still_valid_ids).annotate(
                    annee_course=F('course__annee'),
                    distance_course=F('course__distance')
                ).values('id', 'temps', 'annee_course', 'distance_course', 'coureur_id').order_by('?')[:remaining_count]

                # Conversion en DataFrame
                results_df = pd.DataFrame(list(new_results))
                # Créer un DataFrame pour still_valid_ids
                still_valid_results = ResultatCourse.objects.filter(id__in=still_valid_ids).annotate(
                    annee_course=F('course__annee'),
                    distance_course=F('course__distance')
                ).values('id', 'temps', 'annee_course', 'distance_course', 'coureur_id')

                still_valid_df = pd.DataFrame(list(still_valid_results))

                combined_df = pd.concat([results_df, still_valid_df], keys=['new', 'still_valid'], ignore_index=False)
                combined_df = combined_df.reset_index(level=0).rename(columns={'level_0': 'source'})

                # Obtenir les catégories pour tous les résultats
                all_categories_data = CoureurCategorie.objects.filter(
                    coureur_id__in=combined_df['coureur_id'],
                    annee__in=combined_df['annee_course']
                ).values('coureur_id', 'annee', 'categorie__nom', 'categorie__sexe')

                all_categories_df = pd.DataFrame(list(all_categories_data))

                # Fusionner toutes les données
                merged_data = combined_df.merge(
                    all_categories_df,
                    left_on=['coureur_id', 'annee_course'],
                    right_on=['coureur_id', 'annee'],
                    how='left'
                )

                # Calculer les vitesses
                merged_data['vitesse'] = merged_data['distance_course'] / merged_data['temps'].dt.total_seconds() * 3.6

                # Créer le DataFrame final
                df = merged_data[['id', 'vitesse', 'distance_course', 'categorie__sexe', 'categorie__nom']]
                df.columns = ['id', 'vitesse', 'distance', 'sexe', 'nom_categorie']

                # Utilisation des fonctions
                filtered_dataframes = self.filter_by_series(df, series_categories)
                stats = self.calculate_stats(filtered_dataframes)
                print('stats_updated',stats)

                # Mettre à jour les IDs chargés
                updated_loaded_ids = list(df['id'])
                request.session['loaded_ids'] = updated_loaded_ids
                # Calculer les vitesses pour les nouveaux résultats
                new_vitesses = merged_data[merged_data['source'] == 'new'][['vitesse']]
                print('taille de nouvelle vitesse',len(new_vitesses))
                resultat = ResultatCourse.objects.filter(id__in=updated_loaded_ids)
                print('taille de resultat', len(resultat))
                # Générer les données du graphique
                plot_data = self.generate_plot_data_dynamic(filtered_dataframes, colors)
                vitesses = self.request.session.get('vitesses')
                distances = self.request.session.get('distances')
                # Calcul des statistiques

                return JsonResponse({
                    'total_count': total_count,
                    'stats': stats,
                    'loaded_count': len(resultat),
                    'plot_data': plot_data,
                    'is_update': True,
                    'categories_selected': selected_categories
                })
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

    def generate_plot_data(self, resultats, vitesses):
        data = []
        for i, resultat in enumerate(resultats):
            vitesse = vitesses[i]
            coureur_categorie = CoureurCategorie.objects.filter(coureur=resultat.coureur).first()
            sexe = coureur_categorie.categorie.sexe if coureur_categorie else 'Inconnu'
            data.append({'vitesse': vitesse, 'sexe': sexe})

        df = pd.DataFrame(data)
        plot_data = []

        for sexe, color in [('M', 'blue'), ('F', 'pink')]:
            df_sexe = df[df['sexe'] == sexe]
            plot_data.append({
                'type': 'violin',
                'x': df_sexe['vitesse'].tolist(),
                'name': sexe,
                'box': {'visible': True},
                'line': {'color': color},
                'opacity': 0.6,
                'marker': {'color': color}
            })

        moyenne_hommes = df[df['sexe'] == 'M']['vitesse'].mean()
        moyenne_femmes = df[df['sexe'] == 'F']['vitesse'].mean()

        layout = {
            'title': "Distribution des vitesses",
            'xaxis': {'title': "Vitesse (km/h)"},
            'yaxis': {'title': "Densité"},
            'uirevision': 'constant',
            'shapes': [
                {'type': 'line', 'x0': moyenne_hommes, 'x1': moyenne_hommes, 'y0': 0, 'y1': 1,
                 'line': {'color': 'blue', 'width': 2, 'dash': 'dash'}},
                {'type': 'line', 'x0': moyenne_femmes, 'x1': moyenne_femmes, 'y0': 0, 'y1': 1,
                 'line': {'color': 'deeppink', 'width': 2, 'dash': 'dash'}}
            ]
        }

        return {'data': plot_data, 'layout': layout}


    def generate_plot(self, resultats, vitesses):

        data = []
        for i, resultat in enumerate(resultats):
            vitesse = vitesses[i]
            coureur_categorie = CoureurCategorie.objects.filter(coureur=resultat.coureur).first()
            sexe = coureur_categorie.categorie.sexe if coureur_categorie else 'Inconnu'
            data.append({'vitesse': vitesse, 'sexe': sexe})

        df = pd.DataFrame(data)
        fig = go.Figure()

        for sexe, color in [('M', 'blue'), ('F', 'pink')]:
            df_sexe = df[df['sexe'] == sexe]
            fig.add_trace(go.Violin(x=df_sexe['vitesse'], name=sexe,
                                    box_visible=True, line_color=color,
                                    opacity=0.6,
                                    marker=dict(color=color)))

        fig.update_traces(opacity=0.4)

        moyenne_hommes = df[df['sexe'] == 'M']['vitesse'].mean()
        moyenne_femmes = df[df['sexe'] == 'F']['vitesse'].mean()

        fig.add_vline(x=moyenne_hommes, line_width=2, line_dash="dash", line_color="blue")
        fig.add_vline(x=moyenne_femmes, line_width=2, line_dash="dash", line_color="deeppink")

        fig.update_layout(title="Distribution des vitesses",
                          xaxis_title="Vitesse (km/h)",
                          yaxis_title="Densité")

        return fig.to_html(full_html=False)

    def add_annotations_with_offset(self, layout, moyennes, color_dict):
        """
        Ajoute des annotations avec un décalage vertical pour éviter la superposition des textes.

        :param layout: Le layout du graphique.
        :param moyennes: Dictionnaire des moyennes par série.
        :param color_dict: Dictionnaire des couleurs par série.
        :return: Layout mis à jour avec les annotations.
        """
        offset_step = 0.05  # Décalage vertical entre les annotations
        base_y = 1  # Position de base pour les annotations

        for i, (series_name, moyenne) in enumerate(moyennes.items()):
            if not pd.isna(moyenne):
                layout['annotations'].append({
                    'x': moyenne,
                    'y': base_y - (i * offset_step),  # Décalage vertical
                    'xref': 'x',
                    'yref': 'paper',
                    'text': f"Moyenne {series_name}: {moyenne:.2f} km/h",
                    'showarrow': False,
                    'font': {'color': color_dict.get(series_name, 'gray')}
                })

        return layout

    def generate_plot_data_dynamic(self, filtered_dataframes, colors):
        """
        Génère les données pour un graphique avec des catégories dynamiques.

        :param filtered_dataframes: Dictionnaire de DataFrames filtrés par série.
        :param colors: Liste de tuples (catégorie, couleur).
        :return: Données formatées pour le graphique.
        """
        plot_data = []
        color_dict = dict(colors)
        moyennes = {}
        series_count = len(filtered_dataframes)

        for i, (series_name, df) in enumerate(filtered_dataframes.items()):
            if not df.empty:
                color = color_dict.get(series_name, 'gray')
                side = None

                # Condition pour les violons bilatéraux si moins de 7 séries
                if series_count < 7:
                    side = 'both'

                # Alternance des violons pour plus de 6 séries
                elif series_count >= 7:
                    if i % 2 == 0:
                        side = 'positive'
                    else:
                        side = 'negative'

                plot_data.append({
                    'type': 'violin',
                    'x': df['vitesse'].tolist(),
                    'name': series_name,
                    'box': {'visible': True},
                    'line': {'color': color},
                    'opacity': 0.6,
                    'marker': {'color': color},
                    'side': side
                })
                moyennes[series_name] = df['vitesse'].mean()

        layout = {
            'title': "Distribution des vitesses par série",
            'xaxis': {'title': "Vitesse (km/h)"},
            'yaxis': {'title': "Densité"},
            'uirevision': 'constant',
            'shapes': [
                {'type': 'line',
                 'x0': moyenne,
                 'x1': moyenne,
                 'y0': 0,
                 'y1': 1,
                 'line': {'color': color_dict.get(series_name, 'gray'), 'width': 2, 'dash': 'dash'}}
                for series_name, moyenne in moyennes.items() if not pd.isna(moyenne)
            ],
            'annotations': []  # Les annotations seront ajoutées dans l'étape suivante
        }

        # Ajouter les annotations avec décalage
        layout = self.add_annotations_with_offset(layout, moyennes, color_dict)

        return {'data': plot_data, 'layout': layout}

    def generate_plot_dynamic(self, filtered_dataframes, colors):
        """
        Génère un graphique interactif avec des catégories dynamiques.

        :param filtered_dataframes: Dictionnaire de DataFrames filtrés par série.
        :param colors: Liste de tuples (catégorie, couleur).
        :return: HTML du graphique interactif.
        """
        fig = go.Figure()
        color_dict = dict(colors)
        series_count = len(filtered_dataframes)

        for i, (series_name, df) in enumerate(filtered_dataframes.items()):
            if not df.empty:
                color = color_dict.get(series_name, 'gray')
                side = None

                if series_count < 7:
                    side = 'both'
                elif series_count >= 7:
                    side = 'positive' if i % 2 == 0 else 'negative'

                fig.add_trace(go.Violin(x=df['vitesse'], name=series_name,
                                        box_visible=True, line_color=color,
                                        opacity=0.6,
                                        marker=dict(color=color),
                                        side=side))

        fig.update_traces(opacity=0.4)

        for i, (series_name, df) in enumerate(filtered_dataframes.items()):
            if not df.empty:
                moyenne = df['vitesse'].mean()
                color = color_dict.get(series_name, 'gray')
                if not pd.isna(moyenne):
                    fig.add_annotation(
                        x=moyenne,
                        y=1 - (i * 0.05),  # Décalage vertical
                        xref='x',
                        yref='paper',
                        text=f"Moyenne {series_name}: {moyenne:.2f} km/h",
                        showarrow=False,
                        font=dict(color=color)
                    )
                    fig.add_vline(x=moyenne, line_width=2, line_dash="dash", line_color=color)

        fig.update_layout(title="Distribution des vitesses par série",
                          xaxis_title="Vitesse (km/h)",
                          yaxis_title="Densité",
                          violinmode="group")

        return fig.to_html(full_html=False)



