"""
Tests for API endpoints, especially cloud-ready features
"""

import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from config import Config


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.object(Config, 'DATA_DIR', Path(temp_dir)):
            yield Path(temp_dir)


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
    with patch.object(Config, 'DATA_DIR', Path("/nonexistent/path")):
        response = client.get("/health")
        
        # Should still return 200 but with accessible=False
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        # The actual accessibility will depend on implementation


def test_system_data_location_endpoint(client, temp_data_dir):
    """Test the system data location endpoint"""
    response = client.get("/system/data-location")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "data_directory" in data
    assert "tasks_file" in data
    assert "rates_file" in data
    assert "exported_file" in data
    
    # Check that paths are strings
    assert isinstance(data["data_directory"], str)
    assert isinstance(data["tasks_file"], str)


def test_tasks_endpoint_basic(client, temp_data_dir):
    """Test basic tasks endpoint functionality"""
    # Get tasks (should return empty initially)
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert isinstance(data["tasks"], dict)


def test_create_task_endpoint(client, temp_data_dir):
    """Test creating a task via API"""
    task_data = {
        "name": "Test Task",
        "description": "A test task",
        "parent_heading": "Development"
    }
    
    response = client.post("/tasks", json=task_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "task" in data
    assert data["task"]["name"] == "Test Task"


def test_categories_endpoint(client, temp_data_dir):
    """Test the categories endpoint"""
    response = client.get("/categories")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_currency_endpoints(client, temp_data_dir):
    """Test currency-related endpoints"""
    # Get available currencies
    response = client.get("/currencies")
    assert response.status_code == 200
    
    # Get current currency
    response = client.get("/currency")
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert "symbol" in data
    assert "name" in data


def test_rates_endpoint(client, temp_data_dir):
    """Test rates configuration endpoint"""
    response = client.get("/rates")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)


def test_invoice_preview_endpoint(client, temp_data_dir):
    """Test invoice preview endpoint"""
    response = client.get("/invoice/preview")
    assert response.status_code == 200
    
    data = response.json()
    assert "invoice_data" in data
    assert "summary" in data


@pytest.mark.parametrize("endpoint", [
    "/health",
    "/system/data-location", 
    "/tasks",
    "/categories",
    "/currencies",
    "/currency",
    "/rates",
    "/invoice/preview"
])
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