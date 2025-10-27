"""
API Request Models - All Pydantic models for incoming API requests
Includes comprehensive validation and sanitization for cybersecurity
"""

from datetime import datetime
from typing import Optional, List, Union, Dict
from pydantic import BaseModel, validator, Field

from utils.validation import sanitize_string, sanitize_description, validate_task_name


# =============================================================================
# TIME ENTRY REQUESTS
# =============================================================================

class TimeEntry(BaseModel):
    """Schema for adding time entry to existing task (task_id comes from URL path)"""

    hours: float = Field(..., gt=0, le=24, description="Hours worked (0-24 per entry)")
    date: Union[datetime, str] = Field(..., description="Date and time of work performed")
    description: Optional[str] = Field("", max_length=1000, description="Work description")

    @validator('description')
    def sanitize_description(cls, v):
        """Sanitize description to prevent XSS and injection attacks"""
        if v:
            return sanitize_description(v, max_length=1000)
        return v

    @validator('date')
    def validate_date(cls, v):
        """Validate and convert date to datetime object"""
        if isinstance(v, str):
            try:
                # Try parsing as date string (YYYY-MM-DD)
                if len(v) == 10 and v.count('-') == 2:
                    return datetime.strptime(v, '%Y-%m-%d')
                # Try parsing as ISO datetime
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD or ISO format")
        return v

    @validator('hours')
    def validate_hours(cls, v):
        """Validate hours are reasonable"""
        if v <= 0:
            raise ValueError("Hours must be greater than 0")
        if v > 24:
            raise ValueError("Cannot log more than 24 hours in a single entry")
        return round(v, 2)  # Round to 2 decimal places


class TimeEntryUpdate(BaseModel):
    """Schema for updating existing time entry"""

    duration: Optional[float] = Field(None, gt=0, le=24)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('description')
    def sanitize_description(cls, v):
        """Sanitize description to prevent XSS and injection attacks"""
        if v is not None:
            return sanitize_description(v, max_length=1000)
        return v

    @validator('duration')
    def validate_duration(cls, v):
        """Validate duration if provided"""
        if v is not None:
            if v <= 0:
                raise ValueError("Duration must be greater than 0")
            if v > 24:
                raise ValueError("Cannot log more than 24 hours in a single entry")
            return round(v, 2)
        return v


class TimeEntryCreate(BaseModel):
    """Schema for creating new time entry with task name"""

    task_name: str = Field(..., min_length=1, max_length=255)
    duration: float = Field(..., gt=0, le=24)
    description: Optional[str] = Field(None, max_length=1000)
    entry_date: Optional[datetime] = None

    @validator('task_name')
    def sanitize_task_name(cls, v):
        """Sanitize and validate task name"""
        return sanitize_string(v, max_length=255)

    @validator('description')
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
    category: str = Field(..., max_length=100, description="Task category (can be empty, defaults to 'Other')")
    time_spent: Optional[float] = Field(0.0, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)

    @validator('name')
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

    @validator('description')
    def sanitize_task_description(cls, v):
        """Sanitize description for security"""
        if v:
            return sanitize_description(v, max_length=1000)
        return v

    @validator('category')
    def sanitize_category(cls, v):
        """Sanitize category name - allow empty (defaults to 'Other')"""
        if not v or not v.strip():
            return "Other"  # Default to 'Other' for empty categories
        return sanitize_string(v, max_length=100)

    @validator('hourly_rate')
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

    @validator('description')
    def sanitize_task_description(cls, v):
        """Sanitize description"""
        if v:
            return sanitize_description(v, max_length=1000)
        return v

    @validator('category')
    def sanitize_category(cls, v):
        """Sanitize category"""
        if v:
            return sanitize_string(v, max_length=100)
        return v


class TaskCategoryUpdate(BaseModel):
    """Schema for updating task category"""
    
    category: str = Field(..., max_length=100)

    @validator('category')
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

    @validator('name')
    def sanitize_name(cls, v):
        """Sanitize category name"""
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        return sanitize_string(v, max_length=100)

    @validator('description')
    def sanitize_cat_description(cls, v):
        """Sanitize category description"""
        if v:
            return sanitize_description(v, max_length=500)
        return v

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color format"""
        if v and not v.startswith('#'):
            raise ValueError("Color must be a hex color starting with #")
        return v


# =============================================================================
# ONBOARDING REQUESTS
# =============================================================================

class OnboardingData(BaseModel):
    """Schema for onboarding completion data"""
    
    default_category: str = Field(..., min_length=1, max_length=100)
    categories: List[str] = Field(..., description="List of categories to create")
    rates: Dict[str, float] = Field(..., description="Rates for each category")
    currency_code: str = Field(..., min_length=3, max_length=3, description="Currency code (e.g., USD, EUR)")
    currency_symbol: str = Field(..., min_length=1, max_length=5, description="Currency symbol (e.g., $, €)")
    currency_name: str = Field(..., min_length=1, max_length=50, description="Currency name (e.g., US Dollar)")

    @validator('default_category')
    def sanitize_default_category(cls, v):
        """Sanitize default category"""
        if not v or not v.strip():
            raise ValueError("Default category cannot be empty")
        return sanitize_string(v, max_length=100)

    @validator('categories')
    def sanitize_categories(cls, v):
        """Sanitize all categories in the list"""
        if not v:
            raise ValueError("At least one category must be provided")
        
        sanitized = []
        for category in v:
            if category and category.strip():
                sanitized.append(sanitize_string(category.strip(), max_length=100))
        
        if not sanitized:
            raise ValueError("At least one valid category must be provided")
        
        return sanitized

    @validator('rates')
    def validate_rates(cls, v, values):
        """Validate that rates are provided for all categories"""
        if 'categories' in values and 'default_category' in values:
            all_categories = set(values['categories'])
            all_categories.add(values['default_category'])
            
            # Check that all categories have rates
            missing_rates = all_categories - set(v.keys())
            if missing_rates:
                raise ValueError(f"Rates must be provided for all categories: {missing_rates}")
            
            # Check that all rates are positive
            for category, rate in v.items():
                if rate <= 0:
                    raise ValueError(f"Rate for {category} must be positive")
        
        return v

    @validator('currency_code')
    def validate_currency_code(cls, v):
        """Validate currency code format"""
        if not v or len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters")
        return v.upper()

    @validator('currency_symbol')
    def validate_currency_symbol(cls, v):
        """Validate currency symbol"""
        if not v or not v.strip():
            raise ValueError("Currency symbol cannot be empty")
        return v.strip()

    @validator('currency_name')
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

    @validator('task_type')
    def sanitize_task_type(cls, v):
        """Sanitize task type"""
        if not v or not v.strip():
            raise ValueError("Task type cannot be empty")
        return sanitize_string(v, max_length=100)

    @validator('day_rate')
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

    @validator('default_rate', 'overtime_rate', 'weekend_rate')
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
    
    currency: str = Field(..., min_length=3, max_length=3, description="3-letter currency code")

    @validator('currency')
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

    @validator('code')
    def sanitize_code(cls, v):
        """Sanitize currency code"""
        return sanitize_string(v.upper(), max_length=3)

    @validator('symbol')
    def sanitize_symbol(cls, v):
        """Sanitize currency symbol"""
        return sanitize_string(v, max_length=5)

    @validator('name')
    def sanitize_name(cls, v):
        """Sanitize currency name"""
        return sanitize_string(v, max_length=100)
