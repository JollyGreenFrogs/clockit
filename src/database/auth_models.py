"""
User authentication and authorization models
"""

import uuid
from datetime import datetime

import bcrypt
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from .connection import Base
from .types import UUID


class User(Base):
    """User model with authentication support"""

    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Subscription/billing related
    subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
    subscription_expires = Column(DateTime, nullable=True)

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)
    default_category = Column(String(100), nullable=True)  # User's default category for tasks

    # Security & tracking
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str):
        """Hash and set password"""
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
            "utf-8"
        )

    def check_password(self, password: str) -> bool:
        """Check if provided password matches hash"""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )

    def is_account_locked(self) -> bool:
        """Check if account is locked due to failed attempts"""
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False


class UserSession(Base):
    """Track user sessions for security"""

    __tablename__ = "user_sessions"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), index=True, nullable=False)
    session_token = Column(String(255), unique=True, index=True)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for security and compliance"""

    __tablename__ = "audit_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), index=True, nullable=True)
    action = Column(String(100), nullable=False)  # login, logout, create_task, etc.
    resource_type = Column(String(50))  # task, config, user
    resource_id = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    details = Column(Text)  # JSON details about the action
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
