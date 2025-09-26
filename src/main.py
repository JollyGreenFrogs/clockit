
import os
import json
import signal
import threading
import webbrowser
from datetime import datetime, date
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ms_planner_integration import PlannerConfig, MSPlannerClient, sync_planner_tasks
from version import get_version_string, get_full_version_info

# Get data directory from environment or use default
DATA_DIR = Path(os.environ.get('CLOCKIT_DATA_DIR', './clockit_data'))
DATA_DIR.mkdir(exist_ok=True)

INVOICE_COLUMNS_FILE = DATA_DIR / "invoice_columns.json"
DEFAULT_INVOICE_COLUMNS = ["Task", "Total Hours", "Day Rate", "Hour Rate", "Amount"]
TASKS_DATA_FILE = DATA_DIR / "tasks_data.json"
RATES_CONFIG_FILE = DATA_DIR / "rates_config.json"
EXPORTED_TASKS_FILE = DATA_DIR / "exported_tasks.json"
CURRENCY_CONFIG_FILE = DATA_DIR / "currency_config.json"

# Initialization function to ensure all required files exist
def initialize_application():
    """Initialize the application by creating necessary directories and default files"""
    print(f"🚀 Initializing ClockIt...")
    print(f"📁 Data directory: {DATA_DIR}")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Initialize invoice columns file if it doesn't exist
    if not INVOICE_COLUMNS_FILE.exists():
        print("📋 Creating default invoice columns configuration...")
        try:
            with open(INVOICE_COLUMNS_FILE, 'w') as f:
                json.dump(DEFAULT_INVOICE_COLUMNS, f, indent=2)
            print(f"✅ Created: {INVOICE_COLUMNS_FILE}")
        except Exception as e:
            print(f"❌ Error creating invoice columns file: {e}")
    
    # Initialize tasks data file if it doesn't exist
    if not TASKS_DATA_FILE.exists():
        print("📝 Creating default tasks data file...")
        try:
            with open(TASKS_DATA_FILE, 'w') as f:
                json.dump({"tasks": {}}, f, indent=2)
            print(f"✅ Created: {TASKS_DATA_FILE}")
        except Exception as e:
            print(f"❌ Error creating tasks data file: {e}")
    
    # Initialize rates config file if it doesn't exist
    if not RATES_CONFIG_FILE.exists():
        print("💰 Creating default rates configuration...")
        try:
            with open(RATES_CONFIG_FILE, 'w') as f:
                json.dump({}, f, indent=2)
            print(f"✅ Created: {RATES_CONFIG_FILE}")
        except Exception as e:
            print(f"❌ Error creating rates config file: {e}")
    
    # Initialize exported tasks file if it doesn't exist
    if not EXPORTED_TASKS_FILE.exists():
        print("📤 Creating default exported tasks file...")
        try:
            with open(EXPORTED_TASKS_FILE, 'w') as f:
                json.dump({"exported_task_ids": []}, f, indent=2)
            print(f"✅ Created: {EXPORTED_TASKS_FILE}")
        except Exception as e:
            print(f"❌ Error creating exported tasks file: {e}")
    
    # Initialize currency config file if it doesn't exist
    if not CURRENCY_CONFIG_FILE.exists():
        print("💱 Creating default currency configuration...")
        try:
            with open(CURRENCY_CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CURRENCY, f, indent=2)
            print(f"✅ Created: {CURRENCY_CONFIG_FILE}")
        except Exception as e:
            print(f"❌ Error creating currency config file: {e}")
    
    print("🎉 Application initialization complete!")
    print("=" * 60)

# Default currency settings
DEFAULT_CURRENCY = {
    "code": "USD",
    "symbol": "$",
    "name": "US Dollar"
}

