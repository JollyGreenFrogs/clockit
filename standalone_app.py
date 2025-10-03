#!/usr/bin/env python3
"""
ClockIt - Standalone Time Tracker Application
Single-file version for testing and development
"""

import os
import json
import signal
import threading
import webbrowser
from datetime import datetime, date
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Initialize data directory
DATA_DIR = Path("./clockit_data")
DATA_DIR.mkdir(exist_ok=True)

# Configuration files
TASKS_FILE = DATA_DIR / "tasks.json"
RATES_FILE = DATA_DIR / "rates.json"
CURRENCY_CONFIG_FILE = DATA_DIR / "currency_config.json"

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
    "BBD": {"symbol": "$", "name": "Barbadian Dollar"},
    "BDT": {"symbol": "৳", "name": "Bangladeshi Taka"},
    "BGN": {"symbol": "лв", "name": "Bulgarian Lev"},
    "BHD": {"symbol": "د.ب", "name": "Bahraini Dinar"},
    "BIF": {"symbol": "FBu", "name": "Burundian Franc"},
    "BMD": {"symbol": "$", "name": "Bermudian Dollar"},
    "BND": {"symbol": "$", "name": "Brunei Dollar"},
    "BOB": {"symbol": "$b", "name": "Bolivian Boliviano"},
    "BRL": {"symbol": "R$", "name": "Brazilian Real"},
    "BSD": {"symbol": "$", "name": "Bahamian Dollar"},
    "BTN": {"symbol": "Nu.", "name": "Bhutanese Ngultrum"},
    "BWP": {"symbol": "P", "name": "Botswanan Pula"},
    "BYN": {"symbol": "Br", "name": "Belarusian Ruble"},
    "BZD": {"symbol": "BZ$", "name": "Belize Dollar"},
    "CAD": {"symbol": "C$", "name": "Canadian Dollar"},
    "CDF": {"symbol": "CDF", "name": "Congolese Franc"},
    "CHF": {"symbol": "CHF", "name": "Swiss Franc"},
    "CLP": {"symbol": "$", "name": "Chilean Peso"},
    "CNY": {"symbol": "¥", "name": "Chinese Yuan"},
    "COP": {"symbol": "$", "name": "Colombian Peso"},
    "CRC": {"symbol": "₡", "name": "Costa Rican Colón"},
    "CUC": {"symbol": "$", "name": "Cuban Convertible Peso"},
    "CUP": {"symbol": "₱", "name": "Cuban Peso"},
    "CVE": {"symbol": "$", "name": "Cape Verdean Escudo"},
    "CZK": {"symbol": "Kč", "name": "Czech Republic Koruna"},
    "DJF": {"symbol": "Fdj", "name": "Djiboutian Franc"},
    "DKK": {"symbol": "kr", "name": "Danish Krone"},
    "DOP": {"symbol": "RD$", "name": "Dominican Peso"},
    "DZD": {"symbol": "دج", "name": "Algerian Dinar"},
    "EGP": {"symbol": "£", "name": "Egyptian Pound"},
    "ERN": {"symbol": "Nfk", "name": "Eritrean Nakfa"},
    "ETB": {"symbol": "Br", "name": "Ethiopian Birr"},
    "FJD": {"symbol": "$", "name": "Fijian Dollar"},
    "FKP": {"symbol": "£", "name": "Falkland Islands Pound"},
    "GEL": {"symbol": "₾", "name": "Georgian Lari"},
    "GGP": {"symbol": "£", "name": "Guernsey Pound"},
    "GHS": {"symbol": "¢", "name": "Ghanaian Cedi"},
    "GIP": {"symbol": "£", "name": "Gibraltar Pound"},
    "GMD": {"symbol": "D", "name": "Gambian Dalasi"},
    "GNF": {"symbol": "FG", "name": "Guinean Franc"},
    "GTQ": {"symbol": "Q", "name": "Guatemalan Quetzal"},
    "GYD": {"symbol": "$", "name": "Guyanaese Dollar"},
    "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar"},
    "HNL": {"symbol": "L", "name": "Honduran Lempira"},
    "HRK": {"symbol": "kn", "name": "Croatian Kuna"},
    "HTG": {"symbol": "G", "name": "Haitian Gourde"},
    "HUF": {"symbol": "Ft", "name": "Hungarian Forint"},
    "IDR": {"symbol": "Rp", "name": "Indonesian Rupiah"},
    "ILS": {"symbol": "₪", "name": "Israeli New Sheqel"},
    "IMP": {"symbol": "£", "name": "Manx pound"},
    "INR": {"symbol": "₹", "name": "Indian Rupee"},
    "IQD": {"symbol": "ع.د", "name": "Iraqi Dinar"},
    "IRR": {"symbol": "﷼", "name": "Iranian Rial"},
    "ISK": {"symbol": "kr", "name": "Icelandic Króna"},
    "JEP": {"symbol": "£", "name": "Jersey Pound"},
    "JMD": {"symbol": "J$", "name": "Jamaican Dollar"},
    "JOD": {"symbol": "JD", "name": "Jordanian Dinar"},
    "JPY": {"symbol": "¥", "name": "Japanese Yen"},
    "KES": {"symbol": "KSh", "name": "Kenyan Shilling"},
    "KGS": {"symbol": "лв", "name": "Kyrgystani Som"},
    "KHR": {"symbol": "៛", "name": "Cambodian Riel"},
    "KMF": {"symbol": "CF", "name": "Comorian Franc"},
    "KPW": {"symbol": "₩", "name": "North Korean Won"},
    "KRW": {"symbol": "₩", "name": "South Korean Won"},
    "KWD": {"symbol": "د.ك", "name": "Kuwaiti Dinar"},
    "KYD": {"symbol": "$", "name": "Cayman Islands Dollar"},
    "KZT": {"symbol": "лв", "name": "Kazakhstani Tenge"},
    "LAK": {"symbol": "₭", "name": "Laotian Kip"},
    "LBP": {"symbol": "£", "name": "Lebanese Pound"},
    "LKR": {"symbol": "₨", "name": "Sri Lankan Rupee"},
    "LRD": {"symbol": "$", "name": "Liberian Dollar"},
    "LSL": {"symbol": "M", "name": "Lesotho Loti"},
    "LYD": {"symbol": "ل.د", "name": "Libyan Dinar"},
    "MAD": {"symbol": "د.م.", "name": "Moroccan Dirham"},
    "MDL": {"symbol": "lei", "name": "Moldovan Leu"},
    "MGA": {"symbol": "Ar", "name": "Malagasy Ariary"},
    "MKD": {"symbol": "ден", "name": "Macedonian Denar"},
    "MMK": {"symbol": "K", "name": "Myanma Kyat"},
    "MNT": {"symbol": "₮", "name": "Mongolian Tugrik"},
    "MOP": {"symbol": "MOP$", "name": "Macanese Pataca"},
    "MRO": {"symbol": "UM", "name": "Mauritanian Ouguiya (pre-2018)"},
    "MRU": {"symbol": "UM", "name": "Mauritanian Ouguiya"},
    "MUR": {"symbol": "₨", "name": "Mauritian Rupee"},
    "MVR": {"symbol": "Rf", "name": "Maldivian Rufiyaa"},
    "MWK": {"symbol": "MK", "name": "Malawian Kwacha"},
    "MXN": {"symbol": "$", "name": "Mexican Peso"},
    "MYR": {"symbol": "RM", "name": "Malaysian Ringgit"},
    "MZN": {"symbol": "MT", "name": "Mozambican Metical"},
    "NAD": {"symbol": "$", "name": "Namibian Dollar"},
    "NGN": {"symbol": "₦", "name": "Nigerian Naira"},
    "NIO": {"symbol": "C$", "name": "Nicaraguan Córdoba"},
    "NOK": {"symbol": "kr", "name": "Norwegian Krone"},
    "NPR": {"symbol": "₨", "name": "Nepalese Rupee"},
    "NZD": {"symbol": "NZ$", "name": "New Zealand Dollar"},
    "OMR": {"symbol": "﷼", "name": "Omani Rial"},
    "PAB": {"symbol": "B/.", "name": "Panamanian Balboa"},
    "PEN": {"symbol": "S/.", "name": "Peruvian Nuevo Sol"},
    "PGK": {"symbol": "K", "name": "Papua New Guinean Kina"},
    "PHP": {"symbol": "₱", "name": "Philippine Peso"},
    "PKR": {"symbol": "₨", "name": "Pakistani Rupee"},
    "PLN": {"symbol": "zł", "name": "Polish Zloty"},
    "PYG": {"symbol": "Gs", "name": "Paraguayan Guarani"},
    "QAR": {"symbol": "﷼", "name": "Qatari Rial"},
    "RON": {"symbol": "lei", "name": "Romanian Leu"},
    "RSD": {"symbol": "Дин.", "name": "Serbian Dinar"},
    "RUB": {"symbol": "₽", "name": "Russian Ruble"},
    "RWF": {"symbol": "R₣", "name": "Rwandan Franc"},
    "SAR": {"symbol": "﷼", "name": "Saudi Riyal"},
    "SBD": {"symbol": "$", "name": "Solomon Islands Dollar"},
    "SCR": {"symbol": "₨", "name": "Seychellois Rupee"},
    "SDG": {"symbol": "ج.س.", "name": "Sudanese Pound"},
    "SEK": {"symbol": "kr", "name": "Swedish Krona"},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar"},
    "SHP": {"symbol": "£", "name": "Saint Helena Pound"},
    "SLE": {"symbol": "Le", "name": "Sierra Leonean Leone"},
    "SLL": {"symbol": "Le", "name": "Sierra Leonean Leone (Old)"},
    "SOS": {"symbol": "S", "name": "Somali Shilling"},
    "SRD": {"symbol": "$", "name": "Surinamese Dollar"},
    "STN": {"symbol": "Db", "name": "São Tomé and Príncipe Dobra"},
    "SZL": {"symbol": "L", "name": "Swazi Lilangeni"},
    "THB": {"symbol": "฿", "name": "Thai Baht"},
    "TJS": {"symbol": "SM", "name": "Tajikistani Somoni"},
    "TMT": {"symbol": "T", "name": "Turkmenistani Manat"},
    "TND": {"symbol": "د.ت", "name": "Tunisian Dinar"},
    "TOP": {"symbol": "T$", "name": "Tongan Paʻanga"},
    "TRY": {"symbol": "₺", "name": "Turkish Lira"},
    "TTD": {"symbol": "TT$", "name": "Trinidad and Tobago Dollar"},
    "TVD": {"symbol": "$", "name": "Tuvaluan Dollar"},
    "TWD": {"symbol": "NT$", "name": "New Taiwan Dollar"},
    "TZS": {"symbol": "TSh", "name": "Tanzanian Shilling"},
    "UAH": {"symbol": "₴", "name": "Ukrainian Hryvnia"},
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
    "XPF": {"symbol": "₣", "name": "CFP Franc"},
    "YER": {"symbol": "﷼", "name": "Yemeni Rial"},
    "ZAR": {"symbol": "R", "name": "South African Rand"},
    "ZMW": {"symbol": "ZK", "name": "Zambian Kwacha"},
    "ZWL": {"symbol": "Z$", "name": "Zimbabwean Dollar"},
}

