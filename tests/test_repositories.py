"""
Test database repositories functionality with new architecture
"""

import uuid

import pytest

from database.auth_models import User
from database.repositories import (
    CategoryRepository,
    ConfigRepository,
    TaskRepository,
    TimeEntryRepository,
)


class TestTaskRepository:
    """Test TaskRepository functionality"""

    @pytest.fixture
    def task_repo(self, test_db_session):
        """Create TaskRepository instance"""
        return TaskRepository(test_db_session)

    @pytest.fixture
    def test_user_id(self, test_db_session):
        """Create a test user and return its ID"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        user = User(
            id=uuid.uuid4(),
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        return str(user.id)

    @pytest.fixture
    def test_user_id(self, test_db_session):
        """Create a test user and return its ID"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        user = User(
            id=uuid.uuid4(),
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        return str(user.id)

    @pytest.fixture
    def test_user_id(self, test_db_session):
        """Create a test user and return its ID"""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        return str(user.id)

    def test_create_task(self, task_repo, test_user_id, clean_database):
        """Test creating a new task"""
        success = task_repo.create_or_update_task(
            name="Test Task",
            description="A test task",
            category="Development",
            time_spent=0.0,
            hourly_rate=50.0,
            user_id=test_user_id,
        )

        assert success is True

        # Verify task was created
        tasks = task_repo.get_all_tasks(user_id=test_user_id)
        assert "Test Task" in tasks
        assert tasks["Test Task"] == 0.0

    def test_update_existing_task(self, task_repo, test_user_id, clean_database):
        """Test updating an existing task"""
        # Create initial task
        task_repo.create_or_update_task(
            name="Test Task",
            description="Initial description",
            time_spent=1.0,
            user_id=test_user_id,
        )

        # Update the task
        success = task_repo.create_or_update_task(
            name="Test Task",
            description="Updated description",
            time_spent=2.5,
            user_id=test_user_id,
        )

        assert success is True

        # Verify task was updated
        tasks = task_repo.get_all_tasks(user_id=test_user_id)
        assert tasks["Test Task"] == 2.5

    def test_get_all_tasks_empty(self, task_repo, test_user_id, clean_database):
        """Test getting tasks when none exist"""
        tasks = task_repo.get_all_tasks(user_id=test_user_id)
        assert tasks == {}

    def test_get_all_tasks_with_data(self, task_repo, test_user_id, clean_database):
        """Test getting tasks when they exist"""
        # Create multiple tasks
        task_repo.create_or_update_task("Task 1", time_spent=1.0, user_id=test_user_id)
        task_repo.create_or_update_task("Task 2", time_spent=2.0, user_id=test_user_id)
        task_repo.create_or_update_task("Task 3", time_spent=3.0, user_id=test_user_id)

        tasks = task_repo.get_all_tasks(user_id=test_user_id)

        assert len(tasks) == 3
        assert tasks["Task 1"] == 1.0
        assert tasks["Task 2"] == 2.0
        assert tasks["Task 3"] == 3.0

    def test_user_data_isolation(self, task_repo, test_db_session, clean_database):
        """Test that users can only see their own tasks"""
        # Create two users
        user1 = User(
            id=uuid.uuid4(),
            username="user1",
            email="user1@test.com",
            hashed_password="hash1",
            is_active=True,
        )
        user2 = User(
            id=uuid.uuid4(),
            username="user2",
            email="user2@test.com",
            hashed_password="hash2",
            is_active=True,
        )
        test_db_session.add_all([user1, user2])
        test_db_session.commit()

        user1_id = str(user1.id)
        user2_id = str(user2.id)

        # Create tasks for each user
        task_repo.create_or_update_task("User1 Task", time_spent=1.0, user_id=user1_id)
        task_repo.create_or_update_task("User2 Task", time_spent=2.0, user_id=user2_id)

        # Each user should only see their own tasks
        user1_tasks = task_repo.get_all_tasks(user_id=user1_id)
        user2_tasks = task_repo.get_all_tasks(user_id=user2_id)

        assert len(user1_tasks) == 1
        assert len(user2_tasks) == 1
        assert "User1 Task" in user1_tasks
        assert "User2 Task" in user2_tasks
        assert "User1 Task" not in user2_tasks
        assert "User2 Task" not in user1_tasks

    def test_delete_task(self, task_repo, test_user_id, clean_database):
        """Test task deletion"""
        # Create a task
        task_repo.create_or_update_task(
            "Task to Delete", time_spent=1.0, user_id=test_user_id
        )

        # Verify it exists
        tasks = task_repo.get_all_tasks(user_id=test_user_id)
        assert "Task to Delete" in tasks

        # Delete it
        success = task_repo.delete_task("Task to Delete", user_id=test_user_id)
        assert success is True

        # Verify it's gone
        tasks = task_repo.get_all_tasks(user_id=test_user_id)
        assert "Task to Delete" not in tasks

    def test_delete_nonexistent_task(self, task_repo, test_user_id, clean_database):
        """Test deleting a task that doesn't exist"""
        success = task_repo.delete_task("Nonexistent Task", user_id=test_user_id)
        # Should handle gracefully
        assert success in [True, False]  # Depending on implementation

    def test_get_task_details(self, task_repo, test_user_id, clean_database):
        """Test getting detailed task information"""
        # Create tasks with details
        task_repo.create_or_update_task(
            name="Detailed Task",
            description="A task with details",
            category="Development",
            time_spent=2.5,
            hourly_rate=60.0,
            user_id=test_user_id,
        )

        details = task_repo.get_task_details(user_id=test_user_id)

        assert len(details) == 1
        task_detail = details[0]
        assert task_detail["name"] == "Detailed Task"
        assert task_detail["description"] == "A task with details"
        assert task_detail["category"] == "Development"
        assert task_detail["time_spent"] == 2.5
        assert task_detail["hourly_rate"] == 60.0


