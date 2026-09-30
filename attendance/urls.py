from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_matrix_view, name='list'),
    path('<int:pk>/delete/', views.training_delete_view, name='delete'),
    path('reasons/<int:pk>/edit/', views.reason_edit_view, name='reason_edit'),
    path('reasons/<int:pk>/delete/', views.reason_delete_view, name='reason_delete'),
]