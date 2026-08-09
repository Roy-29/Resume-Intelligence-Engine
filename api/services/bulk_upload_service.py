import os
from django.conf import settings
from rest_framework import status
from api.models import CentralizedResume

class BulkUploadService:
    """Service to handle storing multiple uploaded resumes."""

    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.jpg', '.jpeg', '.png'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    @classmethod
    def process_bulk_upload(cls, job, files, uploaded_via_public_link=False):
        """
        Validates and saves a list of InMemoryUploadedFile objects to CentralizedResume.
        Returns a dict with success count, fail count, and error messages.
        """
        success_count = 0
        failed_count = 0
        errors = []

        for f in files:
            # 1. Size Validation
            if f.size > cls.MAX_FILE_SIZE:
                failed_count += 1
                errors.append(f"{f.name}: Exceeds 10MB limit.")
                continue

            # 2. Extension Validation
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in cls.ALLOWED_EXTENSIONS:
                failed_count += 1
                errors.append(f"{f.name}: Unsupported file format {ext}.")
                continue

            # 3. Save to Centralized Storage
            try:
                # We save it with 'New' status, ready for bulk analysis later
                CentralizedResume.objects.create(
                    job=job,
                    candidate_name=f.name, # Default to filename until parsed
                    resume_file=f,
                    uploaded_via_public_link=uploaded_via_public_link,
                    status='New'
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"{f.name}: Internal save error - {str(e)}")

        return {
            "uploaded_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
            "message": "Bulk upload completed successfully" if failed_count == 0 else "Bulk upload finished with errors."
        }
