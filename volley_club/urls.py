from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin-panel/', admin.site.urls),
]
