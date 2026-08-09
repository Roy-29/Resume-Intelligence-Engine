from django.db import models
from django.contrib.auth.models import User
from candidate.models import JobRole, CandidateAnalysis

class JobPosting(models.Model):
    """A specific job posted by a recruiter."""
    role = models.ForeignKey(JobRole, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    recruiter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'dashboard_message',
                    'message': {
                        'event': 'new_job_created',
                        'job_id': self.pk,
                        'title': self.title
                    }
                }
            )

    def __str__(self):
        return f"{self.title} ({self.role.title})"


class JobApplication(models.Model):
    """Links a candidate's resume analysis to a specific job posting."""
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired')
    ]

    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate_analysis = models.ForeignKey(CandidateAnalysis, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='applied')
    ml_selection_probability = models.FloatField(default=0, help_text="XGBoost predicted probability of hiring")
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate_analysis.candidate_name} -> {self.job_posting.title}"


class MLModelVersion(models.Model):
    """Tracks training runs of the ML selection model."""
    version_id = models.CharField(max_length=100, unique=True)
    trained_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    
    # Metrics
    accuracy = models.FloatField(default=0)
    roc_auc = models.FloatField(default=0)
    confusion_matrix_json = models.JSONField(default=dict)
    
    file_path = models.CharField(max_length=500, help_text="Path to .joblib file")

    def __str__(self):
        return f"Model {self.version_id} (Acc: {self.accuracy:.2f})"


class Interview(models.Model):
    """Tracks scheduled interviews for shortlisted candidates."""
    TYPE_CHOICES = [
        ('phone', 'Phone Screen'),
        ('video', 'Video Call'),
        ('onsite', 'On-site'),
        ('technical', 'Technical Round'),
        ('hr', 'HR Round'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    job_application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    scheduled_at = models.DateTimeField()
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='video')
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"Interview: {self.job_application.candidate_analysis.candidate_name} — {self.get_interview_type_display()}"


class RecruiterMessage(models.Model):
    """In-app messages from recruiters to candidates."""
    job_application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='messages')
    subject = models.CharField(max_length=300)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Message to {self.job_application.candidate_analysis.candidate_name}: {self.subject}"


class RecruiterProfile(models.Model):
    """Extended profile for recruiters with company and personal info."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')

    # Personal Information
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True, help_text="Short professional bio")
    profile_image = models.ImageField(upload_to='profile_images/recruiters/', blank=True, null=True)

    # Company Information
    company_name = models.CharField(max_length=200, blank=True)
    company_website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True, choices=[
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ])
    company_location = models.CharField(max_length=200, blank=True)

    # Professional Info
    job_title = models.CharField(max_length=200, blank=True, help_text="e.g. Senior Technical Recruiter")
    department = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=200, blank=True, help_text="e.g. Data Science, Backend Engineering")
    years_experience = models.PositiveIntegerField(default=0, help_text="Years in recruitment")

    # Social Links
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name or self.user.username} — {self.company_name or 'No Company'}"


class ModelTrainingReport(models.Model):
    """Stores metrics from manual ML model training runs."""
    model_name = models.CharField(max_length=100)
    training_dataset_size = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0)
    precision = models.FloatField(default=0)
    recall = models.FloatField(default=0)
    f1_score = models.FloatField(default=0)
    roc_auc = models.FloatField(default=0)
    cv_accuracy = models.FloatField(default=0, help_text="Cross-validation accuracy")
    confusion_matrix = models.JSONField(default=list)
    training_time = models.FloatField(default=0, help_text="Training time in seconds")
    is_best = models.BooleanField(default=False)
    model_file_path = models.CharField(max_length=500, blank=True)
    training_session = models.CharField(max_length=100, blank=True, help_text="Groups models trained together")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.model_name} — Acc: {self.accuracy:.2%} | F1: {self.f1_score:.2%}"

