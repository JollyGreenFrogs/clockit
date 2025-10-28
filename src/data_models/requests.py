"""
API Request Models - All Pydantic models for incoming API requests
Includes comprehensive validation and sanitization for cybersecurity
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from utils.validation import sanitize_description, sanitize_string, validate_task_name

# =============================================================================
# TIME ENTRY REQUESTS
# =============================================================================


class TimeEntry(BaseModel):
    """Schema for adding time entry to existing task (task_id comes from URL path)"""

    hours: float = Field(..., ge=0.000001, le=24, description="Hours worked (minimum 1 second = 0.000278 hours)")
    date: Union[datetime, str] = Field(
        ..., description="Date and time of work performed"
    )
    description: Optional[str] = Field(
        "", max_length=1000, description="Work description"
    )

    @validator("description")
    def sanitize_description(cls, v):
        """Sanitize description to prevent XSS and injection attacks"""
        if v:
            return sanitize_description(v, max_length=1000)
        return v

    @validator("date")
    def validate_date(cls, v):
        """Validate and convert date to datetime object"""
        if isinstance(v, str):
            try:
                # Try parsing as date string (YYYY-MM-DD)
                if len(v) == 10 and v.count("-") == 2:
                    return datetime.strptime(v, "%Y-%m-%d")
                # Try parsing as ISO datetime
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {v}. Expected YYYY-MM-DD or ISO format"
                )
        return v

    @validator("hours")
    def validate_hours(cls, v):
        """Validate hours are reasonable"""
        if v < 0.000001:  # Allow very small values but not zero or negative
            raise ValueError("Hours must be at least 0.000001 (about 0.0036 seconds)")
        if v > 24:
            raise ValueError("Cannot log more than 24 hours in a single entry")
        return round(v, 6)  # Round to 6 decimal places for 1-second precision


class TimeEntryUpdate(BaseModel):
    """Schema for updating existing time entry"""

    duration: Optional[float] = Field(None, ge=0.000001, le=24, description="Duration in hours (minimum 1 second = 0.000278 hours)")
    description: Optional[str] = Field(None, max_length=1000)

    @validator("description")
    def sanitize_description(cls, v):
        """Sanitize description to prevent XSS and injection attacks"""
        if v is not None:
            return sanitize_description(v, max_length=1000)
        return v

    @validator("duration")
    def validate_duration(cls, v):
        """Validate duration if provided"""
        if v is not None:
            if v < 0.000001:  # Allow very small values but not zero or negative
                raise ValueError("Duration must be at least 0.000001 (about 0.0036 seconds)")
            if v > 24:
                raise ValueError("Cannot log more than 24 hours in a single entry")
            return round(v, 6)  # Round to 6 decimal places for 1-second precision
        return v


class TimeEntryCreate(BaseModel):
    """Schema for creating new time entry with task name"""

    task_name: str = Field(..., min_length=1, max_length=255)
    duration: float = Field(..., ge=0.000001, le=24, description="Duration in hours (minimum 1 second = 0.000278 hours)")
    description: Optional[str] = Field(None, max_length=1000)
    entry_date: Optional[datetime] = None

    @validator("task_name")
    def sanitize_task_name(cls, v):
        """Sanitize and validate task name"""
        return sanitize_string(v, max_length=255)

    @validator("description")
    def sanitize_description(cls, v):
        """Sanitize description"""
        if v:
            return sanitize_description(v, max_length=1000)
        return v


# =============================================================================
# TASK REQUESTS
# =============================================================================


class TaskCreate(BaseModel):
    """Schema for creating a new task"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field("", max_length=1000)
    category: str = Field(
        ...,
        max_length=100,
        description="Task category (can be empty, defaults to 'Other')",
    )
    time_spent: Optional[float] = Field(0.0, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)

    @validator("name")
    def validate_and_sanitize_task_name(cls, v):
        """Comprehensive task name validation and sanitization"""
        # Basic validation
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")

        # Auto-trim whitespace
        v = v.strip()

        # Check for excessive spaces after trimming
        if "  " in v:
            raise ValueError("Task name cannot contain consecutive spaces")

        # Length validation
        if len(v) > 255:
            raise ValueError("Task name cannot exceed 255 characters")

        # Use centralized validation
        is_valid, error_msg = validate_task_name(v)
        if not is_valid:
            raise ValueError(error_msg)

        # Sanitize for security
        return sanitize_string(v, 255)

    @validator("description")
    def sanitize_task_description(cls, v):
        """Sanitize description for security"""
        if v:
            return sanitize_description(v, max_length=1000)
        return v

    @validator("category")
    def sanitize_category(cls, v):
        """Sanitize category name - allow empty (defaults to 'Other')"""
        if not v or not v.strip():
            return "Other"  # Default to 'Other' for empty categories
        return sanitize_string(v, max_length=100)

    @validator("hourly_rate")
    def validate_hourly_rate(cls, v):
        """Validate hourly rate"""
        if v is not None and v < 0:
            raise ValueError("Hourly rate cannot be negative")
        return v


