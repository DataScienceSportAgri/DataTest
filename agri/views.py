from venv import logger

from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from pydantic import ValidationError

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


class ParcelView(TemplateView):
    template_name = 'agri/parcel_viewer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dates'] = self.get_available_dates()
        context['initial_date'] = context['dates'][0]

        processor = ParcelImageProcessor(context['initial_date'],4,4)
        context['rgb_image_path'] = processor.save_rgb_image()
        raw_grid = processor.create_pixel_grid()  # Appel à votre fonction existante
        print('raw grid', raw_grid)
        # Validation Pydantic
        try:
            validated_grid = [GridCellSchema.model_validate(cell).model_dump() for cell in raw_grid]
        except ValidationError as e:
            logger.error("Erreur de validation : %s", e)
            return HttpResponseServerError()
        pixel_grid = processor.serialize_grid(raw_grid)
        # Récupération des données structurées
        grid_session_data = processor.get_grid_ids_and_data(raw_grid)

        # Stockage direct dans la session comme vous le souhaitez
        self.request.session['loaded_ids'] = grid_session_data['ids']
        self.request.session['grid_cells'] = grid_session_data['data']
        self.request.session.modified = True
        print('pixel grid', pixel_grid)

        context['pixel_grid'] = pixel_grid


        return context

    def _store_grid_session(self, grid_payload):
        """Stockage structuré dans la session"""
        session_key = f"grid_{grid_payload['metadata']['date']}"
        self.request.session[session_key] = {
            'metadata': grid_payload['metadata'],
            'cells': grid_payload['cells']
        }
        self.request.session.modified = True



    def get_available_dates(self):
        tiff_dir = os.path.join(settings.STATIC_ROOT, 'satellite_data', '12bands')
        dates = []
        for file in os.listdir(tiff_dir):
            if file.endswith('12band.TIFF'):
                date = file.split('_')[0]  # Extrait la date du nom de fichier
                dates.append(date)
        return sorted(dates)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                action = request.POST.get('action')
                date = request.POST.get('date')

                if action == 'change_date':
                    # Création et sauvegarde de la nouvelle image
                    processor = ParcelImageProcessor(date)
                    image_path = processor.save_rgb_image()
                    pixel_gird = processor.create_pixel_grid()
                    return JsonResponse({
                        'rgb_image_path': image_path,
                        'pixel_gird': pixel_gird
                    })

                elif action == 'get_zone_by_id':
                    cell_id = request.POST.get('cell_id')
                    date = request.POST.get('date')

                    # Vérifier la cohérence de la date
                    current_grid = request.session.get('grid_cells')
                    if not current_grid or current_grid['metadata']['date'] != date:
                        raise ValueError("Session expirée ou date incohérente")
                    # Récupération directe depuis les données de session

                    cell_data = current_grid.get(cell_id)

                    if not cell_data:
                        return JsonResponse({'error': 'Zone non trouvée'}, status=404)
                    processor = ParcelImageProcessor(cell_data['date'], 4, 4)
                    zone_data = processor.get_zone_data(cell_data)
                    return JsonResponse({
                        'coordinates': zone_data['coordinates'],
                        'bands': zone_data['bands']
                    })


            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'error': 'Requête non autorisée'}, status=400)