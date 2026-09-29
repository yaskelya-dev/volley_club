from django.contrib import admin
from django.urls import path, include
from home import views as home_views

urlpatterns = [
    path('', include('home.urls')),
    path('users/', include('users.urls')),
    path('teams/', include('teams.urls')),
    path('players/', include('players.urls')),
    path('admin-panel/', admin.site.urls),
]

handler404 = home_views.page_not_found_view
handler500 = home_views.server_error_view
handler403 = home_views.permission_denied_view
handler400 = home_views.bad_request_view