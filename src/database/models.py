"""
Database models for clockit application
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .auth_models import User  # Import User model
from .connection import Base
from .types import JSON, UUID


class UserConfig(Base):
    """User configuration settings"""

    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=False)
    config_type = Column(String, index=True)  # 'currency', 'rates', etc.
    config_data = Column(JSON)  # Store config as JSON (encrypted at rest)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """Task model with enhanced features"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    time_spent = Column(Float, default=0.0)  # Time in milliseconds
    hourly_rate = Column(Float, nullable=True)  # Override default rate
    is_active = Column(Boolean, default=True)

    # Multi-tenancy: Tasks are unique per user
    # Removed unique=True from name to allow same task names across users

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TimeEntry(Base):
    """Individual time entries for detailed tracking"""

    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Link to task
    task_name = Column(String, index=True)  # Denormalized for reporting
    duration = Column(Float)  # Duration in milliseconds
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    entry_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    """Task categories"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, index=True)  # Unique per user, not globally
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # For UI theming
    created_at = Column(DateTime, default=datetime.utcnow)


class Currency(Base):
    """Available currencies in the system"""

    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(3), unique=True, index=True, nullable=False
    )  # ISO 4217 currency code
    symbol = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
