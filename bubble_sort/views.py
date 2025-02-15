from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.http import JsonResponse
import json

from polls.views import DetailView
from .models import ClassementBubble, Bubble, ColorPreset
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.urls import reverse


class ClassementListView(LoginRequiredMixin, View):
    def get(self, request):
        classements = ClassementBubble.objects.filter(user=request.user)
        return render(request, 'bubble_sort/bubbleclassement_list.html', {'classements': classements})

@method_decorator(csrf_exempt, name='dispatch')
class BubbleListView(LoginRequiredMixin, View):

    def get(self, request, classement_id):
        classement = get_object_or_404(ClassementBubble, id=classement_id, user=request.user)
        bubbles = classement.bubbles.all()
        color_presets = ColorPreset.objects.all()
        color_start = classement.color_start.id
        end_color = classement.color_end.id
        print('id color start', color_start)
        print('id color end', end_color)
        return render(request, 'bubble_sort/bubble_list.html', {'classement': classement, 'bubbles': bubbles, 'color_presets': color_presets, 'color_start':color_start, 'end_color':end_color})

    def post(self, request, classement_id):
        classement = get_object_or_404(ClassementBubble, id=classement_id, user=request.user)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

        action = data.get('action')

        if action == 'update_positions':
            # Ne traiter que les positions
            positions = data.get('positions', [])
            for index, bubble_id in enumerate(positions):  # Liste d'IDs
                try:
                    bubble = classement.bubbles.get(id=bubble_id)
                    bubble.position = index
                    bubble.save()
                except Bubble.DoesNotExist:
                    print(f"Bulle {bubble_id} non trouvée")
            return JsonResponse({'status': 'success', 'message': 'Ordre mis à jour'})

        elif action == 'add_bubble':

            new_bubble = Bubble.objects.create(
                classement=classement,
                content='',
                position=classement.bubbles.count(),
                width=1000,  # Valeurs par défaut cohérentes
                height=150
            )

            return JsonResponse({

                'status': 'success',
                'id': new_bubble.id,
                'position': new_bubble.position,
                'width': new_bubble.width,
                'height': new_bubble.height
            })

        elif action == 'update_name':
            new_name = data.get('classement_name')
            classement.name = new_name
            classement.save()
            return JsonResponse({'status': 'success', 'message': 'Classement name updated'})


        elif action == 'save_bubble_data':
            try:
                bubble = classement.bubbles.get(id=data['bubble_id'])
                field = data['field']
                value = data['value']
                if field == 'content':
                    bubble.content = value
                elif field == 'title':
                    bubble.title = value
                else:
                    return JsonResponse({'status': 'error', 'message': 'Champ invalide'}, status=400)
                bubble.save()
                return JsonResponse({'status': 'success'})
            except Bubble.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Bulle non trouvée'}, status=404)

        elif action == 'delete_bubble':
            print("Delete bubble action received")
            bubble_id = data.get('bubble_id')
            print(f"Attempting to delete bubble with id: {bubble_id}")
            try:
                bubble = classement.bubbles.get(id=bubble_id)
                bubble.delete()
                print("Bubble deleted successfully")
                return JsonResponse({'status': 'success', 'message': 'Bubble deleted'})
            except Bubble.DoesNotExist:
                print("Bubble not found")
                return JsonResponse({'status': 'error', 'message': 'Bubble not found'}, status=404)
                # Dans BubbleListView.post


        elif action == 'resize_bubble':

            try:

                bubble_id = int(data['bubble_id'])  # Conversion explicite
                width = int(data['width'])
                height = int(data['height'])
                bubble = classement.bubbles.get(id=bubble_id)
                bubble.width = width
                bubble.height = height
                bubble.save(update_fields=['width', 'height'])  # Force la sauvegarde
                print(f"SAUVEGARDE RÉUSSIE : Bulle {bubble_id} → {width}x{height}")
                return JsonResponse({'status': 'success'})

            except (KeyError, ValueError, Bubble.DoesNotExist) as e:
                print(f"ERREUR : {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


        elif action == 'update_colors':

            start_color_id = data.get('start_color_id')

            end_color_id = data.get('end_color_id')

            try:

                start_color = ColorPreset.objects.get(id=start_color_id)
                end_color = ColorPreset.objects.get(id=end_color_id)
                # Correction des noms de champs
                classement.color_start = start_color  # Au lieu de start_color
                classement.color_end = end_color  # Au lieu de end_color
                classement.save(update_fields=['color_start', 'color_end'])
                return JsonResponse({
                    'status': 'success',
                    'start_color': start_color.color_code,
                    'end_color': end_color.color_code
                })
            except ColorPreset.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid color'}, status=400)
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)


class UpdatePositionsView(LoginRequiredMixin, View):
    @csrf_exempt
    def post(self, request, classement_id):
        classement = get_object_or_404(ClassementBubble, id=classement_id)
        positions = request.POST.get('positions').split(',')

        for index, bubble_id in enumerate(positions):
            bubble = classement.bubbles.get(id=bubble_id)
            bubble.position = index
            bubble.save()

        return JsonResponse({'status': 'success', 'message': 'Positions updated'})

class CreateClassementView(LoginRequiredMixin, CreateView):
    model = ClassementBubble
    fields = ['name']
    template_name = 'bubble_sort/create_classement.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        return reverse('bubble_list', kwargs={'classement_id': self.object.id})


