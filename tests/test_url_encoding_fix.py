"""
Test URL encoding fix for task names with special characters

This test suite specifically tests the fix for GitHub issue #6:
- Task names with forward slashes (/) causing 404 errors
- URL encoding/decoding of task names in API endpoints
- Proper handling of special characters in task operations
"""

import pytest
import urllib.parse
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from database.auth_models import User


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock authenticated user"""
    user = MagicMock(spec=User)
    user.id = "00000000-0000-0000-0000-000000000001"
    user.username = "test_user"
    user.email = "test@example.com"
    return user


@pytest.fixture
def authenticated_client(client, mock_user):
    """Create a client with mocked authentication"""
    
    def mock_get_current_user():
        return mock_user
    
    # Patch the get_current_user dependency
    app.dependency_overrides = {}
    from auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


class TestURLEncodingFix:
    """Test suite for URL encoding fix"""
    
    @pytest.mark.parametrize("task_name,expected_encoded", [
        ("General IT/Tech work", "General%20IT/Tech%20work"),
        ("Project A/B Testing", "Project%20A/B%20Testing"),
        ("Client/Server Development", "Client/Server%20Development"),
        ("UI/UX Design", "UI/UX%20Design"),
        ("Data Analysis & Reports", "Data%20Analysis%20%26%20Reports"),
        ("Meeting (Project #1)", "Meeting%20(Project%20%231)"),
    ])
    def test_url_encoding_scenarios(self, task_name, expected_encoded):
        """Test that various task names are properly URL encoded"""
        encoded = urllib.parse.quote(task_name)
        assert encoded == expected_encoded
        
        # Test round-trip encoding/decoding
        decoded = urllib.parse.unquote(encoded)
        assert decoded == task_name
    
    
    @patch('business.task_manager.TaskManager.create_task_for_user')
    def test_create_task_with_special_characters(self, mock_create, authenticated_client):
        """Test creating tasks with special characters in names"""
        mock_create.return_value = True
        
        task_data = {
            "name": "General IT/Tech work",
            "description": "IT and technical work tasks"
        }
        
        response = authenticated_client.post("/tasks", json=task_data)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Task created successfully"
        assert response.json()["task_name"] == "General IT/Tech work"
        
        # Verify the task manager was called with correct parameters
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]['name'] == "General IT/Tech work"
    
    
    @patch('business.task_manager.TaskManager.add_time_entry')
    def test_add_time_entry_with_url_encoded_task_name(self, mock_add_time, authenticated_client):
        """Test adding time entries to tasks with URL-encoded names"""
        mock_add_time.return_value = True
        
        # Simulate the frontend sending URL-encoded task name
        task_name = "General IT/Tech work"
        url_encoded_name = urllib.parse.quote(task_name)
        
        time_entry_data = {
            "task_id": task_name,  # Frontend sends original name in body
            "hours": 2.5,
            "date": "2025-10-06",
            "description": "Working on server configuration"
        }
        
        # The URL path will be URL encoded by the client
        response = authenticated_client.post(
            f"/tasks/{url_encoded_name}/time", 
            json=time_entry_data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Time entry added successfully"
        assert response_data["task_name"] == task_name  # Should be decoded
        
        # Verify the task manager received the decoded task name
        mock_add_time.assert_called_once()
        call_args = mock_add_time.call_args
        assert call_args[1]['task_name'] == task_name  # Decoded name
        assert call_args[1]['duration'] == 2.5
    
    
    @patch('business.task_manager.TaskManager.add_time_entry')
    def test_add_time_entry_task_not_found(self, mock_add_time, authenticated_client):
        """Test handling when task is not found"""
        mock_add_time.return_value = False  # Simulate task not found
        
        task_name = "Nonexistent Task/Work"
        url_encoded_name = urllib.parse.quote(task_name)
        
        time_entry_data = {
            "task_id": task_name,
            "hours": 1.0,
            "date": "2025-10-06",
            "description": "Test entry"
        }
        
        response = authenticated_client.post(
            f"/tasks/{url_encoded_name}/time", 
            json=time_entry_data
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    
    @patch('business.task_manager.TaskManager.delete_task')
    def test_delete_task_with_url_encoded_name(self, mock_delete, authenticated_client):
        """Test deleting tasks with URL-encoded names"""
        mock_delete.return_value = True
        
        task_name = "Old Project/Legacy Code"
        url_encoded_name = urllib.parse.quote(task_name)
        
        response = authenticated_client.delete(f"/tasks/{url_encoded_name}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Task deleted successfully"
        assert response_data["task_name"] == task_name  # Should be decoded
        
        # Verify the task manager received the decoded task name
        mock_delete.assert_called_once()
        call_args = mock_delete.call_args
        assert call_args[1]['task_name'] == task_name  # Decoded name
    
    
    @patch('business.task_manager.TaskManager.delete_task')
    def test_delete_nonexistent_task(self, mock_delete, authenticated_client):
        """Test deleting a task that doesn't exist"""
        mock_delete.return_value = False
        
        task_name = "Nonexistent/Task"
        url_encoded_name = urllib.parse.quote(task_name)
        
        response = authenticated_client.delete(f"/tasks/{url_encoded_name}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    
    def test_url_decoding_edge_cases(self):
        """Test edge cases in URL encoding/decoding"""
        test_cases = [
            ("Task with spaces", "Task%20with%20spaces"),
            ("Task/with/multiple/slashes", "Task/with/multiple/slashes"),
            ("Task%20already%20encoded", "Task%2520already%2520encoded"),
            ("Task+with+plus", "Task%2Bwith%2Bplus"),
            ("Task&with&ampersand", "Task%26with%26ampersand"),
            ("Task#with#hash", "Task%23with%23hash"),
        ]
        
        for original, expected_encoded in test_cases:
            # Test encoding
            encoded = urllib.parse.quote(original)
            assert encoded == expected_encoded, f"Encoding failed for '{original}'"
            
            # Test decoding
            decoded = urllib.parse.unquote(encoded)
            assert decoded == original, f"Decoding failed for '{encoded}'"
    
    
    @patch('business.task_manager.TaskManager.add_time_entry')
    def test_complex_task_name_scenarios(self, mock_add_time, authenticated_client):
        """Test complex real-world task name scenarios"""
        mock_add_time.return_value = True
        
        complex_task_names = [
            "Client Work/ABC Corp/Q4 2025",
            "Development/Frontend/React Components",
            "Meeting/Project Planning & Review",
            "Research/AI & Machine Learning",
            "Bug Fix/Issue #123 (Critical)",
        ]
        
        for task_name in complex_task_names:
            url_encoded_name = urllib.parse.quote(task_name)
            
            time_entry_data = {
                "task_id": task_name,
                "hours": 1.5,
                "date": "2025-10-06",
                "description": f"Working on {task_name}"
            }
            
            response = authenticated_client.post(
                f"/tasks/{url_encoded_name}/time", 
                json=time_entry_data
            )
            
            assert response.status_code == 200, f"Failed for task: {task_name}"
            assert response.json()["task_name"] == task_name
        
        # Verify all calls were made with decoded names
        assert mock_add_time.call_count == len(complex_task_names)


class TestURLEncodingIntegration:
    """Integration tests for URL encoding fix"""
    
    @patch('business.task_manager.TaskManager.load_tasks_for_user')
    @patch('business.task_manager.TaskManager.add_time_entry')
    def test_end_to_end_task_workflow(self, mock_add_time, mock_load_tasks, authenticated_client):
        """Test complete workflow: create task, add time, verify"""
        # Mock task exists in database
        task_name = "Integration Test/Full Workflow"
        mock_load_tasks.return_value = {"tasks": {task_name: 5.0}}
        mock_add_time.return_value = True
        
        # Step 1: Verify task exists (GET /tasks)
        response = authenticated_client.get("/tasks")
        assert response.status_code == 200
        
        # Step 2: Add time entry with URL-encoded name
        url_encoded_name = urllib.parse.quote(task_name)
        time_entry_data = {
            "task_id": task_name,
            "hours": 2.0,
            "date": "2025-10-06",
            "description": "Integration testing"
        }
        
        response = authenticated_client.post(
            f"/tasks/{url_encoded_name}/time",
            json=time_entry_data
        )
        
        assert response.status_code == 200
        assert response.json()["task_name"] == task_name
        
        # Verify the backend received decoded task name
        mock_add_time.assert_called_once()
        call_args = mock_add_time.call_args
        assert call_args[1]['task_name'] == task_name


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])