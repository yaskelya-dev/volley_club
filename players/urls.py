from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('', views.player_list_view, name='list'),
    path('<int:pk>/', views.player_detail_view, name='detail'),
    path('<int:pk>/delete/', views.player_delete_view, name='delete'),
]
