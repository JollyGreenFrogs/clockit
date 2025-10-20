"""
Authentication services for user management, JWT tokens, and security
"""

import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database.auth_models import AuditLog, User
from database.models import Category


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements
    Returns: (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    common_patterns = [
        r'(.)\1{3,}',  # Repeated characters (aaaa, 1111) - 4+ times
        r'(0123|1234|2345|3456|4567|5678|6789|7890)',  # Sequential numbers (4+ digits)
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            return False, "Password contains common patterns and is too predictable"
    
    # Check against common passwords
    common_passwords = [
        'password', 'password123', 'admin', 'admin123', 
        'qwerty', '123456', '12345678', 'password1', 'password1!',
        'welcome', 'welcome123', 'letmein'
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, ""


class AuthService:
    """Handles all authentication-related operations"""

    def __init__(self, db: Session):
        self.db = db
        self.secret_key = os.getenv("SECRET_KEY")
        if not self.secret_key:
            raise RuntimeError(
                "SECRET_KEY environment variable must be set. "
                "Generate one using: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        if len(self.secret_key) < 32:
            raise RuntimeError(
                "SECRET_KEY must be at least 32 characters long for security"
            )
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 7

    def create_user(
        self, email: str, username: str, password: str, full_name: Optional[str] = None
    ) -> User:
        """Create a new user account"""
        # Check if user exists
        existing_user_by_email = self.db.query(User).filter(User.email == email).first()
        existing_user_by_username = (
            self.db.query(User).filter(User.username == username).first()
        )

        if existing_user_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        if existing_user_by_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )

        # Hash password with bcrypt
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password.decode("utf-8"),
            full_name=full_name,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Create default categories for new user
        self._create_default_categories(str(user.id))

        # Set default currency for new user
        self._set_default_currency(str(user.id))

        # Log user creation
        self._log_action(str(user.id), "user_created", "user", str(user.id))

        return user

    def authenticate_user(
        self,
        email_or_username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Optional[User]:
        """Authenticate user with email/username and password"""
        user = (
            self.db.query(User)
            .filter(
                (User.email == email_or_username) | (User.username == email_or_username)
            )
            .first()
        )

        if not user:
            self._log_action(
                None,
                "login_failed",
                "user",
                email_or_username,
                details=f"User not found: {email_or_username}",
            )
            return None

        # Check if account is locked
        if user.is_account_locked():
            self._log_action(
                user.id,
                "login_blocked",
                "user",
                str(user.id),
                details="Account locked due to failed attempts",
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked due to multiple failed login attempts",
            )

        # Verify password
        if not bcrypt.checkpw(
            password.encode("utf-8"), user.hashed_password.encode("utf-8")
        ):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)

            self.db.commit()
            self._log_action(
                user.id,
                "login_failed",
                "user",
                str(user.id),
                details="Invalid password",
            )
            return None

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        self.db.commit()

        self._log_action(user.id, "login_success", "user", str(user.id))
        return user

    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {"sub": str(user.id), "exp": expire, "type": "refresh"}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.PyJWTError:
            return None

    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        if not payload or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return self.db.query(User).filter(User.id == user_id).first()

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Create new tokens
        access_token = self.create_access_token(user)
        new_refresh_token = self.create_refresh_token(user)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    def logout_user(self, user_id: str, token: str = None):
        """Logout user and invalidate session"""
        # In a production system, you might want to maintain a blacklist of tokens
        # For now, we just log the action
        self._log_action(user_id, "logout", "user", user_id)

    def _create_default_categories(self, user_id: str):
        """Create default categories for new user"""
        default_categories = [
            {
                "name": "Development",
                "description": "Software development tasks",
                "color": "#007bff",
            },
            {
                "name": "Meeting",
                "description": "Meetings and calls",
                "color": "#28a745",
            },
            {
                "name": "Planning",
                "description": "Project planning and analysis",
                "color": "#ffc107",
            },
            {
                "name": "Testing",
                "description": "Quality assurance and testing",
                "color": "#dc3545",
            },
            {
                "name": "Documentation",
                "description": "Writing documentation",
                "color": "#6f42c1",
            },
        ]

        try:
            for cat_data in default_categories:
                category = Category(
                    user_id=user_id,
                    name=cat_data["name"],
                    description=cat_data["description"],
                    color=cat_data["color"],
                )
                self.db.add(category)

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # Don't fail user creation if category creation fails
            print(
                f"Warning: Failed to create default categories for user {user_id}: {e}"
            )

    def _set_default_currency(self, user_id: str):
        """Set default currency for new user"""
        from database.repositories import ConfigRepository, CurrencyRepository

        try:
            config_repo = ConfigRepository(self.db)
            currency_repo = CurrencyRepository(self.db)

            # Get USD from database instead of hardcoding
            default_currency = currency_repo.get_currency_by_code("USD")
            if not default_currency:
                # Fallback to first available currency if USD not found
                all_currencies = currency_repo.get_all_currencies()
                default_currency = all_currencies[0] if all_currencies else None

            if default_currency:
                config_repo.save_config("currency", default_currency, user_id)
        except Exception as e:
            # Don't fail user creation if currency setting fails
            print(f"Warning: Failed to set default currency for user {user_id}: {e}")

    def _log_action(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        details: str = None,
        ip_address: str = None,
    ):
        """Log action for audit trail"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(log)
        # Don't commit here - let the caller handle it

    def complete_user_onboarding(self, user_id: str, default_category: str) -> bool:
        """Complete user onboarding by setting default category and onboarding status"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.onboarding_completed = True
            user.default_category = default_category
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False


class EncryptionService:
    """Handle data encryption at rest"""

    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY", "").encode()
        if not self.key:
            # Generate a key for development (in production, use proper key management)
            self.key = os.urandom(32)

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like configuration"""
        # In production, use Fernet or similar
        try:
            from cryptography.fernet import Fernet

            f = Fernet(Fernet.generate_key())  # In production, use fixed key
            return f.encrypt(data.encode()).decode()
        except ImportError:
            # Fallback if cryptography is not available
            return data

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        # Implementation would use the same key as encrypt
        return encrypted_data  # Placeholder
