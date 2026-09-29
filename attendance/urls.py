from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.training_list_view, name='list'),
    path('<int:pk>/', views.training_detail_view, name='detail'),
    path('<int:pk>/delete/', views.training_delete_view, name='delete'),
    path('reasons/', views.reason_list_view, name='reasons'),
]
