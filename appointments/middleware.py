# Create a new file: appointments/middleware.py
from django.utils.deprecation import MiddlewareMixin

class DebugMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if 'appointment' in request.path:
            print(f"URL: {request.path}")
            print(f"User: {request.user}")
            print(f"User authenticated: {request.user.is_authenticated}")
            if hasattr(request.user, 'user_type'):
                print(f"User type: {request.user.user_type}")
        return None