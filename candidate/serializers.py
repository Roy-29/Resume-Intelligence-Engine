"""DRF Serializers for Candidate API."""
from rest_framework import serializers
from .models import CandidateAnalysis, JobRole


class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = ['id', 'title', 'description', 'required_skills', 'category']


class CandidateAnalysisSerializer(serializers.ModelSerializer):
    selected_job_role_title = serializers.CharField(
        source='selected_job_role.title', read_only=True, default=''
    )
    score_label = serializers.CharField(read_only=True)

    class Meta:
        model = CandidateAnalysis
        fields = [
            'id', 'original_filename', 'uploaded_at',
            'candidate_name', 'email', 'phone',
            'extracted_skills', 'experience_years',
            'education_level', 'resume_category',
            'overall_score', 'skill_score', 'experience_score',
            'keyword_score', 'education_score', 'completeness_score',
            'score_label',
            'selected_job_role_title',
            'job_match_percentage', 'matched_skills', 'missing_skills',
            'suggestions', 'career_paths', 'share_token',
        ]


class ResumeUploadSerializer(serializers.Serializer):
    resume = serializers.FileField()
    job_role = serializers.CharField(required=False, default='')
