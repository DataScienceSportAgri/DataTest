from django.shortcuts import render
from graph.models import HalfMarathon
def home(request):
    return render(request, 'home.html')

def halfmarathon_list(request):
    halfmarathons = HalfMarathon.objects.all()
    return render(request, 'templates/halfmarathon_list.html', {'halfmarathons': halfmarathons})