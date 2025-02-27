from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='app_presentation'),
    path('demo/', views.ParcelView.as_view(), name='parcel_viewer'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)