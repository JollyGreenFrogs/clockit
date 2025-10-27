"""
Database repositories for data access layer
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .models import Category, Currency, Task, TimeEntry, UserConfig


class ConfigRepository:
    """Repository for user configuration data"""

    def __init__(self, db: Session):
        self.db = db

    def get_config(
        self, config_type: str, user_id: str = "00000000-0000-0000-0000-000000000001"
    ) -> Optional[Dict]:
        """Get configuration by type"""
        # Convert string UUID to UUID object for comparison
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        config = (
            self.db.query(UserConfig)
            .filter(
                and_(
                    UserConfig.user_id == user_uuid,
                    UserConfig.config_type == config_type,
                )
            )
            .first()
        )
        return config.config_data if config else None

    def save_config(
        self,
        config_type: str,
        config_data: Dict,
        user_id: str = "00000000-0000-0000-0000-000000000001",
    ) -> bool:
        """Save or update configuration"""
        try:
            # Convert string UUID to UUID object for comparison
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            config = (
                self.db.query(UserConfig)
                .filter(
                    and_(
                        UserConfig.user_id == user_uuid,
                        UserConfig.config_type == config_type,
                    )
                )
                .first()
            )

            if config:
                config.config_data = config_data
            else:
                config = UserConfig(
                    user_id=user_uuid, config_type=config_type, config_data=config_data
                )
                self.db.add(config)

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e


class TaskRepository:
    """Repository for task data"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_tasks(
        self, user_id: str = "00000000-0000-0000-0000-000000000001"
    ) -> Dict[str, float]:
        """Get all tasks as name -> time_spent mapping (legacy method)"""
        try:
            # Convert string UUID to UUID object for comparison
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            tasks = (
                self.db.query(Task)
                .filter(and_(Task.user_id == user_uuid, Task.is_active == True))
                .all()
            )
            return {task.name: task.time_spent for task in tasks}
        except (ValueError, TypeError):
            # Return empty dict for invalid UUIDs
            return {}

    def get_all_tasks_detailed(
        self, user_id: str = "00000000-0000-0000-0000-000000000001"
    ) -> List[Dict]:
        """Get all tasks with full details including IDs"""
        try:
            # Convert string UUID to UUID object for comparison
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            tasks = (
                self.db.query(Task)
                .filter(and_(Task.user_id == user_uuid, Task.is_active == True))
                .all()
            )
            return [
                {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "category": task.category,
                    "time_spent": task.time_spent,
                    "hourly_rate": task.hourly_rate,
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else None
                    ),
                    "updated_at": (
                        task.updated_at.isoformat() if task.updated_at else None
                    ),
                }
                for task in tasks
            ]
        except (ValueError, TypeError):
            # Return empty list for invalid UUIDs
            return []

    def get_task_by_id(
        self, task_id: int, user_id: str = "00000000-0000-0000-0000-000000000001"
    ) -> Optional[Dict]:
        """Get a single task by ID"""
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        task = (
            self.db.query(Task)
            .filter(
                and_(
                    Task.id == task_id,
                    Task.user_id == user_uuid,
                    Task.is_active == True,
                )
            )
            .first()
        )

        if not task:
            return None

        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "category": task.category,
            "time_spent": task.time_spent,
            "hourly_rate": task.hourly_rate,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    def get_task_details(
        self, user_id: str = "00000000-0000-0000-0000-000000000001"
    ) -> List[Dict]:
        """Get detailed task information"""
        # Convert string UUID to UUID object for comparison
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        tasks = (
            self.db.query(Task)
            .filter(and_(Task.user_id == user_uuid, Task.is_active == True))
            .all()
        )
        return [
            {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "category": task.category,
                "time_spent": task.time_spent,
                "hourly_rate": task.hourly_rate,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
            for task in tasks
        ]

    def create_or_update_task(
        self,
        name: str,
        time_spent: Optional[float] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        hourly_rate: Optional[float] = None,
        user_id: str = "00000000-0000-0000-0000-000000000001",
    ) -> bool:
        """Create new task or update existing one"""
        try:
            # Convert string UUID to UUID object for comparison
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            task = (
                self.db.query(Task)
                .filter(and_(Task.user_id == user_uuid, Task.name == name))
                .first()
            )

            if task:
                # Update existing task
                if time_spent is not None:
                    task.time_spent = time_spent
                if description is not None:
                    task.description = description
                if category is not None:
                    task.category = category
                if hourly_rate is not None:
                    task.hourly_rate = hourly_rate
            else:
                # Create new task
                task = Task(
                    user_id=user_uuid,
                    name=name,
                    description=description or "",
                    category=category,
                    time_spent=time_spent or 0.0,
                    hourly_rate=hourly_rate,
                )
                self.db.add(task)

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_task(
        self, name: str, user_id: str = "00000000-0000-0000-0000-000000000001"
    ) -> bool:
        """Soft delete a task"""
        try:
            # Convert string UUID to UUID object for comparison
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            task = (
                self.db.query(Task)
                .filter(and_(Task.user_id == user_uuid, Task.name == name))
                .first()
            )

            if task:
                task.is_active = False
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e

    def update_task_category(self, task_id: int, user_id: str, category: str) -> bool:
        """Update the category of a specific task"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            result = (
                self.db.query(Task)
                .filter(
                    and_(
                        Task.id == task_id,
                        Task.user_id == user_uuid,
                        Task.is_active == True
                    )
                )
                .update({Task.category: category})
            )
            self.db.commit()
            return result > 0
        except Exception as e:
            self.db.rollback()
            raise e


class CategoryRepository:
    """Repository for category data"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_categories(
        self, user_id: str = "00000000-0000-0000-0000-000000000001"
    ) -> List[Dict]:
        """Get all categories"""
        # Convert string UUID to UUID object for comparison
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        categories = self.db.query(Category).filter(Category.user_id == user_uuid).all()
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "color": cat.color,
            }
            for cat in categories
        ]

    def create_category(
        self,
        name: str,
        description: str = None,
        color: str = None,
        user_id: str = "00000000-0000-0000-0000-000000000001",
    ) -> bool:
        """Create a new category"""
        try:
            category = Category(
                user_id=user_id, name=name, description=description, color=color
            )
            self.db.add(category)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e


