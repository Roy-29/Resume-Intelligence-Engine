import time
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.middleware import get_user
import logging

logger = logging.getLogger(__name__)

class CachedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.time()
        if not hasattr(request, 'session'):
            return self.get_response(request)

        def get_cached_user():
            session_key = request.session.session_key
            if not session_key:
                return get_user(request)
            cache_key = f'auth_user_{session_key}'
            user = cache.get(cache_key)
            if user is None:
                user = get_user(request)
                cache.set(cache_key, user, 600)  # Cache for 10 minutes
            return user

        request.user = SimpleLazyObject(get_cached_user)
        response = self.get_response(request)
        t1 = time.time()
        print(f"Request to {request.path} took {t1 - t0:.3f}s")
        return response