app = FastAPI()

# Pydantic models
class TaskCreate(BaseModel):
    name: str
    description: str = ""
    category: str

class TimeEntry(BaseModel):
    task_id: str
    hours: float
    date: str = None

class RateConfig(BaseModel):
    task_type: str
    day_rate: float

class CurrencyConfig(BaseModel):
    code: str
    symbol: str = ""

# Data management functions
def load_tasks_data():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading tasks: {e}")
    return {"tasks": {}, "time_entries": []}

def save_tasks_data(data):
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving tasks: {e}")

def load_rates_config():
    if os.path.exists(RATES_FILE):
        try:
            with open(RATES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rates: {e}")
    return {}

def save_rates_config(rates):
    try:
        with open(RATES_FILE, 'w') as f:
            json.dump(rates, f, indent=2)
    except Exception as e:
        print(f"Error saving rates: {e}")

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

def save_currency_config(currency_config):
    try:
        with open(CURRENCY_CONFIG_FILE, 'w') as f:
            json.dump(currency_config, f, indent=2)
    except Exception as e:
        print(f"Error saving currency config: {e}")

def get_current_currency():
    config = load_currency_config()
    return {
        "code": config["code"],
        "symbol": config["symbol"],
        "name": config["name"]
    }

# API Routes
@app.get("/tasks")
async def get_tasks():
    return load_tasks_data()

@app.post("/tasks")
async def create_task(task: TaskCreate):
    data = load_tasks_data()
    task_id = f"task_{len(data['tasks']) + 1}"
    
    data["tasks"][task_id] = {
        "id": task_id,
        "name": task.name,
        "description": task.description,
        "category": task.category,
        "created_at": datetime.now().isoformat(),
        "total_hours": 0,
        "exported": False
    }
    
    save_tasks_data(data)
    return {"message": "Task created successfully", "task_id": task_id}

@app.post("/time")
async def add_time_entry(time_entry: TimeEntry):
    data = load_tasks_data()
    
    if time_entry.task_id not in data["tasks"]:
        raise HTTPException(status_code=404, detail="Task not found")
    
    entry = {
        "id": f"time_{len(data['time_entries']) + 1}",
        "task_id": time_entry.task_id,
        "hours": time_entry.hours,
        "date": time_entry.date or date.today().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    
    data["time_entries"].append(entry)
    
    # Update task total hours
    task_hours = sum(e["hours"] for e in data["time_entries"] if e["task_id"] == time_entry.task_id)
    data["tasks"][time_entry.task_id]["total_hours"] = task_hours
    
    save_tasks_data(data)
    return {"message": "Time entry added successfully"}

@app.get("/rates")
async def get_rates():
    return load_rates_config()

@app.post("/rates")
async def set_rate(rate: RateConfig):
    rates = load_rates_config()
    rates[rate.task_type] = rate.day_rate
    save_rates_config(rates)
    return {"message": f"Rate set for {rate.task_type}"}

@app.delete("/rates/{task_type}")
async def delete_rate(task_type: str):
    rates = load_rates_config()
    
    if task_type not in rates:
        raise HTTPException(status_code=404, detail="Task type not found")
    
    del rates[task_type]
    save_rates_config(rates)
    
    return {"message": f"Rate deleted for {task_type}"}

@app.get("/currency")
async def get_currency():
    return get_current_currency()

@app.get("/currency/available")
async def get_available_currencies():
    return CURRENCIES

@app.post("/currency")
async def set_currency(currency_config: CurrencyConfig):
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

@app.get("/categories")
async def get_categories():
    # Get categories from both tasks and rates
    tasks_data = load_tasks_data()
    rates = load_rates_config()
    
    # Collect categories from created tasks
    task_categories = set()
    for task in tasks_data.get("tasks", {}).values():
        if task.get("category"):
            task_categories.add(task["category"])
    
    # Collect categories from rates
    rate_categories = set(rates.keys())
    
    # Combine and sort all categories
    all_categories = sorted(list(task_categories | rate_categories))
    return all_categories

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⏰ ClockIt - Professional Time Tracker</title>
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --background-color: #f8fafc;
            --surface-color: #ffffff;
            --text-color: #2d3748;
            --text-light: #718096;
            --border-color: #e2e8f0;
            --success-color: #48bb78;
            --warning-color: #ed8936;
            --error-color: #f56565;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --border-radius: 8px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px 0;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
        }

        .tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            padding: 5px;
            backdrop-filter: blur(10px);
        }

        .tab-button {
            background: transparent;
            border: none;
            padding: 12px 24px;
            margin: 0 2px;
            border-radius: var(--border-radius);
            color: white;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1rem;
        }

        .tab-button:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .tab-button.active {
            background: white;
            color: var(--primary-color);
            box-shadow: var(--shadow);
        }

        .section {
            background: var(--surface-color);
            border-radius: var(--border-radius);
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: var(--shadow-lg);
            display: none;
        }

        .section.active {
            display: block;
        }

        .section h2 {
            color: var(--primary-color);
            margin-bottom: 20px;
            font-size: 1.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 20px;
            border-radius: var(--border-radius);
            text-align: center;
            box-shadow: var(--shadow);
        }

        .stat-card h3 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .stat-card p {
            opacity: 0.9;
            font-weight: 300;
        }

        .form-row {
            display: flex;
            flex-direction: column;
            margin-bottom: 20px;
        }

        .form-row label {
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--text-color);
        }

        .form-row input, .form-row select, .form-row textarea {
            padding: 12px 16px;
            border: 2px solid var(--border-color);
            border-radius: var(--border-radius);
            font-size: 1rem;
            transition: all 0.3s ease;
            background: white;
        }

        .form-row input:focus, .form-row select:focus, .form-row textarea:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-row textarea {
            resize: vertical;
            min-height: 100px;
        }

        .btn-group {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }

        .btn {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: var(--border-radius);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            box-shadow: var(--shadow);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-secondary {
            background: linear-gradient(135deg, var(--text-light), #a0aec0);
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--warning-color), #dd6b20);
        }

        .btn-small {
            padding: 8px 16px;
            font-size: 0.9rem;
        }

        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: var(--border-radius);
            font-weight: 500;
        }

        .result.success {
            background: #f0fff4;
            color: var(--success-color);
            border: 1px solid #9ae6b4;
        }

        .result.error {
            background: #fff5f5;
            color: var(--error-color);
            border: 1px solid #fed7d7;
        }

        .result.warning {
            background: #fffbf0;
            color: var(--warning-color);
            border: 1px solid #fbd38d;
        }

        .task-item, .rate-item {
            background: #f8fafc;
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }

        .task-item:hover, .rate-item:hover {
            box-shadow: var(--shadow);
            transform: translateY(-1px);
        }

        .task-info, .rate-info {
            flex: 1;
        }

        .task-name, .rate-type {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 5px;
        }

        .task-details, .rate-values {
            color: var(--text-light);
            font-size: 0.9rem;
        }

        .task-actions, .rate-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-light);
        }

        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }

        .empty-state-text {
            font-size: 1.2rem;
            font-weight: 500;
        }

        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
            color: var(--text-light);
        }

        .loading::after {
            content: "";
            width: 30px;
            height: 30px;
            border: 3px solid var(--border-color);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 15px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .container {
                padding: 0 15px;
            }

            .header h1 {
                font-size: 2rem;
            }

            .tabs {
                flex-direction: column;
            }

            .tab-button {
                margin: 2px 0;
            }

            .btn-group {
                flex-direction: column;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }

        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ ClockIt</h1>
            <p>Professional Time Tracker & Invoice Generator</p>
        </div>

        <div class="tabs">
            <button class="tab-button active" onclick="showTab('tasks')">📋 Tasks</button>
            <button class="tab-button" onclick="showTab('time')">⏱️ Time Entry</button>
            <button class="tab-button" onclick="showTab('rates')">💰 Rates</button>
            <button class="tab-button" onclick="showTab('reports')">📊 Reports</button>
        </div>

        <!-- Tasks Section -->
        <div id="tasks" class="section active">
            <h2><span>📋</span> Task Management</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3 id="totalTasks">0</h3>
                    <p>Total Tasks</p>
                </div>
                <div class="stat-card">
                    <h3 id="activeTasks">0</h3>
                    <p>Active Tasks</p>
                </div>
                <div class="stat-card">
                    <h3 id="totalHours">0</h3>
                    <p>Total Hours</p>
                </div>
            </div>

            <div class="form-row">
                <label>Task Name:</label>
                <input type="text" id="taskName" placeholder="e.g., Website Development">
            </div>
            <div class="form-row">
                <label>Description:</label>
                <textarea id="taskDescription" placeholder="Brief description of the task..."></textarea>
            </div>
            <div class="form-row">
                <label>Category:</label>
                <select id="categorySelect" onchange="onCategoryChange()">
                    <option value="">Select a category...</option>
                    <option value="OTHER">➕ Add New Category</option>
                </select>
                <div id="newCategoryInput" class="hidden">
                    <input type="text" id="newCategoryName" placeholder="Enter new category name...">
                    <button class="btn btn-small" onclick="addNewCategory()">Add Category</button>
                </div>
            </div>

            <div class="btn-group">
                <button class="btn" onclick="createTask()">
                    <span>➕</span> Create Task
                </button>
                <button class="btn btn-secondary" onclick="loadTasks()">
                    <span>🔄</span> Refresh Tasks
                </button>
            </div>

            <div id="taskResult"></div>
            <div id="tasksList"></div>
        </div>

        <!-- Time Entry Section -->
        <div id="time" class="section">
            <h2><span>⏱️</span> Time Entry</h2>
            
            <div class="form-row">
                <label>Select Task:</label>
                <select id="timeTaskId">
                    <option value="">Select a task...</option>
                </select>
            </div>
            <div class="form-row">
                <label>Hours Worked:</label>
                <input type="number" id="timeHours" step="0.25" min="0" placeholder="e.g., 2.5">
            </div>
            <div class="form-row">
                <label>Date:</label>
                <input type="date" id="timeDate">
            </div>

            <div class="btn-group">
                <button class="btn" onclick="addTimeEntry()">
                    <span>⏱️</span> Add Time
                </button>
                <button class="btn btn-secondary" onclick="loadTasks()">
                    <span>🔄</span> Refresh Tasks
                </button>
            </div>

            <div id="timeResult"></div>
        </div>

        <!-- Rates Section -->
        <div id="rates" class="section">
            <h2><span>💰</span> Rate Configuration</h2>
            
            <div class="form-row">
                <label>Task Type/Category:</label>
                <select id="rateTaskType">
                    <option value="">Select a category...</option>
                </select>
            </div>
            <div class="form-row">
                <label>Day Rate:</label>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <span id="currencySymbol" style="font-weight: bold; color: #667eea;">$</span>
                    <input type="number" id="dayRate" step="1" min="0" placeholder="e.g., 400" style="flex: 1;">
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

            <!-- Currency Configuration Section -->
            <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid var(--border-color);">
                <h3 style="color: var(--primary-color); margin-bottom: 20px;">💱 Currency Settings</h3>
                
                <div class="form-row">
                    <label>Currency:</label>
                    <select id="currencySelect">
                        <option value="">Loading currencies...</option>
                    </select>
                </div>

                <div class="btn-group">
                    <button class="btn" onclick="applyCurrency()">
                        <span>💱</span> Apply Currency
                    </button>
                </div>
            </div>
        </div>

        <!-- Reports Section -->
        <div id="reports" class="section">
            <h2><span>📊</span> Reports & Export</h2>
            
            <div class="btn-group">
                <button class="btn" onclick="generateInvoice()">
                    <span>📄</span> Generate Invoice
                </button>
                <button class="btn btn-secondary" onclick="exportData()">
                    <span>📤</span> Export Data
                </button>
            </div>

            <div id="reportResult"></div>
        </div>
    </div>

    <script>
        let tasksData = {};
        let currentCurrency = { code: 'USD', symbol: '$', name: 'US Dollar' };

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            loadCurrentCurrency();
            loadCurrencies();
            loadTasks();
            loadRates();
            loadCategories();
            
            // Set today's date as default
            document.getElementById('timeDate').value = new Date().toISOString().split('T')[0];
        });

        // Tab management
        function showTab(tabName) {
            // Hide all sections
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab-button').forEach(button => {
                button.classList.remove('active');
            });
            
            // Show selected section
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab button
            event.target.classList.add('active');
            
            // Load data for the selected tab
            if (tabName === 'tasks') {
                loadTasks();
                loadCategories();
            } else if (tabName === 'rates') {
                loadRates();
                loadCategories();
            }
        }

        // Task management functions
        async function createTask() {
            const name = document.getElementById('taskName').value.trim();
            const description = document.getElementById('taskDescription').value.trim();
            const category = document.getElementById('categorySelect').value;

            if (!name) {
                showResult('taskResult', 'Please enter a task name', 'error');
                return;
            }

            if (!category) {
                showResult('taskResult', 'Please select a category', 'error');
                return;
            }

            try {
                const response = await fetch('/tasks', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: name,
                        description: description,
                        category: category
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    showResult('taskResult', result.message, 'success');
                    document.getElementById('taskName').value = '';
                    document.getElementById('taskDescription').value = '';
                    document.getElementById('categorySelect').value = '';
                    loadTasks();
                    playSuccessSound();
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
                
                Object.values(data.tasks).forEach(task => {
                    if (!task.exported) {
                        const option = document.createElement('option');
                        option.value = task.id;
                        option.textContent = `${task.name} (${task.category})`;
                        taskSelect.appendChild(option);
                    }
                });
                
                // Display tasks list
                displayTasksList(data.tasks);
                
            } catch (error) {
                console.error('Error loading tasks:', error);
                showResult('taskResult', 'Error loading tasks: ' + error.message, 'error');
            }
        }

        function displayTasksList(tasks) {
            const tasksListDiv = document.getElementById('tasksList');
            
            if (Object.keys(tasks).length === 0) {
                tasksListDiv.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📝</div>
                        <div class="empty-state-text">No tasks created yet.</div>
                    </div>
                `;
                return;
            }
            
            let tasksHtml = '<h4>📋 Your Tasks:</h4>';
            
            for (const [taskId, task] of Object.entries(tasks)) {
                const statusIcon = task.exported ? '✅' : '🔄';
                const statusText = task.exported ? 'Exported' : 'Active';
                
                tasksHtml += `
                    <div class="task-item">
                        <div class="task-info">
                            <div class="task-name">${task.name}</div>
                            <div class="task-details">${task.category} • ${task.total_hours.toFixed(1)} hours • ${statusIcon} ${statusText}</div>
                            ${task.description ? `<div style="margin-top: 5px; color: #666;">${task.description}</div>` : ''}
                        </div>
                    </div>
                `;
            }
            
            tasksListDiv.innerHTML = tasksHtml;
        }

        // Time entry functions
        async function addTimeEntry() {
            const taskId = document.getElementById('timeTaskId').value;
            const hours = parseFloat(document.getElementById('timeHours').value);
            const date = document.getElementById('timeDate').value;

            if (!taskId) {
                showResult('timeResult', 'Please select a task', 'error');
                return;
            }

            if (!hours || hours <= 0) {
                showResult('timeResult', 'Please enter valid hours', 'error');
                return;
            }

            try {
                const response = await fetch('/time', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        task_id: taskId,
                        hours: hours,
                        date: date
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    showResult('timeResult', result.message, 'success');
                    document.getElementById('timeHours').value = '';
                    loadTasks();
                    playSuccessSound();
                } else {
                    showResult('timeResult', result.detail, 'error');
                }
            } catch (error) {
                showResult('timeResult', 'Error adding time entry: ' + error.message, 'error');
            }
        }

        // Rate management functions
        async function setRate() {
            const taskType = document.getElementById('rateTaskType').value;
            const dayRate = parseFloat(document.getElementById('dayRate').value);

            if (!taskType) {
                showResult('rateResult', 'Please select a task type', 'error');
                return;
            }

            if (!dayRate || dayRate <= 0) {
                showResult('rateResult', 'Please enter a valid day rate', 'error');
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
                    showResult('rateResult', result.message, 'success');
                    document.getElementById('dayRate').value = '';
                    loadRates();
                    playSuccessSound();
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
                                    <span>✏️</span> Edit
                                </button>
                                <button class="btn btn-small btn-secondary" onclick="deleteRate('${taskType}')">
                                    <span>🗑️</span> Delete
                                </button>
                            </div>
                        </div>
                    `;
                }
                
                document.getElementById('ratesList').innerHTML = ratesHtml;
                
            } catch (error) {
                console.error('Error loading rates:', error);
                showResult('rateResult', 'Error loading rates: ' + error.message, 'error');
            }
        }

        function editRate(taskType, currentRate) {
            document.getElementById('rateTaskType').value = taskType;
            document.getElementById('dayRate').value = currentRate;
            showResult('rateResult', `⚠️ Editing rate for ${taskType}. Update the rate and click "Set Rate" to save.`, 'warning');
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
                    showResult('rateResult', result.message, 'success');
                    loadRates();
                    playSuccessSound();
                } else {
                    showResult('rateResult', result.detail, 'error');
                }
            } catch (error) {
                showResult('rateResult', 'Error deleting rate: ' + error.message, 'error');
            }
        }

        // Category management functions
        async function loadCategories() {
            try {
                const response = await fetch('/categories');
                const categories = await response.json();
                
                const categorySelect = document.getElementById('categorySelect');
                const rateTaskTypeSelect = document.getElementById('rateTaskType');
                
                // Clear existing options except the first one and "OTHER"
                categorySelect.innerHTML = '<option value="">Select a category...</option>';
                rateTaskTypeSelect.innerHTML = '<option value="">Select a category...</option>';
                
                categories.forEach(category => {
                    const option1 = document.createElement('option');
                    option1.value = category;
                    option1.textContent = category;
                    categorySelect.appendChild(option1);
                    
                    const option2 = document.createElement('option');
                    option2.value = category;
                    option2.textContent = category;
                    rateTaskTypeSelect.appendChild(option2);
                });
                
                // Add "OTHER" option to categorySelect only
                const otherOption = document.createElement('option');
                otherOption.value = 'OTHER';
                otherOption.textContent = '➕ Add New Category';
                categorySelect.appendChild(otherOption);
                
            } catch (error) {
                console.error('Error loading categories:', error);
            }
        }

        function showNewCategoryInput() {
            document.getElementById('newCategoryInput').classList.remove('hidden');
            document.getElementById('newCategoryName').focus();
        }

        function addNewCategory() {
            const newCategoryName = document.getElementById('newCategoryName').value.trim();
            
            if (!newCategoryName) {
                showResult('taskResult', 'Please enter a category name', 'error');
                return;
            }
            
            // Add the new category to the select dropdown
            const select = document.getElementById('categorySelect');
            const option = document.createElement('option');
            option.value = newCategoryName;
            option.textContent = newCategoryName;
            
            // Insert before "OTHER" option
            const otherOption = Array.from(select.options).find(opt => opt.value === 'OTHER');
            if (otherOption) {
                select.insertBefore(option, otherOption);
            } else {
                select.appendChild(option);
            }
            
            // Select the new category
            select.value = newCategoryName;
            
            // Hide the new category input
            document.getElementById('newCategoryInput').classList.add('hidden');
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

        // Currency management functions
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
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    showResult('rateResult', result.message, 'success');
                    currentCurrency = result.currency;
                    document.getElementById('currencySymbol').textContent = result.currency.symbol;
                    loadRates(); // Refresh rates display with new currency
                    playSuccessSound();
                } else {
                    showResult('rateResult', result.detail, 'error');
                }
            } catch (error) {
                showResult('rateResult', 'Error setting currency: ' + error.message, 'error');
            }
        }

        // Reports functions
        async function generateInvoice() {
            showResult('reportResult', 'Invoice generation feature coming soon!', 'warning');
        }

        async function exportData() {
            try {
                const tasksResponse = await fetch('/tasks');
                const ratesResponse = await fetch('/rates');
                const currencyResponse = await fetch('/currency');
                
                const data = {
                    tasks: await tasksResponse.json(),
                    rates: await ratesResponse.json(),
                    currency: await currencyResponse.json(),
                    exported_at: new Date().toISOString()
                };
                
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `clockit-export-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showResult('reportResult', 'Data exported successfully!', 'success');
                playSuccessSound();
            } catch (error) {
                showResult('reportResult', 'Error exporting data: ' + error.message, 'error');
            }
        }

        // Utility functions
        function showResult(elementId, message, type) {
            const element = document.getElementById(elementId);
            element.innerHTML = `<div class="result ${type}">${message}</div>`;
            
            // Auto-hide success and warning messages after 5 seconds
            if (type === 'success' || type === 'warning') {
                setTimeout(() => {
                    element.innerHTML = '';
                }, 7000); // Longer timeout for warnings
            }
        }

        function playSuccessSound() {
            try {
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp3Z1VEwaE2OXBhQ==');
                audio.volume = 0.3;
                audio.play().catch(() => {}); // Ignore errors if audio can't play
            } catch (e) {
                // Audio not supported, ignore
            }
        }
    </script>
</body>
</html>
    """)

if __name__ == "__main__":
    print("🚀 Starting ClockIt Time Tracker (Standalone)...")
    print("📁 Data directory: ./clockit_data")
    print("📍 Server will be available at: http://localhost:8001")
    print("🔴 Press Ctrl+C to stop the application")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8001)