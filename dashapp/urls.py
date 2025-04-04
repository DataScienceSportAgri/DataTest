from django.urls import path
from . import views

app_name = 'dashapp'

urlpatterns = [
    path('parcelles/', views.dash_view, name='parcelle_analysis'),
path('api/ml-pipeline/', views.process_ml_pipeline, name='ml_pipeline'),

path('api/save-points/', views.save_points, name='save_points'),
    path('ml-results/<uuid:train_result_id>/<uuid:pred_result_id>/',  # Ajout des UUID
         views.ml_results_view,
         name='ml_results'),
]