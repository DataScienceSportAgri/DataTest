import numpy as np
from django.core.cache import cache
from venv import logger
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError
from .services.image_processor import ParcelImageProcessor
import os
from django.conf import settings
from .schemas import GridCellSchema
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from dash_apps import parcel_dash  # Assurez-vous que cette ligne est présente
from .services.ndvi_plot import *
from django.views import View

def home(request):
    context = {
        'message': 'Cette application vous aide à gérer votre exploitation agricole.'
    }
    return render(request, 'agri/app_presentation.html', context)

def get_available_dates():
    tiff_dir = os.path.join(settings.STATIC_ROOT, 'satellite_data','Boulinsard', '12bands')
    dates = []
    for file in os.listdir(tiff_dir):
        if file.endswith('12band.TIFF'):
            date = file.split('_')[0]  # Extrait la date du nom de fichier
            dates.append(date)
    return sorted(dates)

@method_decorator(csrf_exempt, name='dispatch')
class ParcelView(TemplateView):
    template_name = 'agri/parcel_viewer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Partie commune inchangée
        context['dates'] = get_available_dates()
        context['initial_date'] = context['dates'][0]
        parcel_path = "Boulinsard"
        # Traitement des données principales
        processor = ParcelImageProcessor(context['initial_date'], 4, 4, parcel_path)
        # Génération de l'image RGB
        context['rgb_image_path'] = processor.save_rgb_image()
        # Traitement de la grille
        raw_grid = processor.create_pixel_grid()
        try:
            validated_grid = [GridCellSchema.model_validate(cell).model_dump() for cell in raw_grid]
        except ValidationError as e:
            logger.error("Erreur de validation : %s", e)
            return HttpResponseServerError()

        pixel_grid = processor.serialize_grid(raw_grid)
        grid_session_data = processor.get_grid_ids_and_data(raw_grid)

        # Mise à jour de la session
        self.request.session.update({
            'loaded_ids': grid_session_data['ids'],
            'grid_cells': grid_session_data['data']
        })
        self.request.session.modified = True
        # Données conservées pour la partie non-Dash
        context['pixel_grid'] = pixel_grid

        context['session_key'] = self.request.session.session_key
        return context



    @csrf_exempt
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                action = request.POST.get('action')
                if action == 'change_date':
                    date = request.POST.get('date')
                    column_size = request.POST.get('column_size')
                    row_size = request.POST.get('row_size')
                    parcel_path = "Boulinsard"

                    # Création et sauvegarde de la nouvelle image
                    processor2 = ParcelImageProcessor(date, int(column_size), int(row_size), parcel_path)
                    rgb_image_path = processor2.save_rgb_image()

                    raw_grid2 = processor2.create_pixel_grid()
                    pixel_grid2 = processor2.serialize_grid(raw_grid2)
                    # Récupération des données structurées
                    grid_session_data = processor2.get_grid_ids_and_data(raw_grid2)
                    # Réinitialisation complète
                    # Stockage direct dans la session comme vous le souhaitez
                    try:
                        self.request.session.flush()
                    except:
                        print("cant reset session")
                    try:
                        self.request.session['loaded_ids'] = grid_session_data['ids']
                        self.request.session['grid_cells'] = grid_session_data['data']
                    except:
                        try:
                            self.request.session['loaded_ids'].update(grid_session_data['ids'])
                            self.request.session['grid_cells'].update(grid_session_data['data'])
                        except:
                            print("cant update data")

                    return JsonResponse({
                            'rgb_image_path': rgb_image_path,
                            'pixel_grid': pixel_grid2  # Suppression de la sérialisation superflue
                        }, safe=False)

                elif action == 'get_zone_by_id':
                    cell_id = request.POST.get('cell_id')
                    date = request.POST.get('date')
                    column_size = request.POST.get('column_size')
                    row_size = request.POST.get('row_size')
                    # Vérifier la cohérence de la date
                    current_grid = request.session.get('grid_cells')
                    cell_data = current_grid.get(cell_id)
                    if not cell_data:
                        return JsonResponse({'error': 'Zone non trouvée'}, status=404)
                    parcel_path = 'Boulinsard'
                    processor3 = ParcelImageProcessor(date, int(column_size), int(row_size), parcel_path)

                    zone_data = processor3.get_zone_data(cell_data)

                    # Avant l'envoi au serveur
                    for band in zone_data['bands']:
                        zone_data['bands'][band] = zone_data['bands'][band].item()  # Convertit np.float32 en float natif
                    try:
                        return JsonResponse({
                            'coordinates': zone_data['coordinates'],
                            'bands': zone_data['bands']
                        })
                    except Exception as e:
                        logger.error(f"Erreur critique: {str(e)}", exc_info=True)
                        return JsonResponse({'error': 'Erreur de traitement'}, status=500)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'error': 'Requête non autorisée'}, status=400)

class NDVIView(View):
    def get(self, request, *args, **kwargs):
        # Récupérer la date depuis les paramètres GET ou utiliser une date par défaut
        specific_date = request.GET.get('date', '2021-03-08')  # Date par défaut pour l'initialisation

        try:
            converted_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
        except ValueError:
            return render(request, 'agri/ndvi_template.html', {'error': 'Date invalide'})

        # Obtenir les données NDVI
        ndvi_data, date_df = create_ndvi_cube()
        first_layer = date_df.loc[date_df['sorted_date'] == converted_date].index[0]
        info_last_count = date_df.loc[date_df['sorted_date'] == converted_date].iloc[-1]
        print('info_first_layer', first_layer)

        print('test')
        # Extraire les valeurs de current_date et co
        last_count = info_last_count['number']
        print('layer ',first_layer, last_count)
        # Générer le graphique NDVI
        plot_html = generate_ndvi_plot(ndvi_data, first_layer, last_count)

        # Retourner le contexte au template
        return render(request, 'agri/ndvi_template.html', {'plot_html': plot_html})
