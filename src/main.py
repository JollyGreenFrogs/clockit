import os
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

# Handle imports that work from both project root and src directory
try:
    from .auth.dependencies import get_current_user
    from .auth.routes import router as auth_router
    from .business.currency_manager import CurrencyManager
    from .business.invoice_manager import InvoiceManager
    from .business.task_manager import TaskManager
    from .config import Config
    from .database.auth_models import User
    from .database.connection import get_db
    from .database.init import check_database_connection, init_database
    from .database.repositories import ConfigRepository, CurrencyRepository
    from .logging_config import configure_logging
    from .version import get_full_version_info, get_version_string
except ImportError:
    # Fallback for when running from src directory
    from version import get_version_string, get_full_version_info
    from logging_config import configure_logging
    from config import Config
    from database.init import init_database, check_database_connection
    from database.connection import get_db
    from database.repositories import ConfigRepository, CurrencyRepository
    from business.task_manager import TaskManager
    from business.currency_manager import CurrencyManager
    from business.invoice_manager import InvoiceManager
    from auth.routes import router as auth_router
    from auth.dependencies import get_current_user
    from database.auth_models import User


import logging

# Validate and configure application
if not Config.validate():
    print("Configuration validation failed. Check logs for details.")
    exit(1)

# Configure logging early
configure_logging()
logger = logging.getLogger(__name__)

# Initialize database
logger.info("Initializing database...")
if not check_database_connection():
    logger.error(
        "Database connection failed. Please check your database configuration."
    )
    exit(1)

if not init_database():
    logger.error("Database initialization failed.")
    exit(1)

logger.info("Database initialized successfully")

# Use configuration for data directory (legacy support for file exports only)
DATA_DIR = Config.DATA_DIR

# Initialize business managers (database-only)
task_manager = TaskManager()
currency_manager = CurrencyManager()
invoice_manager = InvoiceManager(
    DATA_DIR, task_manager
)  # Keep for invoice file exports


def initialize_application() -> None:
    """Initialize the application by creating necessary directories.

    All configuration is now stored in the database.
    """
    logger.info("Initializing ClockIt; data directory=%s", DATA_DIR)

    # Ensure data directory exists for file uploads/exports
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception(
            "Could not create data directory %s; falling back to cwd", DATA_DIR
        )

    logger.info("Application initialization complete")


# Pydantic models for API requests
class TimeEntry(BaseModel):
    task_id: str
    hours: float
    date: str
    description: Optional[str] = ""


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str  # Made mandatory - no default value

    @validator("name")
    def validate_task_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")

        # Check for excessive spaces
        if "  " in v:  # Multiple consecutive spaces
            raise ValueError("Task name cannot contain multiple consecutive spaces.")

        if v != v.strip():
            raise ValueError("Task name cannot start or end with spaces.")

        # Ensure reasonable length
        if len(v) > 100:
            raise ValueError("Task name must be 100 characters or less.")

        return v.strip()


class OnboardingData(BaseModel):
    """Schema for onboarding completion data"""
    default_category: str
    categories: list[str]


class OnboardingStatus(BaseModel):
    """Schema for onboarding status response"""
    onboarding_completed: bool
    default_category: Optional[str] = None
    needs_onboarding: bool


class RateConfig(BaseModel):
    task_type: str
    day_rate: float


class CurrencyConfig(BaseModel):
    currency: str  # Just the currency code


# Load invoice columns config
def load_invoice_columns():
    return invoice_manager.load_invoice_columns()


# Save invoice columns config
def save_invoice_columns(columns):
    return invoice_manager.save_invoice_columns(columns)


