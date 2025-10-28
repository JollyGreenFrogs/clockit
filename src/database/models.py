"""
Database models for clockit application
"""

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
    DECIMAL,
)

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
    """Task model with proper category relationship"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    name = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    time_spent = Column(DECIMAL(10, 6), default=0.0)  # Time in hours with 6 decimal precision (1-second accuracy)
    
    # Rate override - if null, inherit from category
    hourly_rate_override = Column(Float, nullable=True)  # Override category rate
    
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)  # Task completion status

    # Multi-tenancy: Tasks are unique per user
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TimeEntry(Base):
    """Individual time entries for detailed tracking"""

    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Link to task
    task_name = Column(String, index=True)  # Denormalized for reporting
    duration = Column(DECIMAL(10, 6))  # Duration in hours with 6 decimal precision (1-second accuracy)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    entry_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    """Task categories with rate and configuration information"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(100), index=True, nullable=False)  # Unique per user
    description = Column(Text, nullable=True)
    color = Column(String(10), nullable=True, default="#007bff")  # Hex color for UI
    
    # Rate information - core business logic
    day_rate = Column(Float, nullable=False, default=0.0)  # Rate per day
    hourly_rate = Column(Float, nullable=True)  # Calculated from day_rate (day_rate/8)
    
    # Future extensibility
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    is_active = Column(Boolean, default=True)  # For soft deletion
    is_default = Column(Boolean, default=False)  # User's default category
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
