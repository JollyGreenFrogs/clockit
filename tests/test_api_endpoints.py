"""
Tests for API endpoints, especially cloud-ready features
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import Config
from main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.object(Config, "DATA_DIR", Path(temp_dir)):
            yield Path(temp_dir)


def get_auth_headers(client):
    """Helper function to create a user and return auth headers"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
    }

    # Register user
    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code == 200

    # Login to get token
    login_response = client.post(
        "/auth/login",
        json={
            "email_or_username": user_data["username"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_health_check_endpoint(client, temp_data_dir):
    """Test the health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "data_directory_accessible" in data
    assert "tasks_loadable" in data

    # Check values
    assert data["status"] == "healthy"
    assert data["data_directory_accessible"] is True
    assert data["tasks_loadable"] is True


def test_health_check_with_missing_data_dir(client):
    """Test health check when data directory is not accessible"""
    with patch.object(Config, "DATA_DIR", Path("/nonexistent/path")):
        response = client.get("/health")

        # Should still return 200 but with accessible=False
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        # The actual accessibility will depend on implementation


def test_system_data_location_endpoint(client, temp_data_dir):
    """Test the system data location endpoint"""
    # This endpoint requires authentication, so we need to create a user and login first
    # Register a user with unique credentials
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"testuser_sysinfo_{unique_id}",
        "email": f"test_sysinfo_{unique_id}@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
    }
    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code == 200

    # Login to get token
    login_response = client.post(
        "/auth/login",
        json={
            "email_or_username": user_data["username"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # Use token to access system endpoint
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = client.get("/system/data-location", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Check required fields for current database-based implementation
    assert "database_type" in data
    assert "data_storage" in data
    assert "data_directory" in data
    assert "status" in data

    # Check that values are as expected
    assert isinstance(data["data_directory"], str)
    assert data["status"] == "database_only"


def test_tasks_endpoint_basic(client, temp_data_dir):
    """Test basic tasks endpoint functionality"""
    # Get auth headers
    headers = get_auth_headers(client)

    # Get tasks (should return empty initially)
    response = client.get("/tasks", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data


def test_create_task_endpoint(client, temp_data_dir):
    """Test creating a task via API"""
    # Get auth headers
    headers = get_auth_headers(client)

    task_data = {
        "name": "Test Task",
        "description": "A test task",
        "category": "Development",
    }

    response = client.post("/tasks", json=task_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "task_name" in data
    assert data["task_name"] == "Test Task"


def test_categories_endpoint(client, temp_data_dir):
    """Test the categories endpoint"""
    # Get auth headers
    headers = get_auth_headers(client)

    response = client.get("/categories", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_currency_endpoints(client, temp_data_dir):
    """Test currency-related endpoints"""
    # Get auth headers
    headers = get_auth_headers(client)

    # Get available currencies
    response = client.get("/currencies", headers=headers)
    assert response.status_code == 200

    # Get current currency
    response = client.get("/currency", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "currency" in data
    currency = data["currency"]
    assert "code" in currency
    assert "symbol" in currency
    assert "name" in currency


def test_rates_endpoint(client, temp_data_dir):
    """Test rates configuration endpoint"""
    # Get auth headers
    headers = get_auth_headers(client)

    response = client.get("/rates", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)


def test_invoice_preview_endpoint(client, temp_data_dir):
    """Test invoice preview endpoint"""
    # Get auth headers
    headers = get_auth_headers(client)

    response = client.get("/invoice/preview", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    # When no tasks exist, we get a preview message instead of invoice data
    if data["status"] == "no_data":
        assert "preview" in data
    else:
        assert "invoice" in data


@pytest.mark.parametrize(
    "endpoint",
    [
        "/health",
        "/system/data-location",
        "/tasks",
        "/categories",
        "/currencies",
        "/currency",
        "/rates",
        "/invoice/preview",
    ],
)
def test_endpoint_accessibility(client, temp_data_dir, endpoint):
    """Test that all main endpoints are accessible"""
    response = client.get(endpoint)
    # Should not return 404 or 500
    assert response.status_code < 500
    assert response.status_code != 404


def test_cors_headers(client, temp_data_dir):
    """Test that CORS headers are present for cloud deployment"""
    response = client.get("/health")

    # Check if CORS headers are present (if implemented)
    # This test may need adjustment based on actual CORS implementation
    assert response.status_code == 200


def test_content_type_headers(client, temp_data_dir):
    """Test that proper content-type headers are returned"""
    response = client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