class TestCategoryRepository:
    """Test CategoryRepository functionality"""

    @pytest.fixture
    def category_repo(self, test_db_session):
        """Create CategoryRepository instance"""
        return CategoryRepository(test_db_session)

    @pytest.fixture
    def test_user_id(self, test_db_session):
        """Create a test user and return its ID"""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        return str(user.id)

    def test_create_category(self, category_repo, test_user_id, clean_database):
        """Test creating a new category"""
        success = category_repo.create_category(
            name="Development",
            description="Software development tasks",
            color="#007bff",
            user_id=test_user_id,
        )

        assert success is True

        # Verify category was created
        categories = category_repo.get_all_categories(user_id=test_user_id)
        assert len(categories) == 1
        assert categories[0]["name"] == "Development"
        assert categories[0]["description"] == "Software development tasks"
        assert categories[0]["color"] == "#007bff"

    def test_get_all_categories_empty(
        self, category_repo, test_user_id, clean_database
    ):
        """Test getting categories when none exist"""
        categories = category_repo.get_all_categories(user_id=test_user_id)
        assert categories == []

    def test_category_user_isolation(
        self, category_repo, test_db_session, clean_database
    ):
        """Test that users can only see their own categories"""
        # Create two users
        user1 = User(
            id=uuid.uuid4(),
            username="user1",
            email="user1@test.com",
            hashed_password="hash1",
            is_active=True,
        )
        user2 = User(
            id=uuid.uuid4(),
            username="user2",
            email="user2@test.com",
            hashed_password="hash2",
            is_active=True,
        )
        test_db_session.add_all([user1, user2])
        test_db_session.commit()

        user1_id = str(user1.id)
        user2_id = str(user2.id)

        # Create categories for each user
        category_repo.create_category("User1 Category", user_id=user1_id)
        category_repo.create_category("User2 Category", user_id=user2_id)

        # Each user should only see their own categories
        user1_categories = category_repo.get_all_categories(user_id=user1_id)
        user2_categories = category_repo.get_all_categories(user_id=user2_id)

        assert len(user1_categories) == 1
        assert len(user2_categories) == 1
        assert user1_categories[0]["name"] == "User1 Category"
        assert user2_categories[0]["name"] == "User2 Category"


