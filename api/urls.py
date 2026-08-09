from django.urls import path
from . import views
from . import ml_views

urlpatterns = [
    # External Job API (Adzuna) Real-time Data
    path('external/jobs/', views.external_jobs, name='external_jobs'),
    path('external/salary/', views.external_salary, name='external_salary'),
    
    # External Market Trends (Google Trends via PyTrends)
    path('market/skill-trend/', views.market_skill_trend, name='market_skill_trend'),
    
    # AI Qualitative Feedback (OpenAI / HuggingFace)
    path('ai/resume-feedback/', views.ai_resume_feedback, name='ai_resume_feedback'),
    path('ai/skill-gap-analysis/', views.ai_skill_gap_analysis, name='ai_skill_gap_analysis'),
    
    # Phase 11: Bulk Processing & CV Collection
    path('resumes/bulk-upload/', views.bulk_upload_resumes, name='bulk_upload_resumes'),
    path('jobs/<int:job_id>/generate-upload-link/', views.generate_public_link, name='generate_public_link'),
    path('public-upload/<uuid:token>/', views.public_resume_upload, name='public_resume_upload'),
    path('resumes/bulk-analyze/', views.bulk_analyze_resumes, name='bulk_analyze_resumes'),
    
    path('job/<int:job_id>/resumes/', views.get_job_resumes, name='get_job_resumes'),
    path('resume/<int:resume_id>/analysis-report/', views.analysis_report, name='analysis_report'),
    path('resume/<int:resume_id>/<str:action>/', views.update_resume_status, name='update_resume_status'),

    # ML Manual Training
    path('recruiter/train-model/', ml_views.train_model, name='ml_train_model'),
    path('recruiter/model-reports/', ml_views.model_reports, name='ml_model_reports'),
    path('recruiter/model-reports/<int:pk>/', ml_views.model_report_detail, name='ml_model_report_detail'),
    path('recruiter/best-model/', ml_views.best_model, name='ml_best_model'),
]
