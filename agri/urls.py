from django.urls import path, include
from . import views
import dash_apps.parcel_dash # Import explicite nécessaire pour
from django.conf import settings
from django.conf.urls.static import static
from django_plotly_dash import DjangoDash
# Configuration Dash

urlpatterns = [
    path('', views.home, name='app_presentation'),
    path('demo/', views.ParcelView.as_view(), name='parcel_viewer'),
    path('ndvi/', views.NDVIView.as_view(), name='ndvi_view'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
