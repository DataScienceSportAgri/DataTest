"""DataTest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
# Configuration Dash

urlpatterns = [
# Configuration requise pour django-plotly-dash
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
    path('', views.home, name='home'),
    path('polls/', include('polls.urls')),
    path('agri/', include('agri.urls')),
    path('admin/', admin.site.urls),
    path('graph/', include('graph.urls')),
    path('bubble_sort/', include('bubble_sort.urls')),
    # Intégration de l'app Dash sous le préfixe 'agri/demo/'
    path('agri/demo/', include([
    path('', include('dashapp.urls', namespace='dashapp')),  # Correction clé
    path('/api/', include('dashapp.urls', 'api')),  # Inclusion du namespace API
    path('dash-components/', include('django_plotly_dash.urls')),  # Routes Dash
    ])),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)