app = FastAPI(
    title="ClockIt - Time Tracker", version=get_full_version_info()["version"]
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize application on startup
initialize_application()

# Include the authentication router
app.include_router(auth_router, tags=["authentication"])

# Onboarding endpoints will be added below


# Version endpoint
@app.get("/version")
async def get_version():
    """Get application version information"""
    return get_full_version_info()


@app.get("/")
async def read_root():
    """
    API Server status endpoint
    """
    return JSONResponse(
        {
            "message": "ClockIt API Server",
            "status": "running",
            "version": get_version_string(),
            "endpoints": {
                "tasks": "/tasks",
                "rates": "/rates",
                "currency": "/currency",
                "invoice": "/invoice",
                "health": "/health",
                "docs": "/docs",
            },
        }
    )


# Task Management Endpoints
@app.get("/tasks")
async def get_tasks(current_user: User = Depends(get_current_user)):
    """Get all tasks for authenticated user"""
    tasks_data = task_manager.load_tasks_for_user(str(current_user.id))
    return tasks_data


@app.post("/tasks")
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user)):
    """Create a new task for authenticated user"""
    try:
        # The TaskCreate model validation will automatically check for problematic characters
        # If validation fails, Pydantic will raise a validation error

        # Use task manager to create task with user context
        success = task_manager.create_task_for_user(
            name=task.name,
            user_id=str(current_user.id),
            description=task.description or "",
            category=task.category or "",  # Fixed: use category from TaskCreate
            task_type=getattr(task, "task_type", ""),
            priority=getattr(task, "priority", ""),
            hourly_rate=getattr(task, "hourly_rate", None),
        )

        if success:
            return {"message": "Task created successfully", "task_name": task.name}
        else:
            raise HTTPException(status_code=500, detail="Failed to create task")

    except ValueError as e:
        # Handle validation errors from Pydantic
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error creating task: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create task")


