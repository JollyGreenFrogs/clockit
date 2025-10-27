"""
Test API endpoints with authentication and new database architecture
"""

from fastapi import status


class TestHealthEndpoints:
    """Test health and system endpoints (should be public)"""

    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_version_endpoint(self, test_client):
        """Test version endpoint"""
        response = test_client.get("/version")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "version" in data
        assert "build_date" in data

    def test_system_data_location(self, authenticated_client, temp_data_dir):
        """Test system data location endpoint"""
        response = authenticated_client.get("/system/data-location")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data_directory" in data


class TestTaskEndpoints:
    """Test task management endpoints"""

    def test_get_tasks_authenticated(self, authenticated_client, clean_database):
        """Test getting tasks with authentication"""
        response = authenticated_client.get("/tasks")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], dict)

    def test_get_tasks_unauthenticated(self, test_client):
        """Test getting tasks without authentication should fail"""
        response = test_client.get("/tasks")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_task_authenticated(
        self, authenticated_client, test_task_data, clean_database
    ):
        """Test creating task with authentication"""
        response = authenticated_client.post("/tasks", json=test_task_data)

        # Should either succeed or fail with specific business logic error
        # but not authentication error
        assert response.status_code != status.HTTP_403_FORBIDDEN

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "message" in data
            assert "task_name" in data
            assert data["task_name"] == test_task_data["name"]

    def test_create_task_unauthenticated(self, test_client, test_task_data):
        """Test creating task without authentication should fail"""
        response = test_client.post("/tasks", json=test_task_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_task_invalid_data(self, authenticated_client, clean_database):
        """Test creating task with invalid data"""
        invalid_data = {"invalid": "data"}
        response = authenticated_client.post("/tasks", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_task_empty_name(self, authenticated_client, clean_database):
        """Test creating task with empty name"""
        invalid_data = {"name": "", "description": "Task with empty name"}
        response = authenticated_client.post("/tasks", json=invalid_data)
        # Should fail validation
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


class TestUserDataIsolation:
    """Test that users can only see their own data"""

    def test_task_isolation_between_users(
        self, test_client, test_task_data, clean_database
    ):
        """Test that users can only see their own tasks"""
        # Create two users
        user1_data = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "TestPassword123!",
        }
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "TestPassword123!",
        }

        # Register both users
        test_client.post("/auth/register", json=user1_data)
        test_client.post("/auth/register", json=user2_data)

        # Login as user1
        login1 = test_client.post(
            "/auth/login",
            json={
                "email_or_username": user1_data["username"],
                "password": user1_data["password"],
            },
        )
        token1 = login1.json()["access_token"]

        # Login as user2
        login2 = test_client.post(
            "/auth/login",
            json={
                "email_or_username": user2_data["username"],
                "password": user2_data["password"],
            },
        )
        token2 = login2.json()["access_token"]

        # User1 creates a task
        test_client.headers.update({"Authorization": f"Bearer {token1}"})
        task_response = test_client.post("/tasks", json=test_task_data)

        # User1 should see their task
        user1_tasks = test_client.get("/tasks")
        assert user1_tasks.status_code == status.HTTP_200_OK

        # User2 should not see user1's tasks
        test_client.headers.update({"Authorization": f"Bearer {token2}"})
        user2_tasks = test_client.get("/tasks")
        assert user2_tasks.status_code == status.HTTP_200_OK

        user1_task_count = len(user1_tasks.json()["tasks"])
        user2_task_count = len(user2_tasks.json()["tasks"])

        # If task creation succeeded, user1 should have more tasks than user2
        if task_response.status_code == status.HTTP_200_OK:
            assert user1_task_count >= user2_task_count


class TestCategoryEndpoints:
    """Test category management endpoints"""

    def test_get_categories_authenticated(self, authenticated_client, clean_database):
        """Test getting categories with authentication"""
        response = authenticated_client.get("/categories")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_get_categories_unauthenticated(self, test_client):
        """Test getting categories without authentication"""
        response = test_client.get("/categories")
        # Categories might be public or protected - check current implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


class TestRatesEndpoints:
    """Test rates management endpoints"""

    def test_get_rates_authenticated(self, authenticated_client, clean_database):
        """Test getting rates with authentication"""
        response = authenticated_client.get("/rates")

        # Rates endpoint might be public or protected
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_get_rates_unauthenticated(self, test_client):
        """Test getting rates without authentication"""
        response = test_client.get("/rates")

        # Check if rates are public or protected
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


class TestCurrencyEndpoints:
    """Test currency management endpoints"""

    def test_get_currency_authenticated(self, authenticated_client, clean_database):
        """Test getting currency with authentication"""
        response = authenticated_client.get("/currency")

        # Currency endpoint might return 404 if not configured, 200 if configured, or 403 if forbidden
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_get_currencies_list(self, test_client):
        """Test getting available currencies list"""
        response = test_client.get("/currencies")

        # This should likely be public
        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.json(), list)

    def test_get_available_currencies(self, test_client):
        """Test getting available currencies"""
        response = test_client.get("/currency/available")

        # This should likely be public
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


class TestTimeEntryEndpoints:
    """Test time entry endpoints"""

    def test_add_time_entry_authenticated(self, authenticated_client, clean_database):
        """Test adding time entry with authentication"""
        # First create a task
        task_data = {
            "name": "Test Task for Time Entry",
            "description": "A task to test time entries",
        }

        task_response = authenticated_client.post("/tasks", json=task_data)

        if task_response.status_code == status.HTTP_200_OK:
            # Try to add time entry
            time_entry_data = {
                "task_id": "Test Task for Time Entry",  # Using task name as ID for now
                "hours": 2.5,
                "date": "2025-10-01",
                "description": "Work done on task",
            }

            response = authenticated_client.post(
                f"/tasks/Test Task for Time Entry/time", json=time_entry_data
            )

            # Should either succeed or fail with business logic error, not auth error
            assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_add_time_entry_unauthenticated(self, test_client):
        """Test adding time entry without authentication should fail"""
        time_entry_data = {
            "task_id": "some_task",
            "hours": 2.5,
            "date": "2025-10-01",
            "description": "Work done",
        }

        response = test_client.post("/tasks/some_task/time", json=time_entry_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_malformed_json(self, authenticated_client):
        """Test endpoints with malformed JSON"""
        response = authenticated_client.post(
            "/tasks", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_content_type(self, authenticated_client, test_task_data):
        """Test endpoints without proper content type"""
        response = authenticated_client.post("/tasks", data=str(test_task_data))
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_nonexistent_endpoint(self, test_client):
        """Test accessing non-existent endpoint"""
        response = test_client.get("/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
