from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'recruiter'

urlpatterns = [
    # Recruiter Auth
    path('signup/', views.recruiter_signup, name='signup'),
    path('login/', views.recruiter_login, name='login'),
    path('logout/', views.recruiter_logout, name='logout'),
    
    path('dashboard/', views.recruiter_dashboard, name='ats_dashboard'),
    path('job/', RedirectView.as_view(pattern_name='recruiter:ats_dashboard', permanent=False), name='job_list'),
    path('profile/', views.recruiter_profile, name='profile'),
    path('job/create/', views.job_create, name='job_create'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('job/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('job/<int:pk>/toggle/', views.toggle_job_active, name='toggle_job_active'),
    path('application/<int:app_pk>/status/', views.change_application_status, name='change_status'),
    path('ceo-analytics/', views.ceo_analytics, name='ceo_analytics'),
    path('ml-models/', views.ml_model_metrics, name='ml_metrics'),
    path('ml-models/retrain/', views.retrain_model, name='retrain_model'),
    path('ml-models/download/', views.download_model_weights, name='download_weights'),

    # Feature 1: Interview Scheduling
    path('interview/schedule/<int:app_pk>/', views.schedule_interview, name='schedule_interview'),
    path('interviews/', views.interview_calendar, name='interview_calendar'),
    path('interview/<int:pk>/', views.interview_detail, name='interview_detail'),
    path('interview/<int:pk>/edit/', views.interview_edit, name='interview_edit'),
    path('interview/<int:pk>/cancel/', views.interview_cancel, name='interview_cancel'),
    path('interview/<int:pk>/complete/', views.interview_complete, name='interview_complete'),

    # Feature 2: Resume Comparison
    path('compare/', views.compare_candidates, name='compare_candidates'),

    # Feature 5: Recruiter Messaging
    path('message/<int:app_pk>/', views.send_message, name='send_message'),
    path('messages/', views.messages_hub, name='messages_hub'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/<int:pk>/edit/', views.message_edit, name='message_edit'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),

    # Resume File Viewing
    path('resume/<int:pk>/view/', views.view_resume_file, name='view_resume'),
    path('resume/<int:pk>/view/centralized/', views.view_resume_file,
         {'source': 'centralized'}, name='view_centralized_resume'),
    path('report/<int:pk>/', views.recruiter_report, name='ai_report'),

]
