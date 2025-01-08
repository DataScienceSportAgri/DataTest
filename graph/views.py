from django.shortcuts import render


from .models import Course, Categorie, CoureurCategorie, Coureur, ResultatCourse
from django.views import generic
import plotly.graph_objects as go
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from .models import ResultatCourse, CoureurCategorie
import pandas as pd
import plotly.graph_objs as go
from random import sample
from django.template.loader import render_to_string
from django.views import generic
from django.db.models import F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
from django.views.generic import DetailView
from django.db.models import Prefetch

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

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.GET.get('action') == 'submit':
                context = self.handle_submit(request)
                return context  # Retourne directement le contexte
            else:
                return self.get_updated_data(request)
        return super().get(request, *args, **kwargs)

    def handle_submit(self, request):
        request.session['user_data'] = {}
        context = self.get_context_data()
        html = render_to_string('graph/partial_vitesse_distribution.html', context, request=request)
        return HttpResponse(html)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        min_distance = int(self.request.GET.get('min_distance', 5000))
        max_distance = int(self.request.GET.get('max_distance', 10000))
        print('min dist', min_distance)
        print('max dist', max_distance)
        # Filtrer et sélectionner aléatoirement 1000 résultats en une seule requête
        initial_results = ResultatCourse.objects.filter(
            course__distance__gte=min_distance,
            course__distance__lte=max_distance
        ).order_by('?')[:1000]

        total_count = ResultatCourse.objects.filter(
            course__distance__gte=min_distance,
            course__distance__lte=max_distance
        ).count()

        # Calculer les vitesses et stocker les données nécessaires
        initial_ids = []
        vitesses = []
        distances = []
        for resultat in initial_results:
            initial_ids.append(resultat.id)
            vitesse = resultat.course.distance / resultat.temps.total_seconds() * 3.6
            vitesses.append(vitesse)
            distances.append(resultat.course.distance)

        # Stocker ces données dans la session
        self.request.session['loaded_ids'] = initial_ids
        self.request.session['vitesses'] = vitesses
        self.request.session['distances'] = distances

        # Générer le graphique
        context['plot'] = self.generate_plot(initial_results, vitesses)
        context['initialData'] = self.generate_plot_data(initial_results, vitesses)
        context['total_count'] = total_count
        context['loaded_count'] = len(initial_ids)
        context['min_distance'] = min_distance
        context['max_distance'] = max_distance
        context['refresh_interval'] = 25000

        return context

    def create_countdown(self, seconds):
        return {
            'countdown': seconds,
            'message': f"Prochaine mise à jour dans {seconds} secondes"
        }

    def get_updated_data(self, request):
        print("Received update request from client")
        min_distance = int(request.GET.get('min_distance', 5000))
        max_distance = int(request.GET.get('max_distance', 10000))
        loaded_count = int(request.GET.get('loaded_count', 0))
        print('min distance : ', min_distance)
        print('max distance : ', max_distance)
        print('loaded count : ', loaded_count)
        # Obtenir le nombre total de résultats correspondant aux filtres
        total_count = ResultatCourse.objects.filter(
            course__distance__gte=min_distance,
            course__distance__lte=max_distance
        ).count()
        print(total_count)
        # Récupérer les IDs déjà chargés
        loaded_ids = set(request.session.get('loaded_ids', []))
        # Filtrer les résultats déjà chargés qui correspondent toujours aux critères
        still_valid_ids = set(ResultatCourse.objects.filter(
            id__in=loaded_ids,
            course__distance__gte=min_distance,
            course__distance__lte=max_distance
        ).values_list('id', flat=True))

        # Calculer le nombre de nouveaux résultats à charger
        remaining_count = min(1000, total_count - len(still_valid_ids))

        # Sélectionner aléatoirement de nouveaux résultats
        new_results = ResultatCourse.objects.filter(
            course__distance__gte=min_distance,
            course__distance__lte=max_distance
        ).exclude(id__in=still_valid_ids).order_by('?')[:remaining_count]

        # Mettre à jour les IDs chargés
        updated_loaded_ids = list(still_valid_ids) + list(new_results.values_list('id', flat=True))
        request.session['loaded_ids'] = updated_loaded_ids
        # Calculer les vitesses pour les nouveaux résultats
        new_vitesses = [resultat.course.distance / resultat.temps.total_seconds() * 3.6 for resultat in new_results]
        print('taille de nouvelle vitesse',len(new_vitesses))
        resultat = ResultatCourse.objects.filter(id__in=updated_loaded_ids)
        print('taille de resultat', len(resultat))
        # Générer les données du graphique
        plot_data = self.generate_plot_data(new_results, new_vitesses)
        return JsonResponse({
            'total_count': total_count,
            'loaded_count': len(resultat),
            'plot_data': plot_data,
            'is_update': True,
        })

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
