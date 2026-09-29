from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.team_list_view, name='list'),
    path('<int:pk>/', views.team_detail_view, name='detail'),
    path('<int:pk>/delete/', views.team_delete_view, name='delete'),
    path('<int:pk>/add-player/', views.add_player_view, name='add_player'),
    path('<int:pk>/remove-player/<int:player_pk>/', views.remove_player_view, name='remove_player'),
]
