import uuid
from django.db import models
from django.core.validators import FileExtensionValidator


class JobRole(models.Model):
    """Stores job roles with required skills and descriptions."""
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    required_skills = models.JSONField(default=list, help_text="List of required skill strings")
    category = models.CharField(max_length=100, blank=True)
    avg_salary_min = models.IntegerField(default=0, help_text="Minimum avg salary in USD")
    avg_salary_max = models.IntegerField(default=0, help_text="Maximum avg salary in USD")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


from django.contrib.auth.models import User

class CandidateAnalysis(models.Model):
    """Stores a single candidate resume analysis."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='analyses')

    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('management', 'Management'),
        ('fresher', 'Fresher'),
        ('other', 'Other'),
    ]

    # Upload
    resume_file = models.FileField(
        upload_to='resumes/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'])]
    )
    original_filename = models.CharField(max_length=300, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Extracted Data
    full_text = models.TextField(blank=True)
    candidate_name = models.CharField(max_length=300, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    extracted_skills = models.JSONField(default=list)
    experience_years = models.FloatField(default=0)
    education_level = models.CharField(max_length=100, blank=True)
    resume_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')

    # Scores (0-100)
    overall_score = models.FloatField(default=0)
    skill_score = models.FloatField(default=0)
    experience_score = models.FloatField(default=0)
    keyword_score = models.FloatField(default=0)
    education_score = models.FloatField(default=0)
    completeness_score = models.FloatField(default=0)

    # Job Matching
    selected_job_role = models.ForeignKey(
        JobRole, null=True, blank=True, on_delete=models.SET_NULL
    )
    job_match_percentage = models.FloatField(default=0)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)

    # AI Suggestions
    suggestions = models.JSONField(default=list)
    career_paths = models.JSONField(default=list)

    # Sharing
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Candidate Analyses'

    def __str__(self):
        return f"{self.candidate_name or 'Unknown'} — {self.uploaded_at:%Y-%m-%d}"

    @property
    def score_label(self):
        if self.overall_score >= 80:
            return 'Excellent'
        elif self.overall_score >= 60:
            return 'Good'
        elif self.overall_score >= 40:
            return 'Average'
        else:
            return 'Needs Improvement'

    @property
    def score_color(self):
        if self.overall_score >= 80:
            return '#10b981'
        elif self.overall_score >= 60:
            return '#f59e0b'
        elif self.overall_score >= 40:
            return '#f97316'
        else:
            return '#ef4444'


class Notification(models.Model):
    """In-app notifications for candidates (status changes, messages, etc)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{'🔵' if not self.is_read else '⚪'} {self.message[:50]}"


class UserProfile(models.Model):
    """Stores user role (candidate or recruiter) and links to Django User."""
    ROLE_CHOICES = [
        ('candidate', 'Candidate'),
        ('recruiter', 'Recruiter'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_recruiter(self):
        return self.role == 'recruiter'

    @property
    def is_candidate(self):
        return self.role == 'candidate'


class CandidateProfile(models.Model):
    """Extended profile for candidates with personal, education, and professional info."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')

    # Personal Information
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, help_text="Short professional summary")
    location = models.CharField(max_length=200, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/candidates/', blank=True, null=True)

    # Education
    highest_education = models.CharField(max_length=50, blank=True, choices=[
        ('high_school', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelors', "Bachelor's Degree"),
        ('masters', "Master's Degree"),
        ('phd', 'PhD / Doctorate'),
        ('other', 'Other'),
    ])
    university = models.CharField(max_length=200, blank=True)
    field_of_study = models.CharField(max_length=200, blank=True, help_text="e.g. Computer Science")
    graduation_year = models.PositiveIntegerField(null=True, blank=True)

    # Professional
    current_job_title = models.CharField(max_length=200, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    preferred_role = models.CharField(max_length=200, blank=True, help_text="e.g. ML Engineer, Data Scientist")
    expected_salary = models.CharField(max_length=50, blank=True, help_text="e.g. $80k-$100k")
    availability = models.CharField(max_length=50, blank=True, choices=[
        ('immediate', 'Immediately'),
        ('2_weeks', '2 Weeks Notice'),
        ('1_month', '1 Month Notice'),
        ('3_months', '3 Months Notice'),
        ('not_looking', 'Not Actively Looking'),
    ])

    # Social Links
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name or self.user.username} — Candidate Profile"


# Auto-create UserProfile when a User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

