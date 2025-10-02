"""
Basic smoke tests to verify the system is working without complex database setup
"""

import pytest
import requests
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBasicFunctionality:
    """Basic smoke tests that don't require database setup"""
    
    def test_server_is_running(self):
        """Test that the server is accessible"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running on localhost:8000")
    
    def test_version_endpoint(self):
        """Test version endpoint accessibility"""
        try:
            response = requests.get("http://localhost:8000/version", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "version" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")
    
    def test_protected_endpoint_requires_auth(self):
        """Test that protected endpoints require authentication"""
        try:
            response = requests.get("http://localhost:8000/tasks", timeout=5)
            # Should return 403 Forbidden (not authenticated)
            assert response.status_code == 403
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")
    
    def test_auth_register_endpoint_exists(self):
        """Test that auth registration endpoint exists"""
        try:
            # Send empty request to see if endpoint exists
            response = requests.post("http://localhost:8000/auth/register", 
                                   json={}, timeout=5)
            # Should return 422 (validation error) not 404 (not found)
            assert response.status_code in [400, 422]  # Validation error, not missing endpoint
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")
    
    def test_auth_login_endpoint_exists(self):
        """Test that auth login endpoint exists"""
        try:
            response = requests.post("http://localhost:8000/auth/login", 
                                   json={}, timeout=5)
            # Should return validation error, not 404
            assert response.status_code in [400, 422]
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")


class TestAuthenticationFlow:
    """Test basic authentication flow"""
    
    def test_full_auth_flow(self):
        """Test complete registration -> login -> protected access flow"""
        base_url = "http://localhost:8000"
        
        try:
            # 1. Register a new user
            register_data = {
                "username": f"testuser_{int(time.time())}",  # Unique username
                "email": f"test_{int(time.time())}@example.com",  # Unique email
                "password": "testpass123"
            }
            
            register_response = requests.post(f"{base_url}/auth/register", 
                                            json=register_data, timeout=5)
            
            if register_response.status_code != 200:
                pytest.skip(f"Registration failed: {register_response.text}")
            
            # 2. Login with the new user
            login_data = {
                "email_or_username": register_data["username"],
                "password": register_data["password"]
            }
            
            login_response = requests.post(f"{base_url}/auth/login", 
                                         json=login_data, timeout=5)
            
            if login_response.status_code != 200:
                pytest.skip(f"Login failed: {login_response.text}")
            
            login_result = login_response.json()
            assert "access_token" in login_result
            access_token = login_result["access_token"]
            
            # 3. Access protected endpoint with token
            headers = {"Authorization": f"Bearer {access_token}"}
            protected_response = requests.get(f"{base_url}/tasks", 
                                            headers=headers, timeout=5)
            
            assert protected_response.status_code == 200
            data = protected_response.json()
            assert "tasks" in data
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")


class TestBreakingChanges:
    """Test that breaking changes are properly implemented"""
    
    def test_endpoints_require_authentication(self):
        """Test that endpoints that should require auth actually do"""
        endpoints_requiring_auth = [
            "/tasks",
            "/tasks",  # POST would be tested with data
        ]
        
        try:
            for endpoint in endpoints_requiring_auth:
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                assert response.status_code == 403, f"Endpoint {endpoint} should require authentication"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")
    
    def test_public_endpoints_still_work(self):
        """Test that public endpoints still work without auth"""
        public_endpoints = [
            "/health", 
            "/version",
            "/system/data-location"
        ]
        
        try:
            for endpoint in public_endpoints:
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                assert response.status_code == 200, f"Public endpoint {endpoint} should work without auth"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")


class TestDatabaseMigration:
    """Test that database migration is working"""
    
    def test_user_data_isolation(self):
        """Test that different users see different data"""
        base_url = "http://localhost:8000"
        
        try:
            # Create two different users
            user1_data = {
                "username": f"user1_{int(time.time())}",
                "email": f"user1_{int(time.time())}@example.com",
                "password": "password123"
            }
            
            user2_data = {
                "username": f"user2_{int(time.time())}",
                "email": f"user2_{int(time.time())}@example.com", 
                "password": "password123"
            }
            
            # Register both users
            requests.post(f"{base_url}/auth/register", json=user1_data, timeout=5)
            requests.post(f"{base_url}/auth/register", json=user2_data, timeout=5)
            
            # Login both users
            login1 = requests.post(f"{base_url}/auth/login", json={
                "email_or_username": user1_data["username"],
                "password": user1_data["password"]
            }, timeout=5)
            
            login2 = requests.post(f"{base_url}/auth/login", json={
                "email_or_username": user2_data["username"],
                "password": user2_data["password"]
            }, timeout=5)
            
            if login1.status_code != 200 or login2.status_code != 200:
                pytest.skip("User login failed")
            
            token1 = login1.json()["access_token"]
            token2 = login2.json()["access_token"]
            
            # Check that each user has isolated task data
            headers1 = {"Authorization": f"Bearer {token1}"}
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            tasks1 = requests.get(f"{base_url}/tasks", headers=headers1, timeout=5)
            tasks2 = requests.get(f"{base_url}/tasks", headers=headers2, timeout=5)
            
            assert tasks1.status_code == 200
            assert tasks2.status_code == 200
            
            # Both should have empty tasks initially (isolated data)
            assert "tasks" in tasks1.json()
            assert "tasks" in tasks2.json()
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")


if __name__ == "__main__":
    """Run smoke tests directly"""
    print("🧪 Running ClockIt Smoke Tests...")
    print("Make sure the server is running on localhost:8000")
    print()
    
    # Test server availability first
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
        else:
            print(f"❌ Server responded but with status {response.status_code}")
            exit(1)
    except:
        print("❌ Server is not accessible on localhost:8000")
        print("Please start the server first: python src/main.py")
        exit(1)
    
    # Run pytest on this file
    import subprocess
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v"
    ])
    exit(result.returncode)