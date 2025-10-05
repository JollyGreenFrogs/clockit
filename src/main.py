import os
import json
import signal
import threading
import webbrowser
from datetime import datetime, date
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from pydantic import BaseModel
from .version import get_version_string, get_full_version_info
from .logging_config import configure_logging
from .config import Config
from .database.init import init_database, check_database_connection
from .database.connection import get_db
from .database.repositories import ConfigRepository, CurrencyRepository
from .business.task_manager import TaskManager
from .business.rate_manager import RateManager
from .business.currency_manager import CurrencyManager
from .business.invoice_manager import InvoiceManager
import logging
from .auth.routes import router as auth_router
from auth.dependencies import get_current_user, get_optional_user
from database.auth_models import User

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
    logger.error("Database connection failed. Please check your database configuration.")
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
invoice_manager = InvoiceManager(DATA_DIR, task_manager)  # Keep for invoice file exports

def initialize_application() -> None:
    """Initialize the application by creating necessary directories.

    All configuration is now stored in the database.
    """
    logger.info("Initializing ClockIt; data directory=%s", DATA_DIR)

    # Ensure data directory exists for file uploads/exports
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception("Could not create data directory %s; falling back to cwd", DATA_DIR)

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
    parent_heading: Optional[str] = ""

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



app = FastAPI(title="ClockIt - Time Tracker", version=get_full_version_info()["version"])

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

# Version endpoint
@app.get("/version")
async def get_version():
    """Get application version information"""
    return get_full_version_info()

# Serve a simple HTML page at the root
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Mount static files for production frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path / "assets"), name="static")

@app.get("/")
async def read_root():
    """
    Serve the React frontend or development info
    """
    # Check if we're in development mode (React dev server running)
    dev_mode = os.getenv('CLOCKIT_DEV_MODE', 'false').lower() == 'true'
    
    if dev_mode:
        # Return development info instead of serving the old frontend
        return JSONResponse({
            "message": "ClockIt API Server",
            "status": "running",
            "version": get_version_string(),
            "development": True,
            "react_frontend": "http://localhost:5173",
            "api_docs": "http://localhost:8000/docs",
            "endpoints": {
                "tasks": "/tasks",
                "rates": "/rates", 
                "currency": "/currency",
                "invoice": "/invoice",
                "health": "/health"
            }
        })
    
    # Production mode - serve the built React frontend
    frontend_index = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    else:
        # Fallback if frontend not built
        return JSONResponse({
            "message": "ClockIt API Server",
            "status": "running",
            "version": get_version_string(),
            "note": "Frontend not built. Please build the React frontend for production.",
            "api_docs": "/docs"
        })


# Task Management Endpoints
@app.get("/tasks")
async def get_tasks(current_user: User = Depends(get_current_user)):
    """Get all tasks for authenticated user"""
    tasks_data = task_manager.load_tasks_for_user(str(current_user.id))
    return tasks_data

@app.post("/tasks")
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user)):
    """Create a new task for authenticated user"""
    # Use task manager to create task with user context
    success = task_manager.create_task_for_user(
        name=task.name,
        user_id=str(current_user.id),
        description=task.description or "",
        category=getattr(task, 'category', ''),
        task_type=getattr(task, 'task_type', ''),
        priority=getattr(task, 'priority', ''),
        hourly_rate=getattr(task, 'hourly_rate', None)
    )
    
    if success:
        return {"message": "Task created successfully", "task_name": task.name}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task")

@app.post("/tasks/{task_id}/time")
async def add_time_entry(task_id: str, time_entry: TimeEntry, current_user: User = Depends(get_current_user)):
    """Add time entry to existing task for authenticated user"""
    success = task_manager.add_time_entry(
        task_name=task_id,  # Note: This assumes task_id is actually task name
        duration=time_entry.hours,
        description=time_entry.description or "",
        date=time_entry.date,
        user_id=str(current_user.id)
    )
    
    if success:
        return {"message": "Time entry added successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add time entry")

