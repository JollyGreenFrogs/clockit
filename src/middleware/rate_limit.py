"""
Rate limiting middleware for API protection
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import logging

logger = logging.getLogger(__name__)


def get_user_or_ip(request: Request) -> str:
    """
    Get user ID if authenticated, otherwise IP address.
    This allows different rate limits for authenticated vs unauthenticated users.
    """
    # Try to get user from auth token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            # Import here to avoid circular dependencies
            from database.connection import get_db
            from auth.services import AuthService
            
            token = auth_header.split(" ")[1]
            db = next(get_db())
            auth_service = AuthService(db)
            payload = auth_service.verify_token(token)
            if payload and payload.get("sub"):
                return f"user:{payload.get('sub')}"
        except Exception:
            # If token verification fails, fall back to IP
            pass
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Create limiter instance
limiter = Limiter(key_func=get_user_or_ip)


def setup_rate_limiting(app):
    """Configure rate limiting for the application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled")
