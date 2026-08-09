"""recruitment URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('candidate/', include('candidate.urls')),
    path('api/candidate/', include('candidate.api_urls')),
    path('api/recruiter/', include('recruiter.api_urls')),
    path('api/', include('api.urls')),
    path('recruiter/', include('recruiter.urls')),
    
    # Unified Homepage Login View (mapped from candidate app)
    path('', lambda req: redirect('candidate:login')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
