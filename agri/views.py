from venv import logger

from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError
from django.core.serializers import serialize
from .services.image_processor import ParcelImageProcessor
import os
from django.conf import settings
from .schemas import GridCellSchema

def home(request):
    context = {
        'message': 'Cette application vous aide à gérer votre exploitation agricole.'
    }
    return render(request, 'agri/app_presentation.html', context)


from django.views.generic import TemplateView

@method_decorator(csrf_exempt, name='dispatch')
class ParcelView(TemplateView):
    template_name = 'agri/parcel_viewer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dates'] = self.get_available_dates()
        context['initial_date'] = context['dates'][0]

        processor = ParcelImageProcessor(context['initial_date'],4,4)
        context['rgb_image_path'] = processor.save_rgb_image()
        raw_grid = processor.create_pixel_grid()  # Appel à votre fonction existante

        # Validation Pydantic
        try:
            validated_grid = [GridCellSchema.model_validate(cell).model_dump() for cell in raw_grid]
        except ValidationError as e:
            logger.error("Erreur de validation : %s", e)
            return HttpResponseServerError()
        pixel_grid = processor.serialize_grid(raw_grid)
        print('pixel_grid', pixel_grid)
        # Récupération des données structurées
        grid_session_data = processor.get_grid_ids_and_data(raw_grid)

        # Stockage direct dans la session comme vous le souhaitez
        self.request.session['loaded_ids'] = grid_session_data['ids']
        self.request.session['grid_cells'] = grid_session_data['data']
        self.request.session.modified = True

        context['pixel_grid'] = pixel_grid

        return context



    def get_available_dates(self):
        tiff_dir = os.path.join(settings.STATIC_ROOT, 'satellite_data', '12bands')
        dates = []
        for file in os.listdir(tiff_dir):
            if file.endswith('12band.TIFF'):
                date = file.split('_')[0]  # Extrait la date du nom de fichier
                dates.append(date)
        return sorted(dates)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                action = request.POST.get('action')
                if action == 'change_date':
                    date = request.POST.get('date')
                    column_size = request.POST.get('column_size')
                    row_size = request.POST.get('row_size')

                    # Création et sauvegarde de la nouvelle image
                    processor2 = ParcelImageProcessor(date, int(column_size), int(row_size))
                    rgb_image_path = processor2.save_rgb_image()

                    raw_grid2 = processor2.create_pixel_grid()
                    pixel_grid2 = processor2.serialize_grid(raw_grid2)
                    # Récupération des données structurées
                    grid_session_data = processor2.get_grid_ids_and_data(raw_grid2)
                    # Réinitialisation complète
                    print('pixel_grid2', pixel_grid2)
                    # Stockage direct dans la session comme vous le souhaitez
                    try:
                        self.request.session.flush()
                    except:
                        print('error flush')
                    try:
                        self.request.session['loaded_ids'] = grid_session_data['ids']
                        self.request.session['grid_cells'] = grid_session_data['data']
                        print('icicici',self.request.session['grid_cells'])
                    except:
                        print("cant insert data")
                        try:
                            self.request.session['loaded_ids'].update(grid_session_data['ids'])
                            self.request.session['grid_cells'].update(grid_session_data['data'])
                            print('update successfull')
                        except:
                            print("cant update data")

                    return JsonResponse({
                            'rgb_image_path': rgb_image_path,
                            'pixel_grid': pixel_grid2  # Suppression de la sérialisation superflue
                        }, safe=False)

                elif action == 'get_zone_by_id':
                    cell_id = request.POST.get('cell_id')
                    print('cell id', cell_id)
                    date = request.POST.get('date')
                    column_size = request.POST.get('column_size')
                    row_size = request.POST.get('row_size')
                    print('date', date)
                    # Vérifier la cohérence de la date
                    current_grid = request.session.get('grid_cells')
                    print('là test de ouf',current_grid)
                    cell_data = current_grid.get(cell_id)
                    print('cell data',cell_data)
                    if not cell_data:
                        return JsonResponse({'error': 'Zone non trouvée'}, status=404)

                    processor3 = ParcelImageProcessor(date, int(column_size), int(row_size))

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