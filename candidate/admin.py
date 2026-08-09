from django.contrib import admin
from .models import JobRole, CandidateAnalysis


@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'avg_salary_min', 'avg_salary_max')
    search_fields = ('title', 'category')


@admin.register(CandidateAnalysis)
class CandidateAnalysisAdmin(admin.ModelAdmin):
    list_display = ('candidate_name', 'email', 'overall_score', 'resume_category', 'uploaded_at')
    list_filter = ('resume_category', 'uploaded_at')
    search_fields = ('candidate_name', 'email')
    readonly_fields = ('share_token',)
