from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Applies security response headers to all responses.
    """

    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Don't allow embedding private areas in iframes, but allow PDF viewer if needed
        if not response.has_header("X-Frame-Options"):
            response["X-Frame-Options"] = "SAMEORIGIN"

        return response
