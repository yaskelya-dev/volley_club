from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    path('', views.schedule_index, name='index'),
    path('refresh/<int:team_id>/', views.refresh_team, name='refresh_team'),
    path('remove/<int:team_id>/', views.remove_team_from_user, name='remove_team'),
]
