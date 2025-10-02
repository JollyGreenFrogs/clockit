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
from ms_planner_integration import PlannerConfig, MSPlannerClient, sync_planner_tasks
from version import get_version_string, get_full_version_info
from logging_config import configure_logging
from config import Config
from database.init import init_database, check_database_connection
from database.connection import get_db
from database.repositories import ConfigRepository, CurrencyRepository
from business.task_manager import TaskManager
from business.rate_manager import RateManager
from business.currency_manager import CurrencyManager
from business.invoice_manager import InvoiceManager
import logging
from auth.routes import router as auth_router
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

# Use configuration for data directory (legacy support)
DATA_DIR = Config.DATA_DIR

# Initialize business managers (updated to not require data_dir)
task_manager = TaskManager()
rate_manager = RateManager(DATA_DIR)  # Keep file-based for now
currency_manager = CurrencyManager()
invoice_manager = InvoiceManager(DATA_DIR, task_manager)  # Pass task_manager instance

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

# Default currency settings
DEFAULT_CURRENCY = {
    "code": "USD",
    "symbol": "$",
    "name": "US Dollar"
}

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

# Load tasks data
def load_tasks_data():
    return task_manager.load_tasks()

# Save tasks data
def save_tasks_data(tasks_data):
    return task_manager.save_tasks(tasks_data)

# Load rates config
def load_rates_config():
    return rate_manager.load_rates()

# Save rates config  
def save_rates_config(rates):
    return rate_manager.save_rates(rates)

# Load currency config
def load_currency_config():
    return currency_manager.load_currency_config()

# Save currency config
def save_currency_config(config):
    return currency_manager.save_currency_config(config)

# Load exported tasks
def load_exported_tasks():
    return task_manager.load_exported_tasks()

# Get current currency info
def get_current_currency():
    return currency_manager.get_current_currency()

# Format currency amount
def format_currency(amount, currency_config=None):
    return currency_manager.format_currency(amount, currency_config)

# Calculate hourly rate from day rate (assuming 8 hour work day)
def calculate_hourly_rate(day_rate):
    return rate_manager.calculate_hourly_rate(day_rate)



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