class TaskUpdate(BaseModel):
    """Schema for updating an existing task"""

    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    time_spent: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)

    @validator("description")
    def sanitize_task_description(cls, v):
        """Sanitize description"""
        if v:
            return sanitize_description(v, max_length=1000)
        return v

    @validator("category")
    def sanitize_category(cls, v):
        """Sanitize category"""
        if v:
            return sanitize_string(v, max_length=100)
        return v


class TaskCategoryUpdate(BaseModel):
    """Schema for updating task category"""

    category: str = Field(..., max_length=100)

    @validator("category")
    def sanitize_category(cls, v):
        """Sanitize category name - allow empty (defaults to 'Other')"""
        if not v or not v.strip():
            return "Other"  # Default to 'Other' for empty categories
        return sanitize_string(v, max_length=100)


# =============================================================================
# CATEGORY REQUESTS
# =============================================================================


class CategoryCreate(BaseModel):
    """Schema for creating a category"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, min_length=4, max_length=7)

    @validator("name")
    def sanitize_name(cls, v):
        """Sanitize category name"""
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        return sanitize_string(v, max_length=100)

    @validator("description")
    def sanitize_cat_description(cls, v):
        """Sanitize category description"""
        if v:
            return sanitize_description(v, max_length=500)
        return v

    @validator("color")
    def validate_color(cls, v):
        """Validate hex color format"""
        if v and not v.startswith("#"):
            raise ValueError("Color must be a hex color starting with #")
        return v


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, min_length=4, max_length=7)
    day_rate: Optional[float] = Field(None, ge=0)

    @validator("name")
    def sanitize_name(cls, v):
        """Sanitize category name"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Category name cannot be empty")
            return sanitize_string(v, max_length=100)
        return v

    @validator("description")
    def sanitize_cat_description(cls, v):
        """Sanitize category description"""
        if v:
            return sanitize_description(v, max_length=500)
        return v

    @validator("color")
    def validate_color(cls, v):
        """Validate hex color format"""
        if v and not v.startswith("#"):
            raise ValueError("Color must be a hex color starting with #")
        return v

    @validator("day_rate")
    def validate_day_rate(cls, v):
        """Validate day rate"""
        if v is not None and v < 0:
            raise ValueError("Day rate cannot be negative")
        return v


# =============================================================================
# ONBOARDING REQUESTS
# =============================================================================


class OnboardingData(BaseModel):
    """Schema for onboarding completion data"""

    default_category: str = Field(..., min_length=1, max_length=100)
    categories: List[str] = Field(..., description="List of categories to create")
    rates: Dict[str, float] = Field(..., description="Rates for each category")
    currency_code: str = Field(
        ..., min_length=3, max_length=3, description="Currency code (e.g., USD, EUR)"
    )
    currency_symbol: str = Field(
        ..., min_length=1, max_length=5, description="Currency symbol (e.g., $, €)"
    )
    currency_name: str = Field(
        ..., min_length=1, max_length=50, description="Currency name (e.g., US Dollar)"
    )

    @validator("default_category")
    def sanitize_default_category(cls, v):
        """Sanitize default category"""
        if not v or not v.strip():
            raise ValueError("Default category cannot be empty")
        return sanitize_string(v, max_length=100)

    @validator("categories")
    def sanitize_categories(cls, v):
        """Sanitize all categories in the list"""
        # Categories can be empty - default category is handled separately
        if not v:
            return []

        sanitized = []
        for category in v:
            if category and category.strip():
                sanitized.append(sanitize_string(category.strip(), max_length=100))

        return sanitized

    @validator("rates")
    def validate_rates(cls, v, values):
        """Validate that rates are provided for all categories"""
        if "categories" in values and "default_category" in values:
            all_categories = set(values["categories"])
            all_categories.add(values["default_category"])

            # Check that all categories have rates
            missing_rates = all_categories - set(v.keys())
            if missing_rates:
                raise ValueError(
                    f"Rates must be provided for all categories: {missing_rates}"
                )

            # Check that all rates are positive
            for category, rate in v.items():
                if rate <= 0:
                    raise ValueError(f"Rate for {category} must be positive")

        return v

    @validator("currency_code")
    def validate_currency_code(cls, v):
        """Validate currency code format"""
        if not v or len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters")
        return v.upper()

    @validator("currency_symbol")
    def validate_currency_symbol(cls, v):
        """Validate currency symbol"""
        if not v or not v.strip():
            raise ValueError("Currency symbol cannot be empty")
        return v.strip()

    @validator("currency_name")
    def validate_currency_name(cls, v):
        """Validate currency name"""
        if not v or not v.strip():
            raise ValueError("Currency name cannot be empty")
        return sanitize_string(v.strip(), max_length=50)


