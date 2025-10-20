"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


# Task-related schemas
class TaskCreate(BaseModel):
    """Schema for creating a new task"""

    task_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    time_spent: Optional[float] = Field(0.0, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)


class TaskUpdate(BaseModel):
    """Schema for updating an existing task"""

    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    time_spent: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)


class TaskResponse(BaseModel):
    """Schema for task response"""

    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    time_spent: float
    hourly_rate: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy models


class TaskListResponse(BaseModel):
    """Schema for tasks list response"""

    tasks: Dict[str, float]  # task_name -> time_spent mapping


# Category schemas
class CategoryCreate(BaseModel):
    """Schema for creating a category"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=7)  # Hex color


class CategoryResponse(BaseModel):
    """Schema for category response"""

    id: int
    name: str
    description: Optional[str]
    color: Optional[str]

    class Config:
        from_attributes = True


# Time entry schemas
class TimeEntryCreate(BaseModel):
    """Schema for creating a time entry"""

    task_name: str = Field(..., min_length=1)
    duration: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    entry_date: Optional[datetime] = None


# Configuration schemas
class CurrencyConfig(BaseModel):
    """Schema for currency configuration"""

    code: str = Field(..., min_length=3, max_length=3)
    symbol: str = Field(..., min_length=1, max_length=5)
    name: str = Field(..., min_length=1, max_length=100)


class RateConfig(BaseModel):
    """Schema for rate configuration"""

    default_rate: float = Field(..., gt=0)
    overtime_rate: Optional[float] = Field(None, gt=0)
    weekend_rate: Optional[float] = Field(None, gt=0)


class ConfigResponse(BaseModel):
    """Schema for configuration response"""

    config_type: str
    config_data: Dict
    updated_at: datetime


# Onboarding schemas
class OnboardingData(BaseModel):
    """Schema for onboarding completion data"""
    
    default_category: str = Field(..., min_length=1, max_length=100)
    categories: list[str] = Field(..., description="List of categories to create")


class OnboardingStatus(BaseModel):
    """Schema for onboarding status response"""
    
    onboarding_completed: bool
    default_category: Optional[str] = None
    needs_onboarding: bool


# API response schemas
class SuccessResponse(BaseModel):
    """Schema for success responses"""

    success: bool = True
    message: str
    data: Optional[Dict] = None


class ErrorResponse(BaseModel):
    """Schema for error responses"""

    success: bool = False
    error: str
    details: Optional[str] = None
