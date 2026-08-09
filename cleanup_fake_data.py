import sys
import os

# Set up Django environment
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from recruiter.models import JobPosting, JobApplication
from candidate.models import CandidateAnalysis

User = get_user_model()

print("Starting cleanup of fake ML seed data...")

# 1. Find the ai_trainer user
try:
    trainer = User.objects.get(username='ai_trainer')
    
    # 2. Find the specific training job
    training_job = JobPosting.objects.filter(title="Senior AI Architect (Training Set)", recruiter=trainer).first()
    
    if training_job:
        app_count = training_job.applications.count()
        print(f"Deleting Job Posting: '{training_job.title}' and its {app_count} applications...")
        training_job.delete() # Cascasde will handle applications
    
    # 3. Delete CandidateAnalysis records created by the trainer
    analyses = CandidateAnalysis.objects.filter(user=trainer)
    analysis_count = analyses.count()
    print(f"Deleting {analysis_count} Candidate Analysis records created by 'ai_trainer'...")
    analyses.delete()
    
    # 4. Delete the trainer user if desired
    print(f"Removing user 'ai_trainer'...")
    trainer.delete()
    
    print("Cleanup complete! Your database is now clean.")

except User.DoesNotExist:
    print("❌ User 'ai_trainer' not found. It seems the data was already removed or never created.")
except Exception as e:
    print(f"❌ Error during cleanup: {str(e)}")
