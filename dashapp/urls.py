from django.urls import path
from . import views

app_name = 'dashapp'

urlpatterns = [
    path('parcelles/', views.dash_view, name='parcelle_analysis'),

]