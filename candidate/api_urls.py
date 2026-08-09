"""API URL patterns for the Candidate module."""
from django.urls import path
from . import api_views

urlpatterns = [
    path('upload-resume/', api_views.api_upload_resume, name='api_upload_resume'),
    path('<int:pk>/report/', api_views.api_report, name='api_report'),
    path('<int:pk>/job-match/', api_views.api_job_match, name='api_job_match'),
    path('<int:pk>/market-insights/', api_views.api_market_insights, name='api_market_insights'),
]
