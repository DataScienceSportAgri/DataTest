from django.shortcuts import render


def home(request):
    context = {
        'message': 'Cette application vous aide à gérer votre exploitation agricole.'
    }
    return render(request, 'agri/app_presentation.html', context)



# Create your views here.