@app.post("/tasks/{task_id}/time")
async def add_time_entry(
    task_id: int, time_entry: TimeEntry, current_user: User = Depends(get_current_user)
):
    """Add time entry to existing task by ID for authenticated user"""
    try:
        logger.info(f"Adding time entry for task ID: {task_id}")

        success = task_manager.add_time_entry_by_id(
            task_id=task_id,
            duration=time_entry.hours,
            description=time_entry.description or "",
            date=time_entry.date,
            user_id=str(current_user.id),
        )

        if success:
            # Get task details for response
            task = task_manager.get_task_by_id(task_id, str(current_user.id))
            task_name = task["name"] if task else f"Task ID {task_id}"
            return {
                "message": "Time entry added successfully",
                "task_name": task_name,
                "task_id": task_id,
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Task ID {task_id} not found or failed to add time entry",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error adding time entry: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to add time entry: {str(e)}"
        )


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    """Delete a task by ID for authenticated user"""
    try:
        logger.info(f"Deleting task ID: {task_id}")

        # Get task details before deletion for response
        task = task_manager.get_task_by_id(task_id, str(current_user.id))
        if not task:
            raise HTTPException(status_code=404, detail=f"Task ID {task_id} not found")

        success = task_manager.delete_task(
            task_name=task["name"], user_id=str(current_user.id)
        )

        if success:
            return {
                "message": "Task deleted successfully",
                "task_name": task["name"],
                "task_id": task_id,
            }
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete task ID {task_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting task: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@app.get("/tasks/{task_id}/time-entries")
async def get_task_time_entries(task_id: int, current_user: User = Depends(get_current_user)):
    """Get all time entries for a specific task"""
    try:
        logger.info(f"Getting time entries for task ID: {task_id}")
        entries = task_manager.get_task_time_entries(task_id, str(current_user.id))
        return {"time_entries": entries}
    except Exception as e:
        logger.exception("Error getting time entries: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get time entries: {str(e)}")


@app.delete("/time-entries/{entry_id}")
async def delete_time_entry(entry_id: int, current_user: User = Depends(get_current_user)):
    """Delete a specific time entry"""
    try:
        logger.info(f"Deleting time entry ID: {entry_id}")
        success = task_manager.delete_time_entry(entry_id, str(current_user.id))
        if success:
            return {"message": "Time entry deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Time entry not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting time entry: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to delete time entry: {str(e)}")


class TimeEntryUpdate(BaseModel):
    duration: Optional[float] = None
    description: Optional[str] = None


@app.put("/time-entries/{entry_id}")
async def update_time_entry(
    entry_id: int,
    update_data: TimeEntryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a specific time entry"""
    try:
        logger.info(f"Updating time entry ID: {entry_id}")
        success = task_manager.update_time_entry(
            entry_id, str(current_user.id),
            update_data.duration, update_data.description
        )
        if success:
            return {"message": "Time entry updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Time entry not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating time entry: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to update time entry: {str(e)}")


class TaskCategoryUpdate(BaseModel):
    category: str


@app.put("/tasks/{task_id}/category")
async def update_task_category(
    task_id: int,
    category_data: TaskCategoryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the category of a specific task"""
    try:
        logger.info(f"Updating category for task ID: {task_id}")
        success = task_manager.update_task_category(task_id, str(current_user.id), category_data.category)
        if success:
            return {"message": "Task category updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating task category: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to update task category: {str(e)}")


# Rate Configuration Endpoints
@app.get("/rates")
async def get_rates(current_user: User = Depends(get_current_user)):
    """Get all rate configurations for authenticated user"""
    try:
        db = next(get_db())
        config_repo = ConfigRepository(db)
        rates_config = config_repo.get_config("rates", str(current_user.id))
        return rates_config or {}
    except Exception as e:
        logger.error(f"Failed to load rates: {e}")
        raise HTTPException(status_code=500, detail="Failed to load rates")


@app.post("/rates")
async def set_rate(
    rate_config: RateConfig, current_user: User = Depends(get_current_user)
):
    """Set day rate for a task type"""
    try:
        db = next(get_db())
        config_repo = ConfigRepository(db)

        # Get existing rates
        rates = config_repo.get_config("rates", str(current_user.id)) or {}
        rates[rate_config.task_type] = rate_config.day_rate

        # Save updated rates
        success = config_repo.save_config("rates", rates, str(current_user.id))
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save rate configuration"
            )

        hourly_rate = rate_config.day_rate / 8  # Assuming 8-hour workday

        # Get user's currency
        user_currency = config_repo.get_config("currency", str(current_user.id))

        return {
            "message": f"Rate set for {rate_config.task_type}",
            "day_rate": rate_config.day_rate,
            "hourly_rate": hourly_rate,
            "currency": user_currency,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set rate: {e}")
        raise HTTPException(status_code=500, detail="Failed to set rate")


@app.put("/rates/{task_type}")
async def update_rate(
    task_type: str,
    rate_config: RateConfig,
    current_user: User = Depends(get_current_user),
):
    """Update existing rate for a task type"""
    try:
        db = next(get_db())
        config_repo = ConfigRepository(db)

        rates = config_repo.get_config("rates", str(current_user.id)) or {}

        if task_type not in rates:
            raise HTTPException(status_code=404, detail="Task type not found")

        rates[task_type] = rate_config.day_rate
        success = config_repo.save_config("rates", rates, str(current_user.id))

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update rate")

        hourly_rate = rate_config.day_rate / 8
        user_currency = config_repo.get_config("currency", str(current_user.id))

        return {
            "message": f"Rate updated for {task_type}",
            "day_rate": rate_config.day_rate,
            "hourly_rate": hourly_rate,
            "currency": user_currency,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rate: {e}")
        raise HTTPException(status_code=500, detail="Failed to update rate")


@app.delete("/rates/{task_type}")
async def delete_rate(task_type: str, current_user: User = Depends(get_current_user)):
    """Delete a rate configuration"""
    try:
        db = next(get_db())
        config_repo = ConfigRepository(db)

        rates = config_repo.get_config("rates", str(current_user.id)) or {}

        if task_type not in rates:
            raise HTTPException(status_code=404, detail="Task type not found")

        del rates[task_type]
        success = config_repo.save_config("rates", rates, str(current_user.id))

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete rate")

        return {"message": f"Rate deleted for {task_type}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete rate")


# Currency Configuration Endpoints
@app.get("/currency")
async def get_currency(current_user: User = Depends(get_current_user)):
    """Get current currency configuration for the authenticated user"""
    db = next(get_db())
    config_repo = ConfigRepository(db)

    user_currency = config_repo.get_config("currency", str(current_user.id))
    if not user_currency:
        raise HTTPException(status_code=404, detail="User currency not configured")

    return {"currency": user_currency}


@app.get("/currencies")
async def get_currencies(current_user: User = Depends(get_current_user)):
    """Get list of all available currencies"""
    try:
        db = next(get_db())
        currency_repo = CurrencyRepository(db)
        currencies = currency_repo.get_all_currencies()
        logger.info(f"Retrieved {len(currencies)} currencies from database")
        return {"currencies": currencies}
    except Exception as e:
        logger.error(f"Failed to load currencies from database: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to load currencies from database"
        )


@app.get("/currency/available")
async def get_available_currencies(current_user: User = Depends(get_current_user)):
    """Get list of all available currencies"""
    db = next(get_db())
    currency_repo = CurrencyRepository(db)
    currencies = currency_repo.get_all_currencies()
    return {"currencies": currencies}


@app.post("/currency")
async def set_currency(
    currency_config: CurrencyConfig, current_user: User = Depends(get_current_user)
):
    """Set the application currency for the authenticated user"""
    db = next(get_db())
    currency_repo = CurrencyRepository(db)

    # Verify currency exists in database
    currency_data = currency_repo.get_currency_by_code(currency_config.currency)
    if not currency_data:
        raise HTTPException(status_code=400, detail="Unsupported currency code")

    # Save user's currency preference
    config_repo = ConfigRepository(db)
    success = config_repo.save_config("currency", currency_data, str(current_user.id))

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to save currency configuration"
        )

    return {
        "message": f"Currency set to {currency_data['name']}",
        "currency": currency_data,
    }


# Categories Endpoints
@app.get("/categories")
async def get_categories(current_user: User = Depends(get_current_user)):
    """Get list of all categories for the user"""
    try:
        categories = task_manager.get_task_categories(str(current_user.id))
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Failed to load categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to load categories")


# Invoice Generation Endpoints
@app.post("/invoice/generate")
async def generate_invoice(current_user: User = Depends(get_current_user)):
    """Generate invoice from non-exported tasks"""
    try:
        result = invoice_manager.generate_invoice(include_exported=False, user_id=str(current_user.id))

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # Export the invoice data
        if invoice_manager.export_invoice(result):
            # Create CSV content manually since create_csv_export doesn't exist
            csv_lines = []
            csv_lines.append("Description,Hours,Hour Rate,Amount")

            total_hours = 0
            for item in result.get("items", []):
                hours = item.get('total_hours', 0)
                total_hours += hours
                csv_lines.append(
                    f"\"{item.get('task', 'N/A')}\",{hours:.2f},{item.get('hour_rate', 'N/A')},{item.get('amount', 'N/A')}"
                )

            csv_lines.append(
                f"Total,,{total_hours:.2f},{result.get('total', 'N/A')}"
            )
            csv_content = "\n".join(csv_lines)

            # Return as downloadable file
            from fastapi.responses import Response

            filename = f"invoice-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to export invoice")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generating invoice: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Error generating invoice: {str(e)}"
        )


