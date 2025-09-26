"""
Task management business logic
"""

import json
import os
from datetime import datetime
import logging
from typing import Dict, List, Optional
from pathlib import Path

class TaskManager:
    """Handles all task-related business operations"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.tasks_file = data_dir / "tasks_data.json"
        self.exported_file = data_dir / "exported_tasks.json"
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_tasks(self) -> Dict:
        """Load tasks from storage"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.exception("Error loading tasks: %s", e)
        return {"tasks": {}}
    
    def save_tasks(self, tasks_data: Dict) -> bool:
        """Save tasks to storage"""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.exception("Error saving tasks: %s", e)
            return False
    
    def create_task(self, name: str, description: str = "", parent_heading: str = "") -> Dict:
        """Create a new task"""
        tasks_data = self.load_tasks()
        task_id = str(len(tasks_data["tasks"]) + 1)
        
        new_task = {
            "id": task_id,
            "name": name,
            "description": description,
            "parent_heading": parent_heading,
            "time_entries": [],
            "total_hours": 0,
            "created_at": datetime.now().isoformat(),
            "exported": False
        }
        
        tasks_data["tasks"][task_id] = new_task
        self.save_tasks(tasks_data)
        return new_task
    
    def add_time_entry(self, task_id: str, hours: float, date: str, description: str = "") -> bool:
        """Add time entry to a task"""
        tasks_data = self.load_tasks()
        
        if task_id not in tasks_data["tasks"]:
            return False
        
        time_entry = {
            "hours": hours,
            "date": date,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        
        tasks_data["tasks"][task_id]["time_entries"].append(time_entry)
        
        # Update total hours
        total_hours = sum(entry["hours"] for entry in tasks_data["tasks"][task_id]["time_entries"])
        tasks_data["tasks"][task_id]["total_hours"] = total_hours
        
        return self.save_tasks(tasks_data)
    
    def get_task_categories(self) -> List[str]:
        """Get all unique task categories"""
        tasks_data = self.load_tasks()
        categories = set()
        
        for task in tasks_data["tasks"].values():
            if task.get("parent_heading"):
                categories.add(task["parent_heading"])
        
        return sorted(list(categories))
    
    def mark_tasks_exported(self, task_ids: List[str]) -> bool:
        """Mark tasks as exported"""
        tasks_data = self.load_tasks()
        
        for task_id in task_ids:
            if task_id in tasks_data["tasks"]:
                tasks_data["tasks"][task_id]["exported"] = True
        
        # Also update exported tasks file
        exported_data = self.load_exported_tasks()
        exported_data["exported_task_ids"].extend(task_ids)
        
        return self.save_tasks(tasks_data) and self.save_exported_tasks(exported_data)
    
    def load_exported_tasks(self) -> Dict:
        """Load exported tasks tracking"""
        if self.exported_file.exists():
            try:
                with open(self.exported_file, 'r') as f:
                    return json.load(f)
            except Exception:
                self.logger.exception("Error loading exported tasks")
        return {"exported_task_ids": []}
    
    def save_exported_tasks(self, exported_data: Dict) -> bool:
        """Save exported tasks tracking"""
        try:
            with open(self.exported_file, 'w') as f:
                json.dump(exported_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.exception("Error saving exported tasks: %s", e)
            return False
