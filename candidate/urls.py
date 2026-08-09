"""URL patterns for the Candidate module (HTML views)."""
from django.urls import path
from . import views

app_name = 'candidate'

urlpatterns = [
    path('upload/', views.upload_resume, name='upload'),
    path('<int:pk>/dashboard/', views.dashboard, name='dashboard'),
    path('<int:pk>/report/', views.report, name='report'),
    path('<int:pk>/report/pdf/', views.download_pdf, name='download_pdf'),
    path('<int:pk>/rematch/', views.rematch_job, name='rematch_job'),
    path('share/<uuid:token>/', views.share_report, name='share_report'),

    # Auth & Profile
    path('signup/', views.user_signup, name='signup'),
    path('login/', views.home_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    
    # Job Board
    path('jobs/', views.job_listings, name='jobs_list'),
    path('jobs/<int:pk>/apply/', views.apply_to_job, name='job_apply'),

    # Notifications & Messages — Unified Inbox
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('messages/', views.recruiter_messages, name='recruiter_messages'),

    # Smart Resume Builder
    path('resume-builder/', views.resume_builder, name='resume_builder'),
    path('resume-builder/enhance/', views.ai_enhance_bullet, name='ai_enhance_bullet'),

    # GitHub Analyzer
    path('github-analyzer/', views.github_analyzer, name='github_analyzer'),
    path('github-analyzer/fetch/', views.fetch_github_data, name='fetch_github_data'),
]