class TimeEntryRepository:
    """Repository for time entry data"""

    def __init__(self, db: Session):
        self.db = db

    def add_time_entry(
        self,
        task_name: str,
        duration: float,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[int] = None,
    ) -> bool:
        """Add a time entry"""
        if not user_id:
            raise ValueError("User ID is required for creating time entries")

        try:
            entry = TimeEntry(
                user_id=user_id,
                task_id=task_id,
                task_name=task_name,
                duration=duration,
                description=description,
            )
            self.db.add(entry)
            
            # Update task's total time_spent if task_id is provided
            if task_id:
                task = self.db.query(Task).filter(
                    and_(Task.id == task_id, Task.user_id == uuid.UUID(user_id))
                ).first()
                if task:
                    # Calculate new total time_spent by summing all time entries for this task
                    total_time = self.db.query(func.sum(TimeEntry.duration)).filter(
                        and_(TimeEntry.task_id == task_id, TimeEntry.user_id == uuid.UUID(user_id))
                    ).scalar() or 0.0
                    total_time += duration  # Add the current entry
                    task.time_spent = total_time
                    task.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def get_time_entries_for_task(self, task_id: int, user_id: str) -> List[Dict]:
        """Get all time entries for a specific task"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            entries = (
                self.db.query(TimeEntry)
                .filter(
                    and_(
                        TimeEntry.task_id == task_id,
                        TimeEntry.user_id == user_uuid
                    )
                )
                .order_by(TimeEntry.created_at.desc())
                .all()
            )
            
            return [
                {
                    "id": entry.id,
                    "task_id": entry.task_id,
                    "task_name": entry.task_name,
                    "duration": entry.duration,
                    "description": entry.description,
                    "start_time": entry.start_time.isoformat() if entry.start_time is not None else None,
                    "end_time": entry.end_time.isoformat() if entry.end_time is not None else None,
                    "entry_date": entry.entry_date.isoformat() if entry.entry_date is not None else None,
                    "created_at": entry.created_at.isoformat() if entry.created_at is not None else None
                }
                for entry in entries
            ]
        except Exception as e:
            raise e

    def delete_time_entry(self, entry_id: int, user_id: str) -> bool:
        """Delete a specific time entry"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            entry = (
                self.db.query(TimeEntry)
                .filter(
                    and_(
                        TimeEntry.id == entry_id,
                        TimeEntry.user_id == user_uuid
                    )
                )
                .first()
            )
            
            if entry:
                self.db.delete(entry)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e

    def update_time_entry(
        self, entry_id: int, user_id: str, duration: Optional[float] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update a specific time entry"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            
            update_data = {}
            if duration is not None:
                update_data[TimeEntry.duration] = duration
            if description is not None:
                update_data[TimeEntry.description] = description
            
            if update_data:
                result = (
                    self.db.query(TimeEntry)
                    .filter(
                        and_(
                            TimeEntry.id == entry_id,
                            TimeEntry.user_id == user_uuid
                        )
                    )
                    .update(update_data)
                )
                self.db.commit()
                return result > 0
            return False
        except Exception as e:
            self.db.rollback()
            raise e


class CurrencyRepository:
    """Repository for currency data"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_currencies(self) -> List[Dict]:
        """Get all active currencies"""
        currencies = self.db.query(Currency).filter(Currency.is_active == True).all()
        return [
            {"code": currency.code, "symbol": currency.symbol, "name": currency.name}
            for currency in currencies
        ]

    def get_currency_by_code(self, code: str) -> Optional[Dict]:
        """Get currency by code"""
        currency = (
            self.db.query(Currency)
            .filter(Currency.code == code, Currency.is_active == True)
            .first()
        )

        if currency:
            return {
                "code": currency.code,
                "symbol": currency.symbol,
                "name": currency.name,
            }
        return None

    def create_currency(self, code: str, symbol: str, name: str) -> bool:
        """Create a new currency"""
        try:
            currency = Currency(code=code, symbol=symbol, name=name)
            self.db.add(currency)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def bulk_create_currencies(self, currencies_data: List[Dict]) -> bool:
        """Create multiple currencies at once"""
        try:
            for curr_data in currencies_data:
                # Check if currency already exists
                existing = (
                    self.db.query(Currency)
                    .filter(Currency.code == curr_data["code"])
                    .first()
                )
                if not existing:
                    currency = Currency(
                        code=curr_data["code"],
                        symbol=curr_data["symbol"],
                        name=curr_data["name"],
                    )
                    self.db.add(currency)

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
