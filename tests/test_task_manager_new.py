"""
Test TaskManager business logic with new database architecture
"""

import uuid
from unittest.mock import Mock, patch

import pytest

from business.task_manager import TaskManager
from database.repositories import (
    CategoryRepository,
    TaskRepository,
    TimeEntryRepository,
)


class TestTaskManagerConstruction:
    """Test TaskManager initialization"""

    def test_task_manager_init(self):
        """Test TaskManager can be initialized without parameters"""
        tm = TaskManager()
        assert tm.logger is not None

    def test_task_manager_init_no_data_dir(self):
        """Test TaskManager doesn't require data_dir parameter anymore"""
        # This should not raise an error
        tm = TaskManager()
        assert isinstance(tm, TaskManager)


class TestTaskManagerWithMockedDB:
    """Test TaskManager with mocked database operations"""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        task_repo = Mock(spec=TaskRepository)
        category_repo = Mock(spec=CategoryRepository)
        time_repo = Mock(spec=TimeEntryRepository)
        return task_repo, category_repo, time_repo

    @pytest.fixture
    def task_manager_with_mocks(self, mock_repositories):
        """Create TaskManager with mocked repositories"""
        tm = TaskManager()

        # Mock the _get_repositories method to return our mocks
        tm._get_repositories = Mock(return_value=mock_repositories)
        return tm, mock_repositories

    def test_load_tasks_success(self, task_manager_with_mocks):
        """Test successful task loading"""
        tm, (task_repo, _, _) = task_manager_with_mocks

        # Mock successful repository call
        task_repo.get_all_tasks.return_value = {"task1": 2.5, "task2": 3.0}

        result = tm.load_tasks()

        assert result == {"tasks": {"task1": 2.5, "task2": 3.0}}
        task_repo.get_all_tasks.assert_called_once()

    def test_load_tasks_for_user_success(self, task_manager_with_mocks):
        """Test successful task loading for specific user"""
        tm, (task_repo, _, _) = task_manager_with_mocks
        user_id = str(uuid.uuid4())

        # Mock successful repository call
        task_repo.get_all_tasks_detailed.return_value = {"user_task": 1.5}

        result = tm.load_tasks_for_user(user_id)

        assert result == {"tasks": {"user_task": 1.5}}
        task_repo.get_all_tasks_detailed.assert_called_once_with(user_id=user_id)

    def test_load_tasks_database_error(self, task_manager_with_mocks):
        """Test task loading with database error"""
        tm, (task_repo, _, _) = task_manager_with_mocks

        # Mock database error
        task_repo.get_all_tasks.side_effect = Exception("Database connection failed")

        result = tm.load_tasks()

        assert result == {"tasks": {}}

    def test_create_task_for_user_success(self, task_manager_with_mocks):
        """Test successful task creation for user"""
        tm, (task_repo, _, _) = task_manager_with_mocks
        user_id = str(uuid.uuid4())

        # Mock successful repository call
        task_repo.create_or_update_task.return_value = True

        result = tm.create_task_for_user(
            name="Test Task",
            user_id=user_id,
            description="Test description",
            category="Development",
            hourly_rate=50.0,
        )

        assert result is True
        task_repo.create_or_update_task.assert_called_once_with(
            name="Test Task",
            description="Test description",
            category="Development",
            time_spent=0.0,
            hourly_rate=50.0,
            user_id=user_id,
        )

    def test_create_task_for_user_failure(self, task_manager_with_mocks):
        """Test task creation failure"""
        tm, (task_repo, _, _) = task_manager_with_mocks
        user_id = str(uuid.uuid4())

        # Mock repository failure
        task_repo.create_or_update_task.side_effect = Exception("Database error")

        result = tm.create_task_for_user(name="Test Task", user_id=user_id)

        assert result is False

    def test_create_task_legacy_method(self, task_manager_with_mocks):
        """Test legacy create_task method still works"""
        tm, (task_repo, _, _) = task_manager_with_mocks

        # Mock successful repository call
        task_repo.create_or_update_task.return_value = True

        result = tm.create_task(
            name="Legacy Task", description="Legacy description", category="Development"
        )

        assert result is True
        task_repo.create_or_update_task.assert_called_once_with(
            name="Legacy Task",
            description="Legacy description",
            category="Development",
            time_spent=0.0,
        )

    def test_save_task_success(self, task_manager_with_mocks):
        """Test successful task saving"""
        tm, (task_repo, _, _) = task_manager_with_mocks

        # Mock successful repository call
        task_repo.create_or_update_task.return_value = True

        result = tm.save_task(
            task_name="Test Task",
            time_spent=2.5,
            description="Updated description",
            category="Development",
            hourly_rate=60.0,
        )

        assert result is True
        task_repo.create_or_update_task.assert_called_once_with(
            name="Test Task",
            time_spent=2.5,
            description="Updated description",
            category="Development",
            hourly_rate=60.0,
        )

    def test_delete_task_success(self, task_manager_with_mocks):
        """Test successful task deletion"""
        tm, (task_repo, _, _) = task_manager_with_mocks
        user_id = str(uuid.uuid4())

        # Mock successful repository call
        task_repo.delete_task.return_value = True

        result = tm.delete_task("Test Task", user_id=user_id)

        assert result is True
        task_repo.delete_task.assert_called_once_with("Test Task", user_id=user_id)

    def test_get_task_categories_success(self, task_manager_with_mocks):
        """Test successful category retrieval"""
        tm, (_, category_repo, _) = task_manager_with_mocks

        # Mock successful repository call
        category_repo.get_all_categories.return_value = [
            {"name": "Development", "description": "Dev work"},
            {"name": "Testing", "description": "Test work"},
        ]

        result = tm.get_task_categories()

        assert result == ["Development", "Testing"]
        category_repo.get_all_categories.assert_called_once()

    def test_create_category_success(self, task_manager_with_mocks):
        """Test successful category creation"""
        tm, (_, category_repo, _) = task_manager_with_mocks

        # Mock successful repository call
        category_repo.create_category.return_value = True

        result = tm.create_category(
            name="New Category", description="A new category", color="#ff0000"
        )

        assert result is True
        category_repo.create_category.assert_called_once_with(
            "New Category", "A new category", "#ff0000"
        )

    def test_add_time_entry_success(self, task_manager_with_mocks):
        """Test successful time entry addition"""
        tm, (task_repo, _, time_repo) = task_manager_with_mocks
        user_id = str(uuid.uuid4())

        # Mock existing tasks and successful operations
        task_repo.get_all_tasks.return_value = {"Test Task": 2.0}
        task_repo.create_or_update_task.return_value = True
        time_repo.add_time_entry.return_value = True

        result = tm.add_time_entry(
            task_name="Test Task",
            duration=1.5,
            date="2025-10-01",
            description="Additional work",
            user_id=user_id,
        )

        assert result is True
        task_repo.get_all_tasks.assert_called_once_with(user_id=user_id)
        task_repo.create_or_update_task.assert_called_once_with(
            name="Test Task", time_spent=3.5, user_id=user_id  # 2.0 + 1.5
        )
        time_repo.add_time_entry.assert_called_once_with(
            task_name="Test Task",
            duration=1.5,
            description="Additional work",
            user_id=user_id,
        )

    def test_get_task_details_success(self, task_manager_with_mocks):
        """Test successful task details retrieval"""
        tm, (task_repo, _, _) = task_manager_with_mocks

        # Mock successful repository call
        expected_details = [
            {"id": "1", "name": "Task 1", "time_spent": 2.5},
            {"id": "2", "name": "Task 2", "time_spent": 3.0},
        ]
        task_repo.get_task_details.return_value = expected_details

        result = tm.get_task_details()

        assert result == expected_details
        task_repo.get_task_details.assert_called_once()


