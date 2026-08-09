import os
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from recruiter.models import JobPosting

def public_resume_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'resumes/{instance.job.id}/public_uploads/{uuid.uuid4().hex}{ext}'

class PublicUploadLink(models.Model):
    """Secure unique link to allow public uploads to a specific job."""
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='public_links')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_upload_limit = models.IntegerField(default=100)
    current_upload_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.current_upload_count >= self.max_upload_limit:
            return False
        return True

    def __str__(self):
        return f"Link for {self.job.title} ({self.token})"


class CentralizedResume(models.Model):
    """Storage for raw resumes collected from bulk and public uploads before full processing."""
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Analyzed', 'Analyzed'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected')
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='centralized_resumes')
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    
    resume_file = models.FileField(
        upload_to=public_resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'])]
    )
    uploaded_via_public_link = models.BooleanField(default=False)
    
    extracted_text = models.TextField(blank=True, null=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    
    # Standard analysis results
    score = models.FloatField(default=0.0)
    fit_level = models.CharField(max_length=50, blank=True, null=True)
    
    # ML Manual Training results
    ml_predicted_score = models.FloatField(blank=True, null=True)
    ml_fit_category = models.CharField(max_length=50, blank=True, null=True)
    ml_model_used = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='New')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.candidate_name or f"Unknown ({self.id})"
        return f"{name} - {self.job.title}"