@app.delete("/tasks/{task_name}")
async def delete_task(task_name: str, current_user: User = Depends(get_current_user)):
    """Delete a task for authenticated user"""
    success = task_manager.delete_task(
        task_name=task_name,
        user_id=str(current_user.id)
    )
    
    if success:
        return {"message": "Task deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete task")

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
async def set_rate(rate_config: RateConfig, current_user: User = Depends(get_current_user)):
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
            raise HTTPException(status_code=500, detail="Failed to save rate configuration")
        
        hourly_rate = rate_config.day_rate / 8  # Assuming 8-hour workday
        
        # Get user's currency
        user_currency = config_repo.get_config("currency", str(current_user.id))
        
        return {
            "message": f"Rate set for {rate_config.task_type}",
            "day_rate": rate_config.day_rate,
            "hourly_rate": hourly_rate,
            "currency": user_currency
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set rate: {e}")
        raise HTTPException(status_code=500, detail="Failed to set rate")

@app.put("/rates/{task_type}")
async def update_rate(task_type: str, rate_config: RateConfig, current_user: User = Depends(get_current_user)):
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
            "currency": user_currency
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
        raise HTTPException(status_code=500, detail="Failed to load currencies from database")

@app.get("/currency/available")
async def get_available_currencies(current_user: User = Depends(get_current_user)):
    """Get list of all available currencies"""
    db = next(get_db())
    currency_repo = CurrencyRepository(db)
    currencies = currency_repo.get_all_currencies()
    return {"currencies": currencies}

@app.post("/currency")
async def set_currency(currency_config: CurrencyConfig, current_user: User = Depends(get_current_user)):
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
        raise HTTPException(status_code=500, detail="Failed to save currency configuration")
    
    return {
        "message": f"Currency set to {currency_data['name']}",
        "currency": currency_data
    }

# Categories Endpoints
@app.get("/categories")
async def get_categories(current_user: User = Depends(get_current_user)):
    """Get list of all task types from rate configuration"""
    try:
        db = next(get_db())
        config_repo = ConfigRepository(db)
        rates = config_repo.get_config("rates", str(current_user.id)) or {}
        
        # Return sorted list of task types that have rates configured
        categories = sorted(list(rates.keys()))
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Failed to load categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to load categories")

# Invoice Generation Endpoints
@app.post("/invoice/generate")
async def generate_invoice(current_user: User = Depends(get_current_user)):
    """Generate invoice from non-exported tasks"""
    # TODO: Implement database-based invoice generation
    # This will use TaskRepository to get user tasks and ConfigRepository for rates
    return {
        "message": "Invoice generation feature coming soon",
        "status": "not_implemented"
    }

@app.get("/invoice/preview")
async def preview_invoice(current_user: User = Depends(get_current_user)):
    """Preview invoice without marking tasks as exported"""
    # TODO: Implement database-based invoice preview
    return {
        "message": "Invoice preview feature coming soon",
        "status": "not_implemented"
    }
    
    return {
        "message": "Invoice preview (not exported)",
        "invoice": invoice_data
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
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": get_version_string(),
            "data_directory_accessible": data_dir_accessible,
            "database_healthy": db_healthy,
            "storage_type": "postgresql"
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
        "status": "database_only"
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

# Catch-all route for React Router (SPA) - MUST BE LAST!
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve React SPA for any unmatched routes (for client-side routing)
    This route MUST be defined last to avoid interfering with API routes
    """
    # Skip API routes and docs
    if (full_path.startswith("docs") or 
        full_path.startswith("openapi.json") or
        full_path.startswith("health") or
        full_path.startswith("tasks") or
        full_path.startswith("rates") or
        full_path.startswith("currency") or
        full_path.startswith("categories") or
        full_path.startswith("invoice") or
        full_path.startswith("system") or
        full_path.startswith("auth")):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Check if we're in development mode
    dev_mode = os.getenv('CLOCKIT_DEV_MODE', 'false').lower() == 'true'
    if dev_mode:
        raise HTTPException(status_code=404, detail="Development mode - use React dev server")
    
    # Serve React app for any non-API route
    frontend_index = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=Config.HOST, 
        port=Config.PORT,
        log_level=Config.LOG_LEVEL.lower()
    )
