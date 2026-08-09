import os
import django
from django.core.management.base import BaseCommand
import random
from django.contrib.auth import get_user_model
from recruiter.models import JobPosting, JobApplication
from candidate.models import CandidateAnalysis, JobRole
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with 1000 realistic dummy candidate profiles and triggers ML training.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting the ML Data Seeding Process...'))

        # Ensure we have a Recruiter User
        recruiter, created = User.objects.get_or_create(username='ai_trainer', defaults={'email': 'trainer@ai.com'})
        if created:
            recruiter.set_password('trainer_pass')
            recruiter.save()

        # Ensure we have a Job Role
        role, _ = JobRole.objects.get_or_create(title="Senior Machine Learning Engineer", defaults={'required_skills': ['python', 'aws', 'ml']})
        
        # Create a Job Posting to attach candidates to
        job, _ = JobPosting.objects.get_or_create(
            title="Senior AI Architect (Training Set)",
            recruiter=recruiter,
            role=role,
            defaults={
                'description': "We represent a fast-growing tech firm looking for a senior AI Engineer.",
                'is_active': False
            }
        )

        total_to_create = 1000
        self.stdout.write(f'Generating {total_to_create} realistic applications for job: {job.title}')

        # Define education levels
        education_levels = ['Bachelors', 'Masters', 'PhD', 'Bootcamp', 'Self-Taught']

        applications_created = 0
        now = timezone.now()

        for i in range(total_to_create):
            # 1. Generate Realistic Variance
            # A healthy ML model needs a clear distinction between "good" an "bad" candidates
            is_good_candidate = random.choice([True, False])

            if is_good_candidate:
                exp_years = random.uniform(4.0, 15.0)
                edu = random.choices(education_levels, weights=[40, 40, 15, 5, 0])[0]
                overall_score = random.uniform(70.0, 99.0)
                semantic_score = random.uniform(0.7, 0.99)
                skills_match = overall_score * random.uniform(0.9, 1.1) 
                # Hired mostly if overall > 85, heavily influenced by ML Pipeline feature extraction
                status = 'hired' if overall_score > 85 and random.random() > 0.3 else 'interviewed'
            else:
                exp_years = random.uniform(0.0, 5.0)
                edu = random.choices(education_levels, weights=[50, 20, 0, 20, 10])[0]
                overall_score = random.uniform(20.0, 65.0)
                semantic_score = random.uniform(0.1, 0.6)
                skills_match = overall_score * random.uniform(0.8, 1.2)
                # Almost always rejected if score < 65
                status = 'rejected' if random.random() > 0.1 else 'reviewed'

            # Keep scores within boundaries
            overall_score = min(99.9, max(0.1, overall_score))
            semantic_score = min(1.0, max(0.0, semantic_score))
            skills_match = min(100.0, max(0.0, skills_match))

            # Create Analysis
            analysis = CandidateAnalysis.objects.create(
                user=recruiter, # Mock user
                candidate_name=f"Generated Candidate #{i}",
                email=f"candidate_{i}@example.com",
                selected_job_role=role,
                experience_years=exp_years,
                education_level=edu,
                overall_score=overall_score,
                extracted_skills={'Python': 1, 'ML': 1} if is_good_candidate else {'HTML': 1}
            )

            # Create Application
            # Scatter the application dates so CEO charts look nice
            applied_date = now - timedelta(days=random.randint(0, 180))
            
            # Predict dummy probability immediately so they show up on dashboards
            dummy_prob = overall_score if is_good_candidate else (overall_score * 0.8)

            JobApplication.objects.create(
                job_posting=job,
                candidate_analysis=analysis,
                status=status,
                applied_at=applied_date,
                ml_selection_probability=dummy_prob
            )

            applications_created += 1
            if applications_created % 100 == 0:
                self.stdout.write(f'Created {applications_created} / {total_to_create} records...')

        self.stdout.write(self.style.SUCCESS(f'Successfully created {applications_created} candidate records.'))
        self.stdout.write(self.style.WARNING('Now triggering XGBoost ML Pipeline... please wait.'))

        # 2. Trigger the ML Pipeline
        # We run it synchronously here so the script waits for it to finish and we can see the result
        from recruiter.ml_pipeline import XGBoostPipeline
        try:
            pipeline = XGBoostPipeline()
            success, version = pipeline.train_and_evaluate(save_model=True)
            if success:
                self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
                self.stdout.write(self.style.SUCCESS(f'✅ ML Pipeline Training COMPLETE!'))
                self.stdout.write(self.style.SUCCESS(f'Model Verson: {version.version_id}'))
                self.stdout.write(self.style.SUCCESS(f'Accuracy: {version.accuracy}%'))
                self.stdout.write(self.style.SUCCESS(f'ROC AUC: {version.roc_auc}'))
                self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
            else:
                 self.stdout.write(self.style.ERROR('❌ ML Pipeline Training FAILED'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Critical ML Pipeline Error: {str(e)}'))
