"""
Security middleware for HTTP security headers and HTTPS enforcement
"""

import os
from fastapi import Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from ..config import Config
except ImportError:
    from config import Config


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Strict-Transport-Security (HSTS) - only in production
        if Config.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Content-Security-Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://static.cloudflareinsights.com 'sha512-z4PhNX7vuL3xVChQ1m2AB9Yg5AULVxXcg/SpIdNs6c5H0NE8XYXysP+DGNKHfuwvY7kxvUdBeoGlODJ6+SfaPg=='",
            "style-src 'self' 'unsafe-inline' 'unsafe-hashes' 'sha256-+OsIn6RhyCZCUkkvtHxFtP0kU3CGdGeLjDd9Fzqdl3o='",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https://cloudflareinsights.com https://static.cloudflareinsights.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection (legacy, but doesn't hurt)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        # Remove sensitive server headers (if they exist)
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        return response


def setup_security_middleware(app):
    """Configure security middleware for the application"""

    # HTTPS redirect in production only when not behind a reverse proxy/tunnel
    # Skip HTTPS redirect if we're behind Cloudflare tunnel or similar proxy
    if Config.ENVIRONMENT == "production" and not os.getenv("DISABLE_HTTPS_REDIRECT", False):
        app.add_middleware(HTTPSRedirectMiddleware)

    # Security headers for all environments
    app.add_middleware(SecurityHeadersMiddleware)
