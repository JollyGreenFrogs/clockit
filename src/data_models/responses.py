"""
API Response Models - All Pydantic models for outgoing API responses
Includes proper data structure for client consumption
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

# =============================================================================
# TASK RESPONSES
# =============================================================================


class TaskResponse(BaseModel):
    """Schema for individual task response"""

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


class TasksDetailedResponse(BaseModel):
    """Schema for detailed tasks response"""

    tasks: Dict[str, TaskResponse]


# =============================================================================
# CATEGORY RESPONSES
# =============================================================================


class CategoryResponse(BaseModel):
    """Schema for category response"""

    id: int
    name: str
    description: Optional[str]
    color: Optional[str]

    class Config:
        from_attributes = True


class CategoriesListResponse(BaseModel):
    """Schema for categories list response"""

    categories: List[CategoryResponse]


# =============================================================================
# TIME ENTRY RESPONSES
# =============================================================================


class TimeEntryResponse(BaseModel):
    """Schema for time entry response"""

    id: int
    task_id: int
    task_name: str
    duration: float
    description: Optional[str]
    entry_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class TimeEntriesListResponse(BaseModel):
    """Schema for time entries list response"""

    time_entries: List[TimeEntryResponse]


# =============================================================================
# CONFIGURATION RESPONSES
# =============================================================================


class ConfigResponse(BaseModel):
    """Schema for configuration response"""

    config_type: str
    config_data: Dict
    updated_at: datetime


class CurrencyResponse(BaseModel):
    """Schema for currency response"""

    code: str
    symbol: str
    name: str


class CurrenciesListResponse(BaseModel):
    """Schema for currencies list response"""

    currencies: List[CurrencyResponse]


class RateResponse(BaseModel):
    """Schema for rate response"""

    task_type: str
    day_rate: float
    hourly_rate: float
    currency: Optional[str]


class RatesListResponse(BaseModel):
    """Schema for rates list response"""

    rates: Dict[str, float]  # task_type -> day_rate mapping


# =============================================================================
# ONBOARDING RESPONSES
# =============================================================================


class OnboardingStatus(BaseModel):
    """Schema for onboarding status response"""

    onboarding_completed: bool
    default_category: Optional[str]
    needs_onboarding: bool


class OnboardingCompletionResponse(BaseModel):
    """Schema for onboarding completion response"""

    message: str
    default_category: str
    categories_created: int


# =============================================================================
# INVOICE RESPONSES
# =============================================================================


class InvoiceItemResponse(BaseModel):
    """Schema for individual invoice item"""

    task: str
    total_hours: float
    day_rate: str
    hour_rate: str
    amount: str
    task_details: List[Dict]


class InvoicePreviewResponse(BaseModel):
    """Schema for invoice preview response"""

    preview: str
    status: str


class InvoiceGenerationResponse(BaseModel):
    """Schema for invoice generation response"""

    date: str
    currency: Dict[str, str]
    items: List[InvoiceItemResponse]
    total: str
    task_ids: List[str]


# =============================================================================
# SYSTEM RESPONSES
# =============================================================================


class HealthCheckResponse(BaseModel):
    """Schema for health check response"""

    status: str
    timestamp: str
    version: str
    data_directory_accessible: bool
    database_healthy: bool
    tasks_loadable: bool
    storage_type: str


class SystemDataLocationResponse(BaseModel):
    """Schema for system data location response"""

    database_type: str
    data_storage: str
    data_directory: str
    status: str


class VersionResponse(BaseModel):
    """Schema for version response"""

    version: str
    build: Optional[str]
    environment: Optional[str]


# =============================================================================
# GENERIC API RESPONSES
# =============================================================================


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


class MessageResponse(BaseModel):
    """Schema for simple message responses"""

    message: str


class StatusResponse(BaseModel):
    """Schema for status responses"""

    status: str
    message: Optional[str] = None


# =============================================================================
# AUTHENTICATION RESPONSES (if needed)
# =============================================================================


class TokenResponse(BaseModel):
    """Schema for authentication token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Schema for user information response"""

    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    subscription_tier: str
    onboarding_completed: bool
