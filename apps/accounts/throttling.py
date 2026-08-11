from rest_framework.throttling import BaseThrottle
from django.core.cache import cache

class LoginFailThrottle(BaseThrottle):
    def allow_request(self, request, view):
        username = request.data.get('username') or request.data.get('email')
        ident = username if username else self.get_ident(request)
        self.cache_key = f"login_failures_{ident}"
        failure_count = cache.get(self.cache_key, 0)
        if failure_count >= 3:
            return False
        return True

    def wait(self):
        return 3600
