from django.urls import path
from . import views

app_name = 'dashapp'

urlpatterns = [
    path('parcelles/', views.dash_view, name='parcelle_analysis'),
    path('api/save-points/', views.save_points, name='save_points'),
    path('api/get-points/', views.get_points, name='get_points'),
    path('api/ml-pipeline/', views.process_ml_pipeline, name='ml_pipeline'),
]