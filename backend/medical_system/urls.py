"""
URL configuration for medical_system project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # Endpoint di autenticazione
    path('health/', auth_views.health_check, name='health-check'),
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
