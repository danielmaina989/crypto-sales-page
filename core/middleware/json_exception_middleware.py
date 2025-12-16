import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class JsonExceptionMiddleware:
    """Middleware that returns JSON error responses for API requests.

    Behavior:
    - If request path starts with /api/ or client accepts application/json, return JSON error.
    - For other requests, re-raise exception so Django shows normal error pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            # Determine if client expects JSON
            accept = request.META.get('HTTP_ACCEPT', '')
            is_api_path = request.path.startswith('/api/')
            wants_json = 'application/json' in accept or is_api_path

            logger.exception('Unhandled exception processing request: %s %s', request.method, request.path)

            if wants_json:
                payload = {
                    'status': 'error',
                    'message': 'internal server error',
                    'detail': str(exc),
                }
                return JsonResponse(payload, status=500)
            # not JSON, re-raise so Django handles it (debug pages in DEBUG mode)
            raise
