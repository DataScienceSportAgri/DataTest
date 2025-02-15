from django.urls import path
from .views import ClassementListView, BubbleListView, UpdatePositionsView, CreateClassementView
urlpatterns = [
    path('', ClassementListView.as_view(), name='bubbleclassement_list'),
    path('create/', CreateClassementView.as_view(), name='create_classement'),
    path('classement/<int:classement_id>/', BubbleListView.as_view(), name='bubble_list'),
    path('classement/<int:classement_id>/update_positions/', UpdatePositionsView.as_view(), name='update_positions')
]