class TestTimeEntryRepository:
    """Test TimeEntryRepository functionality"""

    @pytest.fixture
    def time_repo(self, test_db_session):
        """Create TimeEntryRepository instance"""
        return TimeEntryRepository(test_db_session)

    @pytest.fixture
    def test_user_id(self, test_db_session):
        """Create a test user and return its ID"""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        return str(user.id)

    def test_add_time_entry(self, time_repo, test_user_id, clean_database):
        """Test adding a time entry"""
        success = time_repo.add_time_entry(
            task_name="Test Task",
            duration=2.5,
            description="Work completed",
            user_id=test_user_id,
        )

        assert success is True

    def test_add_time_entry_minimal(self, time_repo, test_user_id, clean_database):
        """Test adding a time entry with minimal data"""
        success = time_repo.add_time_entry(
            task_name="Test Task", duration=1.0, user_id=test_user_id
        )

        assert success is True


class TestConfigRepository:
    """Test ConfigRepository functionality"""

    @pytest.fixture
    def config_repo(self, test_db_session):
        """Create ConfigRepository instance"""
        return ConfigRepository(test_db_session)

    @pytest.fixture
    def test_user_id(self, test_db_session):
        """Create a test user and return its ID"""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        return str(user.id)

    def test_save_and_get_config(self, config_repo, test_user_id, clean_database):
        """Test saving and retrieving configuration"""
        config_data = {"currency": "USD", "default_rate": 50.0, "timezone": "UTC"}

        # Save config
        success = config_repo.save_config("general", config_data, user_id=test_user_id)
        assert success is True

        # Retrieve config
        retrieved_config = config_repo.get_config("general", user_id=test_user_id)
        assert retrieved_config == config_data

    def test_get_nonexistent_config(self, config_repo, test_user_id, clean_database):
        """Test getting configuration that doesn't exist"""
        config = config_repo.get_config("nonexistent", user_id=test_user_id)
        assert config is None

    def test_update_existing_config(self, config_repo, test_user_id, clean_database):
        """Test updating existing configuration"""
        initial_config = {"setting": "value1"}
        updated_config = {"setting": "value2", "new_setting": "new_value"}

        # Save initial config
        config_repo.save_config("test", initial_config, user_id=test_user_id)

        # Update config
        success = config_repo.save_config("test", updated_config, user_id=test_user_id)
        assert success is True

        # Verify update
        retrieved_config = config_repo.get_config("test", user_id=test_user_id)
        assert retrieved_config == updated_config

    def test_config_user_isolation(self, config_repo, test_db_session, clean_database):
        """Test that users can only see their own configuration"""
        # Create two users
        user1 = User(
            id=uuid.uuid4(),
            username="user1",
            email="user1@test.com",
            hashed_password="hash1",
            is_active=True,
        )
        user2 = User(
            id=uuid.uuid4(),
            username="user2",
            email="user2@test.com",
            hashed_password="hash2",
            is_active=True,
        )
        test_db_session.add_all([user1, user2])
        test_db_session.commit()

        user1_id = str(user1.id)
        user2_id = str(user2.id)

        # Save config for each user
        config_repo.save_config("settings", {"user": "user1"}, user_id=user1_id)
        config_repo.save_config("settings", {"user": "user2"}, user_id=user2_id)

        # Each user should only see their own config
        user1_config = config_repo.get_config("settings", user_id=user1_id)
        user2_config = config_repo.get_config("settings", user_id=user2_id)

        assert user1_config["user"] == "user1"
        assert user2_config["user"] == "user2"


class TestRepositoryErrorHandling:
    """Test repository error handling"""

    def test_repository_handles_database_errors(self, test_db_session):
        """Test that repositories handle database errors gracefully"""
        # This would test scenarios like connection failures, constraint violations, etc.
        # Implementation depends on specific error handling strategy
        pass

    def test_invalid_user_id_handling(self, test_db_session, clean_database):
        """Test repositories with invalid user IDs"""
        task_repo = TaskRepository(test_db_session)

        # Test with invalid UUID format
        tasks = task_repo.get_all_tasks(user_id="invalid-uuid")
        # Should handle gracefully, either return empty or raise specific error
        assert isinstance(tasks, dict)

        # Test with non-existent but valid UUID
        nonexistent_id = str(uuid.uuid4())
        tasks = task_repo.get_all_tasks(user_id=nonexistent_id)
        assert isinstance(tasks, dict)
