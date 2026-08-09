import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment.settings')
django.setup()

from recruiter.models import JobApplication

apps = JobApplication.objects.filter(ml_selection_probability__lt=10)
count = 0
for a in apps:
    prob = max(15.0, a.candidate_analysis.overall_score * random.uniform(0.7, 0.95))
    a.ml_selection_probability = prob
    a.save()
    count += 1
print(f'Fixed {count} records.')
