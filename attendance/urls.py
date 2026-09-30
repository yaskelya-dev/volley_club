from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_matrix_view, name='list'),
    path('<int:pk>/delete/', views.training_delete_view, name='delete'),
]