@app.get("/invoice/preview")
async def preview_invoice(current_user: User = Depends(get_current_user)):
    """Preview invoice without marking tasks as exported"""
    try:
        result = invoice_manager.generate_invoice(include_exported=False, user_id=str(current_user.id))

        if "error" in result:
            return {"preview": result["error"], "status": "no_data"}

        # Format the preview text
        preview_lines = []
        preview_lines.append("=== INVOICE PREVIEW ===")
        preview_lines.append("")

        if "items" in result:
            preview_lines.append("ITEMS:")
            total_hours = 0
            for item in result["items"]:
                hours = item.get('total_hours', 0)
                total_hours += hours
                preview_lines.append(
                    f"• {item.get('task', 'N/A')}: {hours:.2f}h @ {item.get('hour_rate', 'N/A')}/hr = {item.get('amount', 'N/A')}"
                )

            preview_lines.append("")
            currency = result.get('currency', {})
            currency_symbol = currency.get('symbol', '$') if isinstance(currency, dict) else '$'
            total_amount = result.get('total', '0.00')
            preview_lines.append(f"TOTAL: {currency_symbol}{total_amount}")
            preview_lines.append(f"Total Hours: {total_hours:.2f}")

        preview_text = "\n".join(preview_lines)

        return {"preview": preview_text, "status": "success"}
    except Exception as e:
        logger.exception("Error generating invoice preview: %s", e)
        return {"preview": f"Error generating preview: {str(e)}", "status": "error"}