# Common currencies - EUR and GBP first, then alphabetical
CURRENCIES = {
    "EUR": {"symbol": "€", "name": "Euro"},
    "GBP": {"symbol": "£", "name": "British Pound"},
    "AED": {"symbol": "د.إ", "name": "UAE Dirham"},
    "AFN": {"symbol": "؋", "name": "Afghan Afghani"},
    "ALL": {"symbol": "L", "name": "Albanian Lek"},
    "AMD": {"symbol": "֏", "name": "Armenian Dram"},
    "AOA": {"symbol": "Kz", "name": "Angolan Kwanza"},
    "ARS": {"symbol": "$", "name": "Argentine Peso"},
    "AUD": {"symbol": "A$", "name": "Australian Dollar"},
    "AWG": {"symbol": "ƒ", "name": "Aruban Florin"},
    "AZN": {"symbol": "₼", "name": "Azerbaijani Manat"},
    "BAM": {"symbol": "КМ", "name": "Bosnia and Herzegovina Convertible Mark"},
    "BBD": {"symbol": "Bds$", "name": "Barbadian Dollar"},
    "BDT": {"symbol": "৳", "name": "Bangladeshi Taka"},
    "BGN": {"symbol": "лв", "name": "Bulgarian Lev"},
    "BHD": {"symbol": "د.ب", "name": "Bahraini Dinar"},
    "BIF": {"symbol": "FBu", "name": "Burundian Franc"},
    "BOB": {"symbol": "Bs.", "name": "Bolivian Boliviano"},
    "BRL": {"symbol": "R$", "name": "Brazilian Real"},
    "BSD": {"symbol": "$", "name": "Bahamian Dollar"},
    "BWP": {"symbol": "P", "name": "Botswana Pula"},
    "BZD": {"symbol": "BZ$", "name": "Belize Dollar"},
    "CAD": {"symbol": "C$", "name": "Canadian Dollar"},
    "CDF": {"symbol": "FC", "name": "Congolese Franc"},
    "CHF": {"symbol": "CHF", "name": "Swiss Franc"},
    "CLP": {"symbol": "$", "name": "Chilean Peso"},
    "CNY": {"symbol": "¥", "name": "Chinese Yuan"},
    "COP": {"symbol": "$", "name": "Colombian Peso"},
    "CRC": {"symbol": "₡", "name": "Costa Rican Colón"},
    "CUP": {"symbol": "$", "name": "Cuban Peso"},
    "CVE": {"symbol": "$", "name": "Cape Verdean Escudo"},
    "CZK": {"symbol": "Kč", "name": "Czech Koruna"},
    "DJF": {"symbol": "Fdj", "name": "Djiboutian Franc"},
    "DKK": {"symbol": "kr", "name": "Danish Krone"},
    "DOP": {"symbol": "RD$", "name": "Dominican Peso"},
    "EGP": {"symbol": "£", "name": "Egyptian Pound"},
    "ERN": {"symbol": "Nfk", "name": "Eritrean Nakfa"},
    "ETB": {"symbol": "Br", "name": "Ethiopian Birr"},
    "FJD": {"symbol": "$", "name": "Fijian Dollar"},
    "GEL": {"symbol": "₾", "name": "Georgian Lari"},
    "GHS": {"symbol": "₵", "name": "Ghanaian Cedi"},
    "GMD": {"symbol": "D", "name": "Gambian Dalasi"},
    "GNF": {"symbol": "FG", "name": "Guinean Franc"},
    "GTQ": {"symbol": "Q", "name": "Guatemalan Quetzal"},
    "GYD": {"symbol": "$", "name": "Guyanese Dollar"},
    "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar"},
    "HNL": {"symbol": "L", "name": "Honduran Lempira"},
    "HRK": {"symbol": "kn", "name": "Croatian Kuna"},
    "HUF": {"symbol": "Ft", "name": "Hungarian Forint"},
    "IDR": {"symbol": "Rp", "name": "Indonesian Rupiah"},
    "ILS": {"symbol": "₪", "name": "Israeli Shekel"},
    "INR": {"symbol": "₹", "name": "Indian Rupee"},
    "IRR": {"symbol": "﷼", "name": "Iranian Rial"},
    "ISK": {"symbol": "kr", "name": "Icelandic Króna"},
    "JMD": {"symbol": "J$", "name": "Jamaican Dollar"},
    "JOD": {"symbol": "د.ا", "name": "Jordanian Dinar"},
    "JPY": {"symbol": "¥", "name": "Japanese Yen"},
    "KES": {"symbol": "KSh", "name": "Kenyan Shilling"},
    "KRW": {"symbol": "₩", "name": "South Korean Won"},
    "KWD": {"symbol": "د.ك", "name": "Kuwaiti Dinar"},
    "KZT": {"symbol": "₸", "name": "Kazakhstani Tenge"},
    "LBP": {"symbol": "ل.ل", "name": "Lebanese Pound"},
    "LKR": {"symbol": "Rs", "name": "Sri Lankan Rupee"},
    "LRD": {"symbol": "$", "name": "Liberian Dollar"},
    "LSL": {"symbol": "L", "name": "Lesotho Loti"},
    "MAD": {"symbol": "د.م.", "name": "Moroccan Dirham"},
    "MKD": {"symbol": "ден", "name": "Macedonian Denar"},
    "MWK": {"symbol": "MK", "name": "Malawian Kwacha"},
    "MXN": {"symbol": "$", "name": "Mexican Peso"},
    "MYR": {"symbol": "RM", "name": "Malaysian Ringgit"},
    "MZN": {"symbol": "MT", "name": "Mozambican Metical"},
    "NAD": {"symbol": "$", "name": "Namibian Dollar"},
    "NGN": {"symbol": "₦", "name": "Nigerian Naira"},
    "NIO": {"symbol": "C$", "name": "Nicaraguan Córdoba"},
    "NOK": {"symbol": "kr", "name": "Norwegian Krone"},
    "NPR": {"symbol": "Rs", "name": "Nepalese Rupee"},
    "NZD": {"symbol": "NZ$", "name": "New Zealand Dollar"},
    "OMR": {"symbol": "ر.ع.", "name": "Omani Rial"},
    "PAB": {"symbol": "B/.", "name": "Panamanian Balboa"},
    "PEN": {"symbol": "S/", "name": "Peruvian Sol"},
    "PGK": {"symbol": "K", "name": "Papua New Guinean Kina"},
    "PHP": {"symbol": "₱", "name": "Philippine Peso"},
    "PKR": {"symbol": "Rs", "name": "Pakistani Rupee"},
    "PLN": {"symbol": "zł", "name": "Polish Złoty"},
    "PYG": {"symbol": "₲", "name": "Paraguayan Guaraní"},
    "QAR": {"symbol": "ر.ق", "name": "Qatari Riyal"},
    "RON": {"symbol": "lei", "name": "Romanian Leu"},
    "RSD": {"symbol": "дин", "name": "Serbian Dinar"},
    "RUB": {"symbol": "₽", "name": "Russian Ruble"},
    "RWF": {"symbol": "RF", "name": "Rwandan Franc"},
    "SAR": {"symbol": "ر.س", "name": "Saudi Riyal"},
    "SBD": {"symbol": "$", "name": "Solomon Islands Dollar"},
    "SEK": {"symbol": "kr", "name": "Swedish Krona"},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar"},
    "SLL": {"symbol": "Le", "name": "Sierra Leonean Leone"},
    "SOS": {"symbol": "S", "name": "Somali Shilling"},
    "SRD": {"symbol": "$", "name": "Surinamese Dollar"},
    "STN": {"symbol": "Db", "name": "São Tomé and Príncipe Dobra"},
    "SZL": {"symbol": "L", "name": "Swazi Lilangeni"},
    "THB": {"symbol": "฿", "name": "Thai Baht"},
    "TND": {"symbol": "د.ت", "name": "Tunisian Dinar"},
    "TOP": {"symbol": "T$", "name": "Tongan Paʻanga"},
    "TRY": {"symbol": "₺", "name": "Turkish Lira"},
    "TTD": {"symbol": "TT$", "name": "Trinidad and Tobago Dollar"},
    "TZS": {"symbol": "TSh", "name": "Tanzanian Shilling"},
    "UGX": {"symbol": "USh", "name": "Ugandan Shilling"},
    "USD": {"symbol": "$", "name": "US Dollar"},
    "UYU": {"symbol": "$U", "name": "Uruguayan Peso"},
    "UZS": {"symbol": "сўм", "name": "Uzbekistani Som"},
    "VES": {"symbol": "Bs.S", "name": "Venezuelan Bolívar"},
    "VND": {"symbol": "₫", "name": "Vietnamese Dong"},
    "VUV": {"symbol": "Vt", "name": "Vanuatu Vatu"},
    "WST": {"symbol": "T", "name": "Samoan Tālā"},
    "XAF": {"symbol": "CFA", "name": "Central African CFA Franc"},
    "XAG": {"symbol": "Ag", "name": "Silver (troy ounce)"},
    "XAU": {"symbol": "Au", "name": "Gold (troy ounce)"},
    "XCD": {"symbol": "$", "name": "East Caribbean Dollar"},
    "XDR": {"symbol": "SDR", "name": "Special Drawing Rights"},
    "XOF": {"symbol": "CFA", "name": "West African CFA Franc"},
    "ZAR": {"symbol": "R", "name": "South African Rand"},
    "ZMW": {"symbol": "ZK", "name": "Zambian Kwacha"}
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
    code: str
    symbol: str
    name: str

