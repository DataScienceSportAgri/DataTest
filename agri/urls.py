from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
# Configuration Dash

urlpatterns = [
    path('', views.home, name='app_presentation'),
    path('demo/', views.ParcelView.as_view(), name='parcel_viewer'),
    path('ndvi/', views.NDVIView.as_view(), name='ndvi_view'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
