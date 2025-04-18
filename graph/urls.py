from django.urls import path

from . import views

app_name = 'graph'
urlpatterns = [
    path('', views.CourseList.as_view(), name='index'),
    path('course/<int:pk>/resultats/', views.ResultatsCourseView.as_view(), name='resultats_course'),
    path(r'vitesse-distribution/', views.VitesseDistributionView.as_view(), name='vitesse_distribution'),

    path('score-distribution/', views.ScoreDistributionView.as_view(), name='score_distribution'),
    path('stat-global/', views.StatGlobalView.as_view(), name='stat_global'),
    path('coureur/<int:pk>/', views.CoureurDetailView.as_view(), name='coureur_detail'),
    path('search/', views.SearchResultsView.as_view(), name='search_results'),
    ]