import sys
import os

# Set up Django environment
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment.settings')
import django
django.setup()

from candidate.models import JobRole
from candidate.data import JOB_ROLE_SKILLS

print(f"Populating JobRole database with {len(JOB_ROLE_SKILLS)} roles...")

created_count = 0
for title, data in JOB_ROLE_SKILLS.items():
    role_obj, created = JobRole.objects.get_or_create(
        title=title,
        defaults={
            'required_skills': data.get('required', []),
            'description': data.get('description', ''),
            'category': data.get('category', ''),
        }
    )
    if created:
        created_count += 1
        print(f"Created role: {title}")
    else:
        print(f"Role already exists: {title}")

print(f"Finished! Created {created_count} new roles.")