# Load invoice columns config
def load_invoice_columns():
    if os.path.exists(INVOICE_COLUMNS_FILE):
        try:
            with open(INVOICE_COLUMNS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading invoice columns: {e}")
    return DEFAULT_INVOICE_COLUMNS.copy()

# Save invoice columns config
def save_invoice_columns(columns):
    try:
        with open(INVOICE_COLUMNS_FILE, 'w') as f:
            json.dump(columns, f, indent=2)
    except Exception as e:
        print(f"Error saving invoice columns: {e}")

# Load tasks data
def load_tasks_data():
    if os.path.exists(TASKS_DATA_FILE):
        try:
            with open(TASKS_DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading tasks data: {e}")
    return {"tasks": {}}

# Save tasks data
def save_tasks_data(data):
    try:
        with open(TASKS_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving tasks data: {e}")

# Load rates config
def load_rates_config():
    if os.path.exists(RATES_CONFIG_FILE):
        try:
            with open(RATES_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rates config: {e}")
    return {}

# Save rates config
def save_rates_config(rates):
    try:
        with open(RATES_CONFIG_FILE, 'w') as f:
            json.dump(rates, f, indent=2)
    except Exception as e:
        print(f"Error saving rates config: {e}")

# Load exported tasks tracking
def load_exported_tasks():
    if os.path.exists(EXPORTED_TASKS_FILE):
        try:
            with open(EXPORTED_TASKS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading exported tasks: {e}")
    return {"exported_task_ids": []}

# Save exported tasks tracking
def save_exported_tasks(exported_data):
    try:
        with open(EXPORTED_TASKS_FILE, 'w') as f:
            json.dump(exported_data, f, indent=2)
    except Exception as e:
        print(f"Error saving exported tasks: {e}")

# Load currency configuration
def load_currency_config():
    if os.path.exists(CURRENCY_CONFIG_FILE):
        try:
            with open(CURRENCY_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Validate currency exists in our list
                if config.get('code') in CURRENCIES:
                    return config
        except Exception as e:
            print(f"Error loading currency config: {e}")
    return DEFAULT_CURRENCY.copy()

# Save currency configuration
def save_currency_config(currency_config):
    try:
        with open(CURRENCY_CONFIG_FILE, 'w') as f:
            json.dump(currency_config, f, indent=2)
    except Exception as e:
        print(f"Error saving currency config: {e}")

# Get current currency info
def get_current_currency():
    config = load_currency_config()
    return {
        "code": config["code"],
        "symbol": config["symbol"],
        "name": config["name"]
    }

# Format currency amount
def format_currency(amount, currency_config=None):
    if currency_config is None:
        currency_config = load_currency_config()
    
    symbol = currency_config["symbol"]
    
    # Handle different currency formatting styles
    if currency_config["code"] in ["EUR", "GBP", "CHF"]:
        # European style: symbol after amount
        return f"{amount:.2f} {symbol}"
    elif currency_config["code"] in ["JPY", "KRW", "VND"]:
        # No decimal places for some currencies
        return f"{symbol}{amount:.0f}"
    else:
        # Default: symbol before amount
        return f"{symbol}{amount:.2f}"

# Calculate hourly rate from day rate (assuming 8 hour work day)
def calculate_hourly_rate(day_rate):
    return day_rate / 8.0



app = FastAPI(title="ClockIt - Time Tracker", version=get_full_version_info()["version"])

# Initialize application on startup
initialize_application()

# Version endpoint
@app.get("/version")
async def get_version():
    """Get application version information"""
    return get_full_version_info()

# Serve a simple HTML page at the root
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ClockIt - Professional Time Tracker</title>
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container { 
                    max-width: 1400px; 
                    margin: 0 auto; 
                    background: white; 
                    border-radius: 15px; 
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                
                .header h1 { font-size: 2.5em; margin-bottom: 10px; font-weight: 300; }
                .header p { font-size: 1.2em; opacity: 0.9; }
                
                .main-content { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; padding: 30px; }
                
                @media (max-width: 1200px) {
                    .main-content { grid-template-columns: 1fr; }
                }
                
                .section { 
                    background: #f8f9fa; 
                    border-radius: 10px; 
                    padding: 25px;
                    border: 1px solid #e9ecef;
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                }
                
                .section:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                }
                
                .section h3 { 
                    color: #495057; 
                    margin-bottom: 20px; 
                    font-size: 1.5em;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .section-icon { font-size: 1.2em; }
                
                .form-grid { display: grid; gap: 15px; margin-bottom: 20px; }
                .form-row { display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: center; }
                
                label { 
                    font-weight: 600; 
                    color: #495057;
                    font-size: 0.95em;
                }
                
                input, select, textarea { 
                    padding: 12px 15px; 
                    border: 2px solid #e9ecef; 
                    border-radius: 8px;
                    font-size: 0.95em;
                    transition: border-color 0.2s ease, box-shadow 0.2s ease;
                }
                
                input:focus, select:focus, textarea:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                
                textarea { resize: vertical; min-height: 80px; }
                
                .btn {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 0.95em;
                    font-weight: 600;
                    transition: all 0.2s ease;
                    margin: 5px;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .btn:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                }
                
                .btn-secondary {
                    background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
                }
                
                .btn-success {
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                }
                
                .btn-danger {
                    background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
                }
                
                .btn-warning {
                    background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
                    color: #212529;
                }
                
                .btn-group { display: flex; gap: 10px; flex-wrap: wrap; }
                
                table { 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 15px 0;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                
                th, td { 
                    padding: 12px 15px; 
                    text-align: left; 
                    border-bottom: 1px solid #e9ecef;
                }
                
                th { 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-weight: 600;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                tr:hover { background-color: #f8f9fa; }
                
                .status-active { 
                    background: #d4edda; 
                    color: #155724; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    font-size: 0.85em;
                    font-weight: 600;
                }
                
                .status-exported { 
                    background: #f8d7da; 
                    color: #721c24; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    font-size: 0.85em;
                    font-weight: 600;
                }
                
                .alert {
                    padding: 15px 20px;
                    margin: 15px 0;
                    border-radius: 8px;
                    font-weight: 500;
                }
                
                .alert-success { 
                    background: #d4edda; 
                    color: #155724; 
                    border: 1px solid #c3e6cb;
                }
                
                .alert-error { 
                    background: #f8d7da; 
                    color: #721c24; 
                    border: 1px solid #f5c6cb;
                }
                
                .alert-warning { 
                    background: #fff3cd; 
                    color: #856404; 
                    border: 1px solid #ffeeba;
                }
                
                .invoice-section {
                    grid-column: 1 / -1;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                }
                
                .invoice-table th { 
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                }
                
                .total-row { 
                    font-weight: bold; 
                    background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
                    color: #856404;
                }
                
                .rate-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px;
                    background: white;
                    border-radius: 8px;
                    margin: 8px 0;
                    border: 1px solid #e9ecef;
                    transition: all 0.2s ease;
                }
                
                .rate-item:hover {
                    background: #f8f9fa;
                    border-color: #667eea;
                }
                
                .rate-info { flex: 1; }
                .rate-type { font-weight: 600; color: #495057; margin-bottom: 4px; }
                .rate-values { font-size: 0.9em; color: #6c757d; }
                
                .rate-actions { display: flex; gap: 8px; }
                .btn-small { 
                    padding: 6px 12px; 
                    font-size: 0.8em;
                    min-width: auto;
                }
                
                .loading {
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .empty-state {
                    text-align: center;
                    padding: 40px 20px;
                    color: #6c757d;
                }
                
                .empty-state-icon { font-size: 3em; margin-bottom: 15px; opacity: 0.5; }
                .empty-state-text { font-size: 1.1em; }
                
                .quick-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                    margin-bottom: 25px;
                }
                
                .stat-card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    border: 1px solid #e9ecef;
                }
                
                .stat-number {
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 5px;
                }
                
                .stat-label {
                    font-size: 0.9em;
                    color: #6c757d;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                /* Stopwatch Styles */
                .stopwatch-widget {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 25px;
                    border: 2px solid #e9ecef;
                    text-align: center;
                }
                
                .stopwatch-display {
                    margin-bottom: 15px;
                }
                
                .timer-display {
                    font-size: 3em;
                    font-weight: bold;
                    color: #495057;
                    margin-bottom: 20px;
                    font-family: 'Courier New', monospace;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                }
                
                .timer-display.running {
                    color: #28a745;
                    animation: pulse 2s infinite;
                }
                
                .timer-display.paused {
                    color: #ffc107;
                }
                
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.7; }
                    100% { opacity: 1; }
                }
                
                .timer-controls {
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                    flex-wrap: wrap;
                }
                
                .timer-controls .btn {
                    min-width: 100px;
                }
                
                .break-section {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    margin-top: 15px;
                }
                
                .alert-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ffc107;
                    color: #212529;
                    padding: 15px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    z-index: 1000;
                    animation: slideIn 0.3s ease;
                }
                
                @keyframes slideIn {
                    from { transform: translateX(100%); }
                    to { transform: translateX(0); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ ClockIt</h1>
                    <p>Professional Time Tracking & Invoice Generation</p>
                    <small style="opacity: 0.8;">{get_version_string()}</small>
                </div>
                
                <div class="main-content">
                    <!-- Task Management Section -->
                    <div class="section">
                        <h3><span class="section-icon">📋</span>Task Management</h3>
                        
                        <div class="quick-stats">
                            <div class="stat-card">
                                <div class="stat-number" id="totalTasks">0</div>
                                <div class="stat-label">Total Tasks</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number" id="activeTasks">0</div>
                                <div class="stat-label">Active Tasks</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number" id="totalHours">0</div>
                                <div class="stat-label">Total Hours</div>
                            </div>
                        </div>
                        
                        <div class="form-grid">
                            <div class="form-row">
                                <label>Task Name:</label>
                                <input type="text" id="taskName" placeholder="Enter task name">
                            </div>
                            <div class="form-row">
                                <label>Description:</label>
                                <textarea id="taskDescription" placeholder="Task description (optional)"></textarea>
                            </div>
                            <div class="form-row">
                                <label>Category:</label>
                                <div style="display: flex; gap: 10px; align-items: center;">
                                    <select id="categorySelect" onchange="onCategoryChange()" style="flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
                                        <option value="">Select a category...</option>
                                    </select>
                                    <button type="button" class="btn btn-secondary" onclick="showNewCategoryInput()" style="white-space: nowrap;">
                                        <span>➕</span> New
                                    </button>
                                </div>
                                <div id="newCategoryInput" style="display: none; margin-top: 10px;">
                                    <input type="text" id="newCategoryName" placeholder="Enter new category name" style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
                                    <div style="margin-top: 10px; display: flex; gap: 10px;">
                                        <button type="button" class="btn" onclick="addNewCategory()" style="flex: 1;">
                                            <span>✅</span> Add Category
                                        </button>
                                        <button type="button" class="btn btn-secondary" onclick="cancelNewCategory()" style="flex: 1;">
                                            <span>❌</span> Cancel
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="btn-group">
                            <button class="btn" onclick="createTask()">
                                <span>➕</span> Create Task
                            </button>
                            <button class="btn btn-secondary" onclick="loadTasks()">
                                <span>🔄</span> Refresh
                            </button>
                        </div>
                        
                        <div id="taskResult"></div>
                        <div id="tasksList"></div>
                    </div>
                    
                    <!-- Time Tracking Section -->
                    <div class="section">
                        <h3><span class="section-icon">⏱️</span>Time Tracking</h3>
                        
                        <!-- Stopwatch Widget -->
                        <div class="stopwatch-widget">
                            <div class="stopwatch-display">
                                <div class="timer-display" id="timerDisplay">00:00:00</div>
                                <div class="timer-controls">
                                    <button class="btn btn-success" id="startBtn" onclick="startTimer()">
                                        <span>▶️</span> Start
                                    </button>
                                    <button class="btn btn-warning" id="pauseBtn" onclick="pauseTimer()" disabled>
                                        <span>⏸️</span> Pause
                                    </button>
                                    <button class="btn btn-danger" id="stopBtn" onclick="stopTimer()" disabled>
                                        <span>⏹️</span> Stop
                                    </button>
                                </div>
                            </div>
                            <div class="break-section" id="breakSection" style="display: none;">
                                <div class="form-row">
                                    <label>Break time to subtract (minutes):</label>
                                    <input type="number" id="breakMinutes" min="0" placeholder="e.g., 15" value="0">
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-grid">
                            <div class="form-row">
                                <label>Select Task:</label>
                                <select id="timeTaskId">
                                    <option value="">Select a task...</option>
                                </select>
                            </div>
                            <div class="form-row">
                                <label>Hours:</label>
                                <input type="number" id="timeHours" step="0.25" min="0" placeholder="e.g., 2.5">
                            </div>
                            <div class="form-row">
                                <label>Date:</label>
                                <input type="date" id="timeDate">
                            </div>
                            <div class="form-row">
                                <label>Description:</label>
                                <input type="text" id="timeDescription" placeholder="What you worked on">
                            </div>
                        </div>
                        
                        <button class="btn btn-success" onclick="addTimeEntry()">
                            <span>⏰</span> Add Time Entry
                        </button>
                        
                        <div id="timeResult"></div>
                    </div>
                    
                    <!-- Rate Configuration Section -->
                    <div class="section">
                        <h3><span class="section-icon">💰</span>Rate Configuration</h3>
                        
                        <div class="form-grid">
                            <div class="form-row">
                                <label>Currency:</label>
                                <select id="currencySelect">
                                    <option value="">Loading currencies...</option>
                                </select>
                            </div>
                            <div class="form-row">
                                <label>Task Type:</label>
                                <input type="text" id="rateTaskType" placeholder="e.g., Design, Development">
                            </div>
                            <div class="form-row">
                                <label>Day Rate:</label>
                                <div style="display: flex; gap: 10px; align-items: center;">
                                    <span id="currencySymbol" style="font-weight: bold; color: #667eea;">$</span>
                                    <input type="number" id="dayRate" step="1" min="0" placeholder="e.g., 400" style="flex: 1;">
                                </div>
                            </div>
                        </div>
                        
                        <div class="btn-group">
                            <button class="btn" onclick="setRate()">
                                <span>💾</span> Set Rate
                            </button>
                            <button class="btn btn-secondary" onclick="loadRates()">
                                <span>🔄</span> Refresh Rates
                            </button>
                        </div>
                        
                        <div id="rateResult"></div>
                        <div id="ratesList"></div>
                    </div>
                    
                    <!-- Currency Configuration Section -->
                    <div class="section">
                        <h3><span class="section-icon">💱</span>Currency Settings</h3>
                        
                        <div class="form-grid">
                            <div class="form-row">
                                <label>Currency:</label>
                                <select id="currencySelect">
                                    <option value="">Select currency...</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="btn-group">
                            <button class="btn" onclick="applyCurrency()">
                                <span>💾</span> Set Currency
                            </button>
                            <button class="btn btn-secondary" onclick="loadCurrentCurrency()">
                                <span>🔄</span> Refresh
                            </button>
                        </div>
                        
                        <div id="currencyResult"></div>
                        <div id="currentCurrency"></div>
                    </div>
                    
                    <!-- Microsoft Planner Integration Section -->
                    <div class="section">
                        <h3><span class="section-icon">🔗</span>Microsoft Planner</h3>
                        
                        <div class="btn-group">
                            <button class="btn btn-secondary" onclick="checkPlannerConfig()">
                                <span>⚙️</span> Check Config
                            </button>
                            <button class="btn btn-warning" onclick="setupPlanner()">
                                <span>🔧</span> Setup
                            </button>
                            <button class="btn" onclick="syncPlanner()">
                                <span>🔄</span> Sync Tasks
                            </button>
                        </div>
                        
                        <div id="plannerResult"></div>
                    </div>
                    
                    <!-- Invoice Generation Section -->
                    <div class="section invoice-section">
                        <h3><span class="section-icon">🧾</span>Invoice Generation</h3>
                        
                        <div class="btn-group">
                            <button class="btn btn-secondary" onclick="previewInvoice()">
                                <span>👁️</span> Preview Invoice
                            </button>
                            <button class="btn btn-success" onclick="generateInvoice()">
                                <span>📄</span> Generate & Export
                            </button>
                        </div>
                        
                        <div id="invoiceResult"></div>
                        <div id="invoicePreview"></div>
                    </div>
                    
                    <!-- Application Control Section -->
                    <div class="section">
                        <h3><span class="section-icon">⚙️</span>Application Control</h3>
                        
                        <div class="btn-group">
                            <button class="btn btn-secondary" onclick="showDataLocation()">
                                <span>📁</span> Data Location
                            </button>
                            <button class="btn btn-danger" onclick="shutdownApp()">
                                <span>🔴</span> Shutdown ClockIt
                            </button>
                        </div>
                        
                        <div id="controlResult"></div>
                    </div>
                </div>
            </div>
            
            <script>
                // Wait for DOM to be ready before initializing
                document.addEventListener('DOMContentLoaded', function() {
                    // Set today's date as default
                    document.getElementById('timeDate').value = new Date().toISOString().split('T')[0];
                    
                    // Load initial data
                    loadTasks();
                    loadRates();
                    loadCurrencies();
                    loadCurrentCurrency();
                    loadCategories();
                });
                
                let tasksData = {};
                let currentCurrency = { code: 'USD', symbol: '$', name: 'US Dollar' };
                
                // Stopwatch variables
                let startTime = null;
                let elapsedTime = 0;
                let timerInterval = null;
                let isPaused = false;
                let isRunning = false;
                let hourlyAlertShown = false;
                
                // Stopwatch functions
                function startTimer() {
                    if (!isRunning) {
                        startTime = Date.now() - elapsedTime;
                        isRunning = true;
                        isPaused = false;
                        hourlyAlertShown = false;
                    } else if (isPaused) {
                        startTime = Date.now() - elapsedTime;
                        isPaused = false;
                    }
                    
                    timerInterval = setInterval(updateTimerDisplay, 100);
                    
                    // Update button states
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('pauseBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = false;
                    
                    // Update timer display class
                    document.getElementById('timerDisplay').className = 'timer-display running';
                }
                
                function pauseTimer() {
                    if (isRunning && !isPaused) {
                        clearInterval(timerInterval);
                        isPaused = true;
                        
                        // Update button states
                        document.getElementById('startBtn').disabled = false;
                        document.getElementById('pauseBtn').disabled = true;
                        
                        // Update timer display class
                        document.getElementById('timerDisplay').className = 'timer-display paused';
                    }
                }
                
                function stopTimer() {
                    if (isRunning) {
                        clearInterval(timerInterval);
                        
                        // Show break section for editing time
                        document.getElementById('breakSection').style.display = 'block';
                        
                        // Calculate final hours (subtract break time)
                        const breakMinutes = parseFloat(document.getElementById('breakMinutes').value) || 0;
                        const totalMinutes = Math.floor(elapsedTime / 60000);
                        const finalMinutes = Math.max(0, totalMinutes - breakMinutes);
                        const finalHours = (finalMinutes / 60).toFixed(2);
                        
                        // Auto-fill the hours field
                        document.getElementById('timeHours').value = finalHours;
                        
                        // Reset stopwatch
                        resetTimer();
                        
                        // Show notification
                        showTimerAlert(`Timer stopped! Tracked ${finalHours} hours (${totalMinutes} total minutes - ${breakMinutes} break minutes)`, 'success');
                    }
                }
                
                function resetTimer() {
                    clearInterval(timerInterval);
                    elapsedTime = 0;
                    startTime = null;
                    isRunning = false;
                    isPaused = false;
                    hourlyAlertShown = false;
                    
                    // Reset display
                    document.getElementById('timerDisplay').textContent = '00:00:00';
                    document.getElementById('timerDisplay').className = 'timer-display';
                    
                    // Reset button states
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('pauseBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = true;
                    
                    // Hide break section
                    document.getElementById('breakSection').style.display = 'none';
                    document.getElementById('breakMinutes').value = '0';
                }
                
                function updateTimerDisplay() {
                    if (isRunning && !isPaused) {
                        elapsedTime = Date.now() - startTime;
                        
                        const hours = Math.floor(elapsedTime / 3600000);
                        const minutes = Math.floor((elapsedTime % 3600000) / 60000);
                        const seconds = Math.floor((elapsedTime % 60000) / 1000);
                        
                        document.getElementById('timerDisplay').textContent = 
                            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                        
                        // Show hourly alert
                        if (elapsedTime >= 3600000 && !hourlyAlertShown) { // 1 hour = 3600000ms
                            hourlyAlertShown = true;
                            showTimerAlert('⏰ You have been working for 1 hour! Take a break or check if the tracked time is correct.', 'warning');
                        }
                    }
                }
                
                function showTimerAlert(message, type) {
                    // Create alert element
                    const alert = document.createElement('div');
                    alert.className = 'alert-notification';
                    alert.innerHTML = `
                        <strong>${type === 'warning' ? '⚠️' : '✅'}</strong> ${message}
                        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 1.2em; cursor: pointer;">×</button>
                    `;
                    
                    document.body.appendChild(alert);
                    
                    // Auto-remove after 5 seconds
                    setTimeout(() => {
                        if (alert.parentElement) {
                            alert.remove();
                        }
                    }, 5000);
                    
                    // Play notification sound if possible
                    try {
                        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhCjSS3vLHaSAELYHO8diJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhCjSS3vLHaSAELYHO8diJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhCjSS3vLHaSAELYHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhCjSS3vLHaSAE');
                        audio.volume = 0.3;
                        audio.play().catch(() => {}); // Ignore errors if audio can't play
                    } catch (e) {
                        // Audio not supported, ignore
                    }
                }
                
                async function loadCurrencies() {
                    try {
                        const response = await fetch('/currency/available');
                        const currencies = await response.json();
                        
                        const currencySelect = document.getElementById('currencySelect');
                        currencySelect.innerHTML = '';
                        
                        // Sort currencies by code for easier selection
                        const sortedCurrencies = Object.entries(currencies).sort(([a], [b]) => a.localeCompare(b));
                        
                        for (const [code, info] of sortedCurrencies) {
                            const option = document.createElement('option');
                            option.value = code;
                            option.textContent = `${code} - ${info.name} (${info.symbol})`;
                            currencySelect.appendChild(option);
                        }
                        
                    } catch (error) {
                        console.error('Error loading currencies:', error);
                    }
                }
                
                // Function to apply selected currency
                function applyCurrency() {
                    const currencySelect = document.getElementById('currencySelect');
                    const selectedCurrency = currencySelect.value;
                    if (selectedCurrency) {
                        setCurrency(selectedCurrency);
                    } else {
                        showResult('rateResult', 'Please select a currency first', 'error');
                    }
                }
                
                async function loadCurrentCurrency() {
                    try {
                        const response = await fetch('/currency');
                        const currency = await response.json();
                        currentCurrency = currency;
                        
                        // Update UI
                        document.getElementById('currencySymbol').textContent = currency.symbol;
                        document.getElementById('currencySelect').value = currency.code;
                        
                    } catch (error) {
                        console.error('Error loading current currency:', error);
                    }
                }
                
                async function setCurrency(currencyCode) {
                    try {
                        const response = await fetch('/currency', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                code: currencyCode,
                                symbol: '', // Will be filled from server data
                                name: ''    // Will be filled from server data
                            })
                        });
                        
                        const result = await response.json();
                        if (response.ok) {
                            currentCurrency = result.currency;
                            document.getElementById('currencySymbol').textContent = result.currency.symbol;
                            showResult('rateResult', `✅ Currency changed to ${result.currency.name}`, 'success');
                            loadRates(); // Refresh rates to show with new currency
                        } else {
                            showResult('rateResult', result.detail, 'error');
                        }
                    } catch (error) {
                        showResult('rateResult', 'Error setting currency: ' + error.message, 'error');
                    }
                }
                
                // Category Management Functions - Categories come from rate configuration
                async function loadCategories() {
                    try {
                        const response = await fetch('/categories');
                        const categories = await response.json();
                        
                        console.log('Loading categories from rates:', categories); // Debug log
                        
                        const select = document.getElementById('categorySelect');
                        // Store current selection
                        const currentValue = select.value;
                        
                        // Clear existing options except the first one
                        select.innerHTML = '<option value="">Select a category...</option>';
                        
                        // Add categories
                        categories.forEach(category => {
                            const option = document.createElement('option');
                            option.value = category;
                            option.textContent = category;
                            select.appendChild(option);
                        });
                        
                        // Add "Other" option if there are existing categories
                        if (categories.length > 0) {
                            const option = document.createElement('option');
                            option.value = 'OTHER';
                            option.textContent = '--- Other ---';
                            select.appendChild(option);
                        }
                        
                        // Restore selection if it still exists
                        if (currentValue && categories.includes(currentValue)) {
                            select.value = currentValue;
                        }
                    } catch (error) {
                        console.error('Error loading categories:', error);
                    }
                }
                
                function showNewCategoryInput() {
                    document.getElementById('newCategoryInput').style.display = 'block';
                    document.getElementById('newCategoryName').focus();
                }
                
                function cancelNewCategory() {
                    document.getElementById('newCategoryInput').style.display = 'none';
                    document.getElementById('newCategoryName').value = '';
                    document.getElementById('categorySelect').value = '';
                }
                
                async function addNewCategory() {
                    const newCategoryName = document.getElementById('newCategoryName').value.trim();
                    
                    if (!newCategoryName) {
                        alert('Please enter a category name');
                        return;
                    }
                    
                    // Check if category already exists in rates
                    const rates = await fetch('/rates').then(r => r.json());
                    if (rates[newCategoryName]) {
                        alert('This category already exists in your rate configuration');
                        return;
                    }
                    
                    // Add to dropdown temporarily
                    const select = document.getElementById('categorySelect');
                    const option = document.createElement('option');
                    option.value = newCategoryName;
                    option.textContent = newCategoryName + ' (No rate set)';
                    option.style.color = '#ff6b6b'; // Red color to indicate missing rate
                    
                    // Insert before "Other" option if it exists
                    const otherOption = Array.from(select.options).find(opt => opt.value === 'OTHER');
                    if (otherOption) {
                        select.insertBefore(option, otherOption);
                    } else {
                        select.appendChild(option);
                    }
                    
                    // Select the new category
                    select.value = newCategoryName;
                    
                    // Hide the new category input
                    document.getElementById('newCategoryInput').style.display = 'none';
                    document.getElementById('newCategoryName').value = '';
                    
                    showResult('taskResult', `⚠️ Category "${newCategoryName}" added. Please set a rate for this category in the Rate Configuration section.`, 'warning');
                }
                
                // Handle category dropdown change
                function onCategoryChange() {
                    const select = document.getElementById('categorySelect');
                    if (select.value === 'OTHER') {
                        showNewCategoryInput();
                        select.value = '';
                    }
                }
                
                async function createTask() {
                    const name = document.getElementById('taskName').value.trim();
                    const description = document.getElementById('taskDescription').value.trim();
                    const categorySelect = document.getElementById('categorySelect');
                    const parentHeading = categorySelect.value.trim();
                    
                    if (!name) {
                        showResult('taskResult', 'Please enter a task name', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/tasks', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                name: name,
                                description: description,
                                parent_heading: parentHeading
                            })
                        });
                        
                        const result = await response.json();
                        if (response.ok) {
                            showResult('taskResult', result.message, 'success');
                            // Clear form
                            document.getElementById('taskName').value = '';
                            document.getElementById('taskDescription').value = '';
                            document.getElementById('categorySelect').value = '';
                            loadTasks();
                            // Add a small delay to ensure data is saved before reloading categories
                            setTimeout(() => {
                                loadCategories(); // Refresh categories in case this was a new one
                            }, 100);
                        } else {
                            showResult('taskResult', result.detail, 'error');
                        }
                    } catch (error) {
                        showResult('taskResult', 'Error creating task: ' + error.message, 'error');
                    }
                }
                
                async function loadTasks() {
                    try {
                        const response = await fetch('/tasks');
                        const data = await response.json();
                        tasksData = data;
                        
                        // Update stats
                        const totalTasks = Object.keys(data.tasks).length;
                        const activeTasks = Object.values(data.tasks).filter(t => !t.exported).length;
                        const totalHours = Object.values(data.tasks).reduce((sum, t) => sum + (t.total_hours || 0), 0);
                        
                        document.getElementById('totalTasks').textContent = totalTasks;
                        document.getElementById('activeTasks').textContent = activeTasks;
                        document.getElementById('totalHours').textContent = totalHours.toFixed(1);
                        
                        // Update task selector
                        const taskSelect = document.getElementById('timeTaskId');
                        taskSelect.innerHTML = '<option value="">Select a task...</option>';
                        
                        if (totalTasks === 0) {
                            document.getElementById('tasksList').innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-state-icon">📝</div>
                                    <div class="empty-state-text">No tasks yet. Create your first task above!</div>
                                </div>
                            `;
                            return;
                        }
                        
                        let tasksHtml = '<table><tr><th>ID</th><th>Name</th><th>Category</th><th>Hours</th><th>Status</th></tr>';
                        
                        for (const [id, task] of Object.entries(data.tasks)) {
                            taskSelect.innerHTML += `<option value="${id}">${task.name} (${task.total_hours}h)</option>`;
                            const status = task.exported ? 'Exported' : 'Active';
                            const statusClass = task.exported ? 'status-exported' : 'status-active';
                            tasksHtml += `
                                <tr>
                                    <td>${id}</td>
                                    <td>${task.name}</td>
                                    <td>${task.parent_heading || 'General'}</td>
                                    <td>${task.total_hours}</td>
                                    <td><span class="${statusClass}">${status}</span></td>
                                </tr>
                            `;
                        }
                        
                        tasksHtml += '</table>';
                        document.getElementById('tasksList').innerHTML = tasksHtml;
                    } catch (error) {
                        showResult('taskResult', 'Error loading tasks: ' + error.message, 'error');
                    }
                }
                
                async function addTimeEntry() {
                    const taskId = document.getElementById('timeTaskId').value;
                    const hours = parseFloat(document.getElementById('timeHours').value);
                    const date = document.getElementById('timeDate').value;
                    const description = document.getElementById('timeDescription').value.trim();
                    
                    if (!taskId || !hours || !date) {
                        showResult('timeResult', 'Please fill in task, hours, and date', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch(`/tasks/${taskId}/time`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                task_id: taskId,
                                hours: hours,
                                date: date,
                                description: description
                            })
                        });
                        
                        const result = await response.json();
                        if (response.ok) {
                            showResult('timeResult', `✅ Time entry added! Total hours: ${result.total_hours}`, 'success');
                            document.getElementById('timeHours').value = '';
                            document.getElementById('timeDescription').value = '';
                            loadTasks();
                        } else {
                            showResult('timeResult', result.detail, 'error');
                        }
                    } catch (error) {
                        showResult('timeResult', 'Error adding time entry: ' + error.message, 'error');
                    }
                }
                
                async function setRate() {
                    const taskType = document.getElementById('rateTaskType').value.trim();
                    const dayRate = parseFloat(document.getElementById('dayRate').value);
                    
                    if (!taskType || !dayRate) {
                        showResult('rateResult', 'Please enter both task type and day rate', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/rates', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                task_type: taskType,
                                day_rate: dayRate
                            })
                        });
                        
                        const result = await response.json();
                        if (response.ok) {
                            const formattedHourly = formatCurrencyJS(result.hourly_rate, result.currency);
                            showResult('rateResult', `✅ ${result.message}! Hourly rate: ${formattedHourly}`, 'success');
                            document.getElementById('rateTaskType').value = '';
                            document.getElementById('dayRate').value = '';
                            loadRates();
                            loadCategories(); // Refresh categories since we added a new rate
                        } else {
                            showResult('rateResult', result.detail, 'error');
                        }
                    } catch (error) {
                        showResult('rateResult', 'Error setting rate: ' + error.message, 'error');
                    }
                }
                
                function formatCurrencyJS(amount, currency) {
                    const symbol = currency.symbol;
                    const code = currency.code;
                    
                    // Handle different currency formatting styles
                    if (['EUR', 'GBP', 'CHF'].includes(code)) {
                        // European style: amount symbol
                        return `${amount.toFixed(2)} ${symbol}`;
                    } else if (['JPY', 'KRW', 'VND'].includes(code)) {
                        // No decimal places for some currencies
                        return `${symbol}${Math.round(amount)}`;
                    } else {
                        // Default: symbol amount
                        return `${symbol}${amount.toFixed(2)}`;
                    }
                }
                
                async function loadRates() {
                    try {
                        const response = await fetch('/rates');
                        const rates = await response.json();
                        
                        if (Object.keys(rates).length === 0) {
                            document.getElementById('ratesList').innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-state-icon">💰</div>
                                    <div class="empty-state-text">No rates configured yet.</div>
                                </div>
                            `;
                            return;
                        }
                        
                        let ratesHtml = '<h4>📊 Current Rates:</h4>';
                        
                        for (const [taskType, dayRate] of Object.entries(rates)) {
                            const hourlyRate = dayRate / 8;
                            const formattedDay = formatCurrencyJS(dayRate, currentCurrency);
                            const formattedHourly = formatCurrencyJS(hourlyRate, currentCurrency);
                            
                            ratesHtml += `
                                <div class="rate-item">
                                    <div class="rate-info">
                                        <div class="rate-type">${taskType}</div>
                                        <div class="rate-values">Day: ${formattedDay} • Hourly: ${formattedHourly}</div>
                                    </div>
                                    <div class="rate-actions">
                                        <button class="btn btn-small btn-warning" onclick="editRate('${taskType}', ${dayRate})">
                                            ✏️ Edit
                                        </button>
                                        <button class="btn btn-small btn-danger" onclick="deleteRate('${taskType}')">
                                            🗑️ Delete
                                        </button>
                                    </div>
                                </div>
                            `;
                        }
                        
                        document.getElementById('ratesList').innerHTML = ratesHtml;
                    } catch (error) {
                        showResult('rateResult', 'Error loading rates: ' + error.message, 'error');
                    }
                }
                
                function editRate(taskType, currentRate) {
                    document.getElementById('rateTaskType').value = taskType;
                    document.getElementById('dayRate').value = currentRate;
                    document.getElementById('rateTaskType').focus();
                }
                
                async function deleteRate(taskType) {
                    if (!confirm(`Are you sure you want to delete the rate for "${taskType}"?`)) {
                        return;
                    }
                    
                    try {
                        const response = await fetch(`/rates/${encodeURIComponent(taskType)}`, {
                            method: 'DELETE'
                        });
                        
                        const result = await response.json();
                        if (response.ok) {
                            showResult('rateResult', `✅ ${result.message}`, 'success');
                            loadRates();
                            loadCategories(); // Refresh categories since we deleted a rate
                        } else {
                            showResult('rateResult', result.detail, 'error');
                        }
                    } catch (error) {
                        showResult('rateResult', 'Error deleting rate: ' + error.message, 'error');
                    }
                }
                
                async function previewInvoice() {
                    try {
                        const response = await fetch('/invoice/preview');
                        const result = await response.json();
                        
                        if (result.invoice.length === 0) {
                            document.getElementById('invoicePreview').innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-state-icon">📄</div>
                                    <div class="empty-state-text">${result.message}</div>
                                </div>
                            `;
                            showResult('invoiceResult', result.message, 'error');
                            return;
                        }
                        
                        let invoiceHtml = '<h4>👁️ Invoice Preview:</h4><table class="invoice-table">';
                        
                        // Header
                        const firstRow = result.invoice[0];
                        invoiceHtml += '<tr>';
                        for (const key of Object.keys(firstRow)) {
                            invoiceHtml += `<th>${key}</th>`;
                        }
                        invoiceHtml += '</tr>';
                        
                        // Data rows
                        result.invoice.forEach(row => {
                            const isTotal = row.Task === 'TOTAL';
                            invoiceHtml += `<tr${isTotal ? ' class="total-row"' : ''}>`;
                            for (const value of Object.values(row)) {
                                invoiceHtml += `<td>${value}</td>`;
                            }
                            invoiceHtml += '</tr>';
                        });
                        
                        invoiceHtml += '</table>';
                        document.getElementById('invoicePreview').innerHTML = invoiceHtml;
                        showResult('invoiceResult', '✅ Invoice preview generated', 'success');
                    } catch (error) {
                        showResult('invoiceResult', 'Error generating invoice preview: ' + error.message, 'error');
                    }
                }
                
                async function generateInvoice() {
                    if (!confirm('This will mark tasks as exported and they won\\'t appear in future invoices. Continue?')) {
                        return;
                    }
                    
                    try {
                        const response = await fetch('/invoice/generate', {method: 'POST'});
                        const result = await response.json();
                        
                        if (result.invoice.length === 0) {
                            document.getElementById('invoicePreview').innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-state-icon">📄</div>
                                    <div class="empty-state-text">${result.message}</div>
                                </div>
                            `;
                            showResult('invoiceResult', result.message, 'error');
                            return;
                        }
                        
                        let invoiceHtml = '<h4>📄 Generated Invoice (Exported):</h4><table class="invoice-table">';
                        
                        // Header
                        const firstRow = result.invoice[0];
                        invoiceHtml += '<tr>';
                        for (const key of Object.keys(firstRow)) {
                            invoiceHtml += `<th>${key}</th>`;
                        }
                        invoiceHtml += '</tr>';
                        
                        // Data rows
                        result.invoice.forEach(row => {
                            const isTotal = row.Task === 'TOTAL';
                            invoiceHtml += `<tr${isTotal ? ' class="total-row"' : ''}>`;
                            for (const value of Object.values(row)) {
                                invoiceHtml += `<td>${value}</td>`;
                            }
                            invoiceHtml += '</tr>';
                        });
                        
                        invoiceHtml += '</table>';
                        document.getElementById('invoicePreview').innerHTML = invoiceHtml;
                        showResult('invoiceResult', `✅ ${result.message}`, 'success');
                        loadTasks(); // Refresh to show exported status
                    } catch (error) {
                        showResult('invoiceResult', 'Error generating invoice: ' + error.message, 'error');
                    }
                }
                
                async function checkPlannerConfig() {
                    try {
                        const response = await fetch('/planner/config');
                        const config = await response.json();
                        
                        let message = '⚙️ Configuration Status:<br>';
                        message += `Tenant ID: ${config.tenant_id_set ? '✅ Set' : '❌ Not Set'}<br>`;
                        message += `Client ID: ${config.client_id_set ? '✅ Set' : '❌ Not Set'}<br>`;
                        message += `Client Secret: ${config.client_secret_set ? '✅ Set' : '❌ Not Set'}<br>`;
                        message += `Fully Configured: ${config.fully_configured ? '✅ Yes' : '❌ No'}`;
                        
                        showResult('plannerResult', message, config.fully_configured ? 'success' : 'error');
                    } catch (error) {
                        showResult('plannerResult', 'Error checking config: ' + error.message, 'error');
                    }
                }
                
                async function setupPlanner() {
                    try {
                        const response = await fetch('/planner/setup', {method: 'POST'});
                        const result = await response.json();
                        
                        let message = `✅ ${result.message}<br><br>📋 Setup Instructions:<br>`;
                        result.instructions.forEach((instruction, index) => {
                            message += `${index + 1}. ${instruction}<br>`;
                        });
                        
                        showResult('plannerResult', message, 'success');
                    } catch (error) {
                        showResult('plannerResult', 'Error setting up planner: ' + error.message, 'error');
                    }
                }
                
                async function syncPlanner() {
                    showResult('plannerResult', '🔄 Syncing with Microsoft Planner...', 'success');
                    
                    try {
                        const response = await fetch('/planner/sync', {method: 'POST'});
                        const result = await response.json();
                        
                        if (response.ok) {
                            showResult('plannerResult', `✅ ${result.message}`, 'success');
                            if (result.new_tasks > 0) {
                                loadTasks();
                            }
                        } else {
                            showResult('plannerResult', `❌ ${result.detail}`, 'error');
                        }
                    } catch (error) {
                        showResult('plannerResult', 'Error syncing with planner: ' + error.message, 'error');
                    }
                }
                
                async function showDataLocation() {
                    try {
                        const response = await fetch('/system/data-location');
                        const result = await response.json();
                        
                        let message = `📁 Data Storage Location:<br><strong>${result.data_directory}</strong><br><br>`;
                        message += `📄 Your files:<br>`;
                        message += `• Tasks: ${result.tasks_file}<br>`;
                        message += `• Rates: ${result.rates_file}<br>`;
                        message += `• Exported Tasks: ${result.exported_file}<br>`;
                        
                        showResult('controlResult', message, 'success');
                    } catch (error) {
                        showResult('controlResult', 'Error getting data location: ' + error.message, 'error');
                    }
                }
                
                async function shutdownApp() {
                    if (!confirm('Are you sure you want to shutdown ClockIt? All data will be saved automatically.')) {
                        return;
                    }
                    
                    try {
                        showResult('controlResult', '🛑 Shutting down ClockIt...', 'success');
                        
                        // Give user feedback before shutdown
                        setTimeout(() => {
                            document.body.innerHTML = `
                                <div style="
                                    display: flex; 
                                    justify-content: center; 
                                    align-items: center; 
                                    height: 100vh; 
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    text-align: center;
                                    font-family: 'Segoe UI', sans-serif;
                                ">
                                    <div>
                                        <h1 style="font-size: 3em; margin-bottom: 20px;">👋</h1>
                                        <h2>ClockIt has been shut down</h2>
                                        <p style="margin-top: 20px; opacity: 0.8;">All your data has been saved automatically</p>
                                        <p style="margin-top: 10px; opacity: 0.8;">You can safely close this browser tab</p>
                                    </div>
                                </div>
                            `;
                        }, 1000);
                        
                        // Send shutdown request
                        await fetch('/system/shutdown', {method: 'POST'});
                        
                    } catch (error) {
                        // Expected - server will close before responding
                        console.log('Shutdown initiated');
                    }
                }
                
                function showResult(elementId, message, type) {
                    const element = document.getElementById(elementId);
                    let alertClass;
                    if (type === 'success') {
                        alertClass = 'alert-success';
                    } else if (type === 'warning') {
                        alertClass = 'alert-warning';
                    } else {
                        alertClass = 'alert-error';
                    }
                    element.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
                    
                    // Auto-hide success and warning messages after 5 seconds
                    if (type === 'success' || type === 'warning') {
                        setTimeout(() => {
                            element.innerHTML = '';
                        }, 7000); // Longer timeout for warnings
                    }
                }
            </script>
        </body>
    </html>
    """)

@app.get("/planner/config")
async def get_planner_config():
    """Get Microsoft Planner configuration status"""
    config = PlannerConfig.load_config()
    
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
async def get_tasks():
    """Get all tasks"""
    tasks_data = load_tasks_data()
    return tasks_data

@app.post("/tasks")
async def create_task(task: TaskCreate):
    """Create a new task"""
    tasks_data = load_tasks_data()
    task_id = str(len(tasks_data["tasks"]) + 1)
    
    new_task = {
        "id": task_id,
        "name": task.name,
        "description": task.description,
        "parent_heading": task.parent_heading,
        "time_entries": [],
        "total_hours": 0,
        "created_at": datetime.now().isoformat(),
        "exported": False
    }
    
    tasks_data["tasks"][task_id] = new_task
    save_tasks_data(tasks_data)
    
    return {"message": "Task created", "task": new_task}

@app.post("/tasks/{task_id}/time")
async def add_time_entry(task_id: str, time_entry: TimeEntry):
    """Add time entry to existing task"""
    tasks_data = load_tasks_data()
    
    if task_id not in tasks_data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Validate time_entry.task_id matches task_id
    if time_entry.task_id != task_id:
        raise HTTPException(status_code=400, detail="Task ID mismatch")
    
    new_entry = {
        "hours": time_entry.hours,
        "date": time_entry.date,
        "description": time_entry.description,
        "timestamp": datetime.now().isoformat()
    }
    
    tasks_data["tasks"][task_id]["time_entries"].append(new_entry)
    
    # Recalculate total hours
    total_hours = sum(entry["hours"] for entry in tasks_data["tasks"][task_id]["time_entries"])
    tasks_data["tasks"][task_id]["total_hours"] = total_hours
    
    save_tasks_data(tasks_data)
    
    return {"message": "Time entry added", "total_hours": total_hours}

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
async def get_currency():
    """Get current currency configuration"""
    return get_current_currency()

@app.get("/currency/available")
async def get_available_currencies():
    """Get list of all available currencies"""
    return CURRENCIES

@app.post("/currency")
async def set_currency(currency_config: CurrencyConfig):
    """Set the application currency"""
    if currency_config.code not in CURRENCIES:
        raise HTTPException(status_code=400, detail="Unsupported currency code")
    
    # Update with official currency data
    currency_data = CURRENCIES[currency_config.code]
    config = {
        "code": currency_config.code,
        "symbol": currency_data["symbol"],
        "name": currency_data["name"]
    }
    
    save_currency_config(config)
    
    return {
        "message": f"Currency set to {config['name']}",
        "currency": config
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
    uvicorn.run(app, host="0.0.0.0", port=8001)
