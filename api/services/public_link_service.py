from api.models import PublicUploadLink
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class PublicLinkService:
    @classmethod
    def generate_link(cls, job, max_limit=100, expires_in_days=30):
        """Creates a secure upload token attached to a specific Job."""
        try:
            expiration = timezone.now() + timezone.timedelta(days=expires_in_days)
            
            link = PublicUploadLink.objects.create(
                job=job,
                max_upload_limit=max_limit,
                expires_at=expiration
            )
            
            # The domain would realistically be generated from settings or Request Sites framework
            # Return just the token and let frontend handle the FQDN
            return {
                "success": True,
                "token": str(link.token),
                "expires_at": str(link.expires_at)
            }
        except Exception as e:
            logger.error(f"Generate Link Error: {str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def validate_and_increment_token(cls, token):
        """Validates if a public link is still active and increments upload count."""
        try:
            link = PublicUploadLink.objects.get(token=token)
            
            if not link.is_valid():
                return False, None
                
            link.current_upload_count += 1
            link.save()
            return True, link.job
            
        except PublicUploadLink.DoesNotExist:
            return False, None
        except Exception as e:
            logger.error(f"Validate Token Error: {str(e)}")
            return False, None