class TestTaskManagerErrorHandling:
    """Test TaskManager error handling"""

    def test_all_methods_handle_exceptions_gracefully(self):
        """Test that all methods handle exceptions gracefully"""
        tm = TaskManager()

        # Mock _get_repositories to raise an exception
        tm._get_repositories = Mock(side_effect=Exception("Database connection failed"))

        # All these methods should return safe default values, not raise exceptions
        assert tm.load_tasks() == {"tasks": {}}
        assert tm.load_tasks_for_user("user_id") == {"tasks": {}}
        assert tm.save_task("task", 1.0) is False
        assert tm.create_task("task") is False
        assert tm.create_task_for_user("task", "user_id") is False
        assert tm.add_time_entry("task", 1.0) is False
        assert tm.delete_task("task") is False
        assert tm.get_task_categories() == []
        assert tm.create_category("category") is False
        assert tm.get_task_details() == []


class TestTaskManagerIntegration:
    """Integration tests with real database (using test fixtures)"""

    def test_task_manager_with_real_db(self, test_db_session, clean_database):
        """Test TaskManager with real database session"""
        # This would require setting up the database dependency override
        # in the TaskManager or using dependency injection
        pass  # Placeholder for integration tests

    def test_user_data_isolation_in_task_manager(self, test_db_session, clean_database):
        """Test that TaskManager properly isolates user data"""
        # This would test that the TaskManager methods properly
        # use user_id parameters to isolate data
        pass  # Placeholder for integration tests