@app.get("/")
async def read_root():
    """
    Serve development info or main application page
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
    
    # Production mode - serve the extracted HTML frontend
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if not frontend_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(frontend_path)

    config_status = {
        'tenant_id_set': bool(config.get('tenant_id')),
        'client_id_set': bool(config.get('client_id')),
        'client_secret_set': bool(config.get('client_secret')),
        'fully_configured': all([config.get('tenant_id'), config.get('client_id'), config.get('client_secret')])
    }
    
    return config_status

@app.post("/planner/setup")
async def setup_planner_config():
    """Create sample configuration file for Microsoft Planner"""
    try:
        PlannerConfig.create_sample_config()
        return {
            'message': 'Sample configuration file created: planner_config_sample.json',
            'instructions': [
                '1. Register an app in Azure AD (https://portal.azure.com)',
                '2. Add Microsoft Graph API permissions: Tasks.Read, Group.Read.All', 
                '3. Grant admin consent for the permissions',
                '4. Copy Tenant ID, Client ID, and create a Client Secret',
                '5. Rename planner_config_sample.json to planner_config.json and update with your values'
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create config: {str(e)}")

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
        date=time_entry.date
    )
    
    if success:
        return {"message": "Time entry added successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add time entry")

# Rate Configuration Endpoints
@app.get("/rates")
async def get_rates():
    """Get all rate configurations"""
    return load_rates_config()

@app.post("/rates")
async def set_rate(rate_config: RateConfig):
    """Set day rate for a task type"""
    rates = load_rates_config()
    rates[rate_config.task_type] = rate_config.day_rate
    save_rates_config(rates)
    
    hourly_rate = calculate_hourly_rate(rate_config.day_rate)
    currency = get_current_currency()
    
    return {
        "message": f"Rate set for {rate_config.task_type}",
        "day_rate": rate_config.day_rate,
        "hourly_rate": hourly_rate,
        "currency": currency
    }

@app.put("/rates/{task_type}")
async def update_rate(task_type: str, rate_config: RateConfig):
    """Update existing rate for a task type"""
    rates = load_rates_config()
    
    if task_type not in rates:
        raise HTTPException(status_code=404, detail="Task type not found")
    
    rates[task_type] = rate_config.day_rate
    save_rates_config(rates)
    
    hourly_rate = calculate_hourly_rate(rate_config.day_rate)
    currency = get_current_currency()
    
    return {
        "message": f"Rate updated for {task_type}",
        "day_rate": rate_config.day_rate,
        "hourly_rate": hourly_rate,
        "currency": currency
    }

@app.delete("/rates/{task_type}")
async def delete_rate(task_type: str):
    """Delete a rate configuration"""
    rates = load_rates_config()
    
    if task_type not in rates:
        raise HTTPException(status_code=404, detail="Task type not found")
    
    del rates[task_type]
    save_rates_config(rates)
    
    return {"message": f"Rate deleted for {task_type}"}

# Currency Configuration Endpoints
@app.get("/currency")
async def get_currency(current_user: User = Depends(get_current_user)):
    """Get current currency configuration for the authenticated user"""
    db = next(get_db())
    config_repo = ConfigRepository(db)
    
    user_currency = config_repo.get_config("currency", str(current_user.id))
    if not user_currency:
        # Fallback to USD if somehow no currency is set (shouldn't happen for new users)
        default_currency = {"code": "USD", "symbol": "$", "name": "US Dollar"}
        return {"currency": default_currency}
    
    return {"currency": user_currency}

@app.get("/currencies")
async def get_currencies():
    """Get list of all available currencies"""
    try:
        db = next(get_db())
        currency_repo = CurrencyRepository(db)
        currencies = currency_repo.get_all_currencies()
        
        # Debug logging
        print(f"DEBUG: Found {len(currencies)} currencies in database")
        
        return {"currencies": currencies}
    except Exception as e:
        print(f"ERROR: Failed to load currencies: {e}")
        # Fallback to a basic set if database fails
        fallback_currencies = [
            {"code": "USD", "symbol": "$", "name": "US Dollar"},
            {"code": "EUR", "symbol": "€", "name": "Euro"},
            {"code": "GBP", "symbol": "£", "name": "British Pound"}
        ]
        return {"currencies": fallback_currencies}

@app.get("/currency/available")
async def get_available_currencies():
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
async def get_categories():
    """Get list of all task types from rate configuration"""
    rates = load_rates_config()
    
    # Return sorted list of task types that have rates configured
    categories = sorted(list(rates.keys()))
    return categories

# Invoice Generation Endpoints
@app.post("/invoice/generate")
async def generate_invoice():
    """Generate invoice from non-exported tasks"""
    tasks_data = load_tasks_data()
    rates = load_rates_config()
    exported_data = load_exported_tasks()
    
    # Group tasks by parent heading
    grouped_tasks = {}
    invoice_data = []
    exported_task_ids = []
    
    for task_id, task in tasks_data["tasks"].items():
        # Skip already exported tasks
        if task.get("exported", False) or task_id in exported_data.get("exported_task_ids", []):
            continue
            
        # Skip tasks with no time entries
        if task["total_hours"] == 0:
            continue
        
        parent_heading = task.get("parent_heading", "General")
        
        if parent_heading not in grouped_tasks:
            grouped_tasks[parent_heading] = []
        
        grouped_tasks[parent_heading].append({
            "task_id": task_id,
            "name": task["name"],
            "total_hours": task["total_hours"]
        })
    
    # Generate invoice lines
    for heading, tasks in grouped_tasks.items():
        total_hours = sum(task["total_hours"] for task in tasks)
        
        # Try to find rate by heading or use default rate
        day_rate = rates.get(heading, rates.get("default", 100.0))
        hour_rate = calculate_hourly_rate(day_rate)
        amount = total_hours * hour_rate
        
        # Bundle tasks with same parent heading
        task_names = ", ".join(task["name"] for task in tasks)
        
        # Get currency for formatting
        currency = get_current_currency()
        
        invoice_line = {
            "Task": task_names,
            "Total Hours": round(total_hours, 2),
            "Day Rate": format_currency(day_rate, currency),
            "Hour Rate": format_currency(hour_rate, currency),
            "Amount": format_currency(amount, currency)
        }
        
        invoice_data.append(invoice_line)
        
        # Mark tasks as exported
        for task in tasks:
            exported_task_ids.append(task["task_id"])
    
    if not invoice_data:
        return {"message": "No tasks available for invoicing", "invoice": []}
    
    # Calculate totals
    total_hours = sum(line["Total Hours"] for line in invoice_data)
    # Calculate total amount from raw values
    total_amount = 0
    for heading, tasks in grouped_tasks.items():
        heading_hours = sum(task["total_hours"] for task in tasks)
        day_rate = rates.get(heading, rates.get("default", 100.0))
        hour_rate = calculate_hourly_rate(day_rate)
        total_amount += heading_hours * hour_rate
    
    # Add totals row
    currency = get_current_currency()
    invoice_data.append({
        "Task": "TOTAL",
        "Total Hours": round(total_hours, 2),
        "Day Rate": "",
        "Hour Rate": "",
        "Amount": format_currency(total_amount, currency)
    })
    
    # Mark tasks as exported
    for task_id in exported_task_ids:
        tasks_data["tasks"][task_id]["exported"] = True
    
    save_tasks_data(tasks_data)
    
    # Update exported tasks tracking
    exported_data["exported_task_ids"].extend(exported_task_ids)
    save_exported_tasks(exported_data)
    
    return {
        "message": f"Invoice generated with {len(exported_task_ids)} tasks",
        "invoice": invoice_data,
        "export_date": datetime.now().isoformat()
    }

@app.get("/invoice/preview")
async def preview_invoice():
    """Preview invoice without marking tasks as exported"""
    tasks_data = load_tasks_data()
    rates = load_rates_config()
    exported_data = load_exported_tasks()
    
    # Group tasks by parent heading
    grouped_tasks = {}
    invoice_data = []
    
    for task_id, task in tasks_data["tasks"].items():
        # Skip already exported tasks
        if task.get("exported", False) or task_id in exported_data.get("exported_task_ids", []):
            continue
            
        # Skip tasks with no time entries
        if task["total_hours"] == 0:
            continue
        
        parent_heading = task.get("parent_heading", "General")
        
        if parent_heading not in grouped_tasks:
            grouped_tasks[parent_heading] = []
        
        grouped_tasks[parent_heading].append({
            "name": task["name"],
            "total_hours": task["total_hours"]
        })
    
    # Generate invoice lines
    for heading, tasks in grouped_tasks.items():
        total_hours = sum(task["total_hours"] for task in tasks)
        
        # Try to find rate by heading or use default rate
        day_rate = rates.get(heading, rates.get("default", 100.0))
        hour_rate = calculate_hourly_rate(day_rate)
        amount = total_hours * hour_rate
        
        # Bundle tasks with same parent heading
        task_names = ", ".join(task["name"] for task in tasks)
        
        # Get currency for formatting
        currency = get_current_currency()
        
        invoice_line = {
            "Task": task_names,
            "Total Hours": round(total_hours, 2),
            "Day Rate": format_currency(day_rate, currency),
            "Hour Rate": format_currency(hour_rate, currency),
            "Amount": format_currency(amount, currency)
        }
        
        invoice_data.append(invoice_line)
    
    if not invoice_data:
        return {"message": "No tasks available for invoicing", "invoice": []}
    
    # Calculate totals
    total_hours = sum(line["Total Hours"] for line in invoice_data)
    # Calculate total amount from raw values
    total_amount = 0
    for heading, tasks in grouped_tasks.items():
        heading_hours = sum(task["total_hours"] for task in tasks)
        day_rate = rates.get(heading, rates.get("default", 100.0))
        hour_rate = calculate_hourly_rate(day_rate)
        total_amount += heading_hours * hour_rate
    
    # Add totals row
    currency = get_current_currency()
    invoice_data.append({
        "Task": "TOTAL",
        "Total Hours": round(total_hours, 2),
        "Day Rate": "",
        "Hour Rate": "",
        "Amount": format_currency(total_amount, currency)
    })
    
    return {
        "message": "Invoice preview (not exported)",
        "invoice": invoice_data
    }

# Microsoft Planner Integration Endpoints
@app.post("/planner/sync")
async def sync_planner_tasks_endpoint():
    """Sync tasks from Microsoft Planner"""
    config = PlannerConfig.load_config()
    
    if not all([config.get('tenant_id'), config.get('client_id'), config.get('client_secret')]):
        raise HTTPException(status_code=400, detail="Microsoft Planner not configured. Use /planner/setup first.")
    
    try:
        client = MSPlannerClient(
            tenant_id=config['tenant_id'],
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )
        
        tasks_data = load_tasks_data()
        new_tasks = await sync_planner_tasks(client, tasks_data["tasks"])
        
        # Add new tasks to local storage
        for task in new_tasks:
            task_id = str(len(tasks_data["tasks"]) + 1)
            new_task = {
                "id": task_id,
                "name": task["name"],
                "description": task["description"],
                "parent_heading": task.get("external_source", "MS Planner"),
                "time_entries": [],
                "total_hours": 0,
                "created_at": datetime.now().isoformat(),
                "exported": False,
                "external_id": task.get("external_id"),
                "external_source": task.get("external_source")
            }
            tasks_data["tasks"][task_id] = new_task
        
        save_tasks_data(tasks_data)
        
        return {
            "message": f"Synced {len(new_tasks)} new tasks from Microsoft Planner",
            "new_tasks": len(new_tasks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync with Planner: {str(e)}")

# System Control Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Basic health checks
        data_dir_accessible = DATA_DIR.exists() and DATA_DIR.is_dir()
        
        # Check if we can load tasks (basic functionality test)
        tasks_data = load_tasks_data()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": get_version_string(),
            "data_directory_accessible": data_dir_accessible,
            "tasks_loadable": bool(tasks_data)
        }
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/system/data-location")
async def get_data_location():
    """Get the data storage location"""
    return {
        "data_directory": str(DATA_DIR),
        "tasks_file": str(TASKS_DATA_FILE),
        "rates_file": str(RATES_CONFIG_FILE),
        "exported_file": str(EXPORTED_TASKS_FILE)
    }

@app.post("/system/shutdown")
async def shutdown_application():
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
        app, 
        host=Config.HOST, 
        port=Config.PORT,
        log_level=Config.LOG_LEVEL.lower()
    )
