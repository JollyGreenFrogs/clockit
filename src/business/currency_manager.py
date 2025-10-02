"""
Currency management business logic
"""

import logging
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database.repositories import ConfigRepository

class CurrencyManager:
    """Handles all currency-related business operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.default_currency = {
            "code": "USD",
            "symbol": "$",
            "name": "US Dollar"
        }
    
    def _get_config_repo(self) -> ConfigRepository:
        """Get config repository with database session"""
        db = next(get_db())
        return ConfigRepository(db)
    
    def load_currency_config(self) -> Dict:
        """Load currency configuration from database"""
        try:
            config_repo = self._get_config_repo()
            config = config_repo.get_config("currency")
            return config if config else self.default_currency.copy()
        except Exception as e:
            self.logger.exception("Error loading currency config: %s", e)
            return self.default_currency.copy()
    
    def save_currency_config(self, currency_config: Dict) -> bool:
        """Save currency configuration to database"""
        try:
            config_repo = self._get_config_repo()
            return config_repo.save_config("currency", currency_config)
        except Exception as e:
            self.logger.exception("Error saving currency config: %s", e)
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