# Onboarding Endpoints
@app.get("/onboarding/status")
async def get_onboarding_status(current_user: User = Depends(get_current_user)):
    """Get user's onboarding status"""
    try:
        return OnboardingStatus(
            onboarding_completed=bool(current_user.onboarding_completed),
            default_category=current_user.default_category,
            needs_onboarding=not bool(current_user.onboarding_completed)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting onboarding status: {str(e)}")


@app.post("/onboarding/complete")
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """Complete user onboarding"""
    try:
        # Update user's onboarding status and default category
        from auth.services import AuthService
        auth_service = AuthService(db)
        success = auth_service.complete_user_onboarding(
            user_id=str(current_user.id),
            default_category=onboarding_data.default_category
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to complete onboarding")

        # Create initial categories if provided
        for category_name in onboarding_data.categories:
            if category_name.strip():
                task_manager.create_category(
                    name=category_name.strip(),
                    description="Category created during onboarding",
                    color="#007bff"  # Default blue color
                )

        return {
            "message": "Onboarding completed successfully",
            "default_category": onboarding_data.default_category,
            "categories_created": len(onboarding_data.categories)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing onboarding: {str(e)}")


@app.get("/onboarding/check")
async def check_onboarding_required(current_user: User = Depends(get_current_user)):
    """Check if user needs onboarding (used by frontend for routing)"""
    return {
        "requires_onboarding": not bool(current_user.onboarding_completed),
        "user_id": str(current_user.id),
        "username": current_user.username
    }


# System Control Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Basic health checks
        data_dir_accessible = DATA_DIR.exists() and DATA_DIR.is_dir()

        # Check database connection
        db_healthy = check_database_connection()

        # Check if task system is loadable (basic functionality test)
        tasks_loadable = True
        try:
            # Simple test to see if we can instantiate task manager
            from business.task_manager import TaskManager

            TaskManager()  # Just test instantiation
            tasks_loadable = True
        except Exception as e:
            logger.warning(f"Task system check failed: {e}")
            tasks_loadable = False

        overall_healthy = db_healthy and tasks_loadable

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": get_version_string(),
            "data_directory_accessible": data_dir_accessible,
            "database_healthy": db_healthy,
            "tasks_loadable": tasks_loadable,
            "storage_type": "postgresql",
        }
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.get("/system/data-location")
async def get_data_location(current_user: User = Depends(get_current_user)):
    """Get information about data storage location"""
    return {
        "database_type": Config.DATABASE_TYPE,
        "data_storage": "PostgreSQL Database",
        "data_directory": str(DATA_DIR),  # Only used for invoice exports
        "status": "database_only",
    }


@app.post("/system/shutdown")
async def shutdown_application(current_user: User = Depends(get_current_user)):
    """Shutdown the application gracefully"""
    import threading
    import time

    def delayed_shutdown():
        time.sleep(1)  # Give response time to be sent
        print("\n🛑 Shutdown requested from web interface...")
        print("💾 All data has been saved automatically")
        print("👋 Thank you for using ClockIt!")
        os._exit(0)  # Force exit

    # Start shutdown in background thread
    shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
    shutdown_thread.start()

    return {"message": "Shutdown initiated"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host=Config.HOST, port=Config.PORT, log_level=Config.LOG_LEVEL.lower()
    )
