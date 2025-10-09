"""
Task management business logic
"""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database.repositories import (
    CategoryRepository,
    TaskRepository,
    TimeEntryRepository,
)


class TaskManager:
    """Handles all task-related business operations"""
    
    def __init__(self, data_dir=None):
        """Initialize TaskManager
        
        Args:
            data_dir: Legacy parameter for backwards compatibility, ignored in database version
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if data_dir is not None:
            # For backwards compatibility, just log a warning
            self.logger.warning(
                "data_dir parameter is deprecated and ignored in database-backed TaskManager"
            )

    def _get_repositories(self):
        """Get database repositories with session"""
        db = next(get_db())
        return (TaskRepository(db), CategoryRepository(db), TimeEntryRepository(db))

    def load_tasks(self) -> Dict:
        """Load tasks from database"""
        try:
            task_repo, _, _ = self._get_repositories()
            tasks = task_repo.get_all_tasks()
            return {"tasks": tasks}
        except Exception as e:
            self.logger.exception("Error loading tasks: %s", e)
            return {"tasks": {}}

    def load_tasks_for_user(self, user_id: str) -> Dict:
        """Load tasks from database for specific user with full details"""
        try:
            task_repo, _, _ = self._get_repositories()
            tasks = task_repo.get_all_tasks_detailed(user_id=user_id)
            return {"tasks": tasks}
        except Exception as e:
            self.logger.exception("Error loading tasks for user %s: %s", user_id, e)
            return {"tasks": {}}

    def get_task_by_id(self, task_id: int, user_id: str) -> Optional[Dict]:
        """Get a single task by ID"""
        try:
            task_repo, _, _ = self._get_repositories()
            return task_repo.get_task_by_id(task_id, user_id)
        except Exception as e:
            self.logger.exception(
                "Error getting task %s for user %s: %s", task_id, user_id, e
            )
            return None

    def save_task(
        self,
        task_name: str,
        time_spent: float,
        description: str = "",
        category: str = "",
        hourly_rate: Optional[float] = None,
    ) -> bool:
        """Save or update a task"""
        try:
            task_repo, _, _ = self._get_repositories()
            return task_repo.create_or_update_task(
                name=task_name,
                time_spent=time_spent,
                description=description,
                category=category,
                hourly_rate=hourly_rate,
            )
        except Exception as e:
            self.logger.exception("Error saving task: %s", e)
            return False

    def create_task(self, name: str, description: str = "", category: str = "") -> bool:
        """Create a new task"""
        try:
            task_repo, _, _ = self._get_repositories()
            return task_repo.create_or_update_task(
                name=name, description=description, category=category, time_spent=0.0
            )
        except Exception as e:
            self.logger.exception("Error creating task: %s", e)
            return False

    def create_task_for_user(
        self,
        name: str,
        user_id: str,
        description: str = "",
        category: str = "",
        task_type: str = "",
        priority: str = "",
        hourly_rate: Optional[float] = None,
    ) -> bool:
        """Create a new task for specific user"""
        try:
            task_repo, _, _ = self._get_repositories()
            return task_repo.create_or_update_task(
                name=name,
                description=description,
                category=category,
                time_spent=0.0,
                hourly_rate=hourly_rate,
                user_id=user_id,
            )
        except Exception as e:
            self.logger.exception("Error creating task for user %s: %s", user_id, e)
            return False

    def add_time_entry(
        self,
        task_name: str,
        duration: float,
        date: Optional[str] = None,
        description: str = "",
        user_id: Optional[str] = None,
    ) -> bool:
        """Add time entry to a task for a specific user"""
        try:
            if not user_id:
                self.logger.error("User ID is required for adding time entries")
                return False

            task_repo, _, time_repo = self._get_repositories()

            # First check if task exists for this user
            tasks = task_repo.get_all_tasks(user_id=user_id)
            if task_name not in tasks:
                self.logger.error(
                    f"Task '{task_name}' not found for user {user_id}. Available tasks: {list(tasks.keys())}"
                )
                return False

            # Get the current task time for this user
            current_time = tasks.get(task_name, 0.0)

            success = task_repo.create_or_update_task(
                name=task_name, time_spent=current_time + duration, user_id=user_id
            )

            # Then add detailed time entry
            if success:
                time_repo.add_time_entry(
                    task_name=task_name,
                    duration=duration,
                    description=description,
                    user_id=user_id,
                )

            return success
        except Exception as e:
            self.logger.exception("Error adding time entry: %s", e)
            return False

    def add_time_entry_by_id(
        self,
        task_id: int,
        duration: float,
        date: Optional[str] = None,
        description: str = "",
        user_id: Optional[str] = None,
    ) -> bool:
        """Add time entry to a task by ID for a specific user"""
        try:
            if not user_id:
                self.logger.error("User ID is required for adding time entries")
                return False

            task_repo, _, time_repo = self._get_repositories()

            # First check if task exists for this user
            task = task_repo.get_task_by_id(task_id, user_id)
            if not task:
                self.logger.error(f"Task ID {task_id} not found for user {user_id}")
                return False

            # Get the current task time
            current_time = task.get("time_spent", 0.0)

            success = task_repo.create_or_update_task(
                name=task["name"], time_spent=current_time + duration, user_id=user_id
            )

            # Then add detailed time entry
            if success:
                time_repo.add_time_entry(
                    task_name=task["name"],
                    duration=duration,
                    description=description,
                    user_id=user_id,
                )

            return success
        except Exception as e:
            self.logger.exception("Error adding time entry by ID: %s", e)
            return False

    def delete_task(self, task_name: str, user_id: Optional[str] = None) -> bool:
        """Delete a task for a specific user"""
        try:
            if not user_id:
                self.logger.error("User ID is required for deleting tasks")
                return False

            task_repo, _, _ = self._get_repositories()
            return task_repo.delete_task(task_name, user_id=user_id)
        except Exception as e:
            self.logger.exception("Error deleting task for user %s: %s", user_id, e)
            return False

    def get_task_categories(self) -> List[str]:
        """Get all available categories"""
        try:
            _, cat_repo, _ = self._get_repositories()
            categories = cat_repo.get_all_categories()
            return [cat["name"] for cat in categories]
        except Exception as e:
            self.logger.exception("Error getting categories: %s", e)
            return []

    def create_category(
        self, name: str, description: str = "", color: str = ""
    ) -> bool:
        """Create a new category"""
        try:
            _, cat_repo, _ = self._get_repositories()
            return cat_repo.create_category(name, description, color)
        except Exception as e:
            self.logger.exception("Error creating category: %s", e)
            return False

    def get_task_details(self) -> List[Dict]:
        """Get detailed task information"""
        try:
            task_repo, _, _ = self._get_repositories()
            return task_repo.get_task_details()
        except Exception as e:
            self.logger.exception("Error getting task details: %s", e)
            return []