# =============================================================================
# CONFIGURATION REQUESTS
# =============================================================================


class RateConfig(BaseModel):
    """Schema for rate configuration"""

    task_type: str = Field(..., min_length=1, max_length=100)
    day_rate: float = Field(..., gt=0, description="Daily rate must be positive")

    @validator("task_type")
    def sanitize_task_type(cls, v):
        """Sanitize task type"""
        if not v or not v.strip():
            raise ValueError("Task type cannot be empty")
        return sanitize_string(v, max_length=100)

    @validator("day_rate")
    def validate_day_rate(cls, v):
        """Validate day rate"""
        if v <= 0:
            raise ValueError("Day rate must be greater than 0")
        if v > 100000:  # Reasonable upper limit
            raise ValueError("Day rate seems unreasonably high")
        return round(v, 2)


class AdvancedRateConfig(BaseModel):
    """Schema for advanced rate configuration from schemas.py"""

    default_rate: float = Field(..., gt=0)
    overtime_rate: Optional[float] = Field(None, gt=0)
    weekend_rate: Optional[float] = Field(None, gt=0)

    @validator("default_rate", "overtime_rate", "weekend_rate")
    def validate_rates(cls, v):
        """Validate all rate fields"""
        if v is not None:
            if v <= 0:
                raise ValueError("Rate must be greater than 0")
            if v > 100000:
                raise ValueError("Rate seems unreasonably high")
            return round(v, 2)
        return v


class CurrencyConfig(BaseModel):
    """Schema for currency configuration"""

    currency: str = Field(
        ..., min_length=3, max_length=3, description="3-letter currency code"
    )

    @validator("currency")
    def validate_currency_code(cls, v):
        """Validate and sanitize currency code"""
        if not v or len(v) != 3 or not v.isalpha():
            raise ValueError("Currency code must be a 3-letter alphabetic code")

        # Sanitize by converting to uppercase and ensuring no special characters
        sanitized = v.strip().upper()
        if not sanitized.isalpha():
            raise ValueError("Currency code must contain only letters")

        # TODO: Could add validation against known currency codes from database
        return sanitized


class AdvancedCurrencyConfig(BaseModel):
    """Schema for advanced currency configuration from schemas.py"""

    code: str = Field(..., min_length=3, max_length=3)
    symbol: str = Field(..., min_length=1, max_length=5)
    name: str = Field(..., min_length=1, max_length=100)

    @validator("code")
    def sanitize_code(cls, v):
        """Sanitize currency code"""
        return sanitize_string(v.upper(), max_length=3)

    @validator("symbol")
    def sanitize_symbol(cls, v):
        """Sanitize currency symbol"""
        return sanitize_string(v, max_length=5)

    @validator("name")
    def sanitize_name(cls, v):
        """Sanitize currency name"""
        return sanitize_string(v, max_length=100)


# =============================================================================
# PASSWORD MANAGEMENT REQUESTS
# =============================================================================


class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator("current_password")
    def validate_current_password(cls, v):
        """Validate current password is provided"""
        if not v or not v.strip():
            raise ValueError("Current password is required")
        return v

    @validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if not v or len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError("New password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError("New password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError("New password must contain at least one number")
        
        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError("New password must contain at least one special character")
        
        return v
