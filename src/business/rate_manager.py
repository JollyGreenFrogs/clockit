"""
Rate management business logic
"""

import json
import logging
from pathlib import Path
from typing import Dict


class RateManager:
    """Handles all rate-related business operations"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.rates_file = data_dir / "rates_config.json"
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_rates(self) -> Dict[str, float]:
        """Load rates from storage"""
        if self.rates_file.exists():
            try:
                with open(self.rates_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.exception("Error loading rates: %s", e)
        return {}

    def save_rates(self, rates: Dict[str, float]) -> bool:
        """Save rates to storage"""
        try:
            with open(self.rates_file, "w") as f:
                json.dump(rates, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving rates: {e}")
            return False

    def set_rate(self, task_type: str, day_rate: float) -> bool:
        """Set rate for a task type"""
        rates = self.load_rates()
        rates[task_type] = day_rate
        return self.save_rates(rates)

    def get_rate(self, task_type: str) -> float:
        """Get rate for a task type"""
        rates = self.load_rates()
        return rates.get(task_type, 0.0)

    def delete_rate(self, task_type: str) -> bool:
        """Delete rate for a task type"""
        rates = self.load_rates()
        if task_type in rates:
            del rates[task_type]
            return self.save_rates(rates)
        return False

    def calculate_hourly_rate(self, day_rate: float) -> float:
        """Calculate hourly rate from day rate (8 hour work day)"""
        return day_rate / 8.0

    def get_all_categories(self) -> list:
        """Get all rate categories"""
        rates = self.load_rates()
        return list(rates.keys())
