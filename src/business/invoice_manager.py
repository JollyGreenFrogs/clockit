"""
Invoice generation business logic
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from .task_manager import TaskManager
from .rate_manager import RateManager
from .currency_manager import CurrencyManager

class InvoiceManager:
    """Handles invoice generation and export logic"""
    
    def __init__(self, data_dir: Path, task_manager: TaskManager):
        self.data_dir = data_dir
        self.columns_file = data_dir / "invoice_columns.json"
        self.default_columns = ["Task", "Total Hours", "Day Rate", "Hour Rate", "Amount"]
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.task_manager = task_manager
        self.rate_manager = RateManager(data_dir)
        self.currency_manager = CurrencyManager()
    
    def load_invoice_columns(self) -> List[str]:
        """Load invoice column configuration"""
        if self.columns_file.exists():
            try:
                with open(self.columns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.exception("Error loading invoice columns: %s", e)
        return self.default_columns.copy()
    
    def save_invoice_columns(self, columns: List[str]) -> bool:
        """Save invoice column configuration"""
        try:
            with open(self.columns_file, 'w') as f:
                json.dump(columns, f, indent=2)
            return True
        except Exception as e:
            self.logger.exception("Error saving invoice columns: %s", e)
            return False
    
    def generate_invoice(self, include_exported: bool = False) -> Dict:
        """Generate invoice from tasks"""
        tasks_data = self.task_manager.load_tasks()
        rates = self.rate_manager.load_rates()
        currency_config = self.currency_manager.get_current_currency()
        
        # Filter tasks for invoice
        eligible_tasks = {}
        for task_id, task in tasks_data["tasks"].items():
            if task["total_hours"] > 0:
                if include_exported or not task.get("exported", False):
                    eligible_tasks[task_id] = task
        
        if not eligible_tasks:
            return {"error": "No eligible tasks found for invoice"}
        
        # Group tasks by parent heading
        grouped_tasks = {}
        for task_id, task in eligible_tasks.items():
            heading = task.get("parent_heading", "Other")
            if heading not in grouped_tasks:
                grouped_tasks[heading] = []
            grouped_tasks[heading].append((task_id, task))
        
        # Generate invoice items
        invoice_items = []
        total_amount = 0
        task_ids_to_export = []
        
        for heading, tasks in grouped_tasks.items():
            total_hours = sum(task["total_hours"] for _, task in tasks)
            
            # Get rate for this category
            day_rate = rates.get(heading, 0)
            hour_rate = self.rate_manager.calculate_hourly_rate(day_rate)
            amount = total_hours * hour_rate
            total_amount += amount
            
            # Collect task IDs for export tracking
            task_ids_to_export.extend([task_id for task_id, _ in tasks])
            
            # Create invoice item
            item = {
                "task": heading,
                "total_hours": round(total_hours, 2),
                "day_rate": self.currency_manager.format_currency(day_rate, currency_config),
                "hour_rate": self.currency_manager.format_currency(hour_rate, currency_config),
                "amount": self.currency_manager.format_currency(amount, currency_config),
                "task_details": [
                    {
                        "name": task["name"],
                        "hours": task["total_hours"],
                        "description": task.get("description", "")
                    }
                    for _, task in tasks
                ]
            }
            invoice_items.append(item)
        
        # Generate invoice
        invoice = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "currency": currency_config,
            "items": invoice_items,
            "total": self.currency_manager.format_currency(total_amount, currency_config),
            "task_ids": task_ids_to_export
        }
        
        return invoice
    
    def export_invoice(self, invoice_data: Dict) -> bool:
        """Export invoice and mark tasks as exported"""
        try:
            # Save invoice to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            invoice_file = self.data_dir / f"invoice_{timestamp}.json"
            
            with open(invoice_file, 'w') as f:
                json.dump(invoice_data, f, indent=2)
            
            # Mark tasks as exported
            task_ids = invoice_data.get("task_ids", [])
            if task_ids:
                self.task_manager.mark_tasks_exported(task_ids)
            
            return True
            
        except Exception as e:
            print(f"Error exporting invoice: {e}")
            return False
