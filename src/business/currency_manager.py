"""
Currency management business logic
"""

import json
from pathlib import Path
from typing import Dict

class CurrencyManager:
    """Handles all currency-related business operations"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.currency_file = data_dir / "currency_config.json"
        self.default_currency = {
            "code": "USD",
            "symbol": "$",
            "name": "US Dollar"
        }
    
    def load_currency_config(self) -> Dict:
        """Load currency configuration from storage"""
        if self.currency_file.exists():
            try:
                with open(self.currency_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading currency config: {e}")
        return self.default_currency.copy()
    
    def save_currency_config(self, currency_config: Dict) -> bool:
        """Save currency configuration to storage"""
        try:
            with open(self.currency_file, 'w') as f:
                json.dump(currency_config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving currency config: {e}")
            return False
    
    def set_currency(self, code: str, symbol: str, name: str) -> bool:
        """Set the application currency"""
        config = {
            "code": code,
            "symbol": symbol,
            "name": name
        }
        return self.save_currency_config(config)
    
    def get_current_currency(self) -> Dict:
        """Get current currency configuration"""
        return self.load_currency_config()
    
    def format_currency(self, amount: float, currency_config: Dict = None) -> str:
        """Format currency amount according to currency rules"""
        if currency_config is None:
            currency_config = self.load_currency_config()
        
        symbol = currency_config["symbol"]
        code = currency_config["code"]
        
        # Handle different currency formatting styles
        if code in ["EUR", "GBP", "CHF"]:
            # European style: symbol after amount
            return f"{amount:.2f} {symbol}"
        elif code in ["JPY", "KRW", "VND"]:
            # No decimal places for some currencies
            return f"{symbol}{amount:.0f}"
        else:
            # Default: symbol before amount
            return f"{symbol}{amount:.2f}"
