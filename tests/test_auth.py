"""
Test authentication functionality
"""

import pytest
from fastapi import status


class TestUserRegistration:
    """Test user registration functionality"""

    def test_register_new_user(self, test_client, test_user_data, clean_database):
        """Test successful user registration"""
        response = test_client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "id" in data
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert "password" not in data  # Password should not be returned

    def test_register_duplicate_username(
        self, test_client, test_user_data, clean_database
    ):
        """Test registration with duplicate username"""
        # Register first user
        response1 = test_client.post("/auth/register", json=test_user_data)
        assert response1.status_code == status.HTTP_200_OK

        # Try to register with same username
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"

        response2 = test_client.post("/auth/register", json=duplicate_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "username already exists" in response2.json()["detail"].lower()

    def test_register_duplicate_email(
        self, test_client, test_user_data, clean_database
    ):
        """Test registration with duplicate email"""
        # Register first user
        response1 = test_client.post("/auth/register", json=test_user_data)
        assert response1.status_code == status.HTTP_200_OK

        # Try to register with same email
        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "differentuser"

        response2 = test_client.post("/auth/register", json=duplicate_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already exists" in response2.json()["detail"].lower()

    def test_register_invalid_email(self, test_client, clean_database):
        """Test registration with invalid email"""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpass123",
        }

        response = test_client.post("/auth/register", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, test_client, clean_database):
        """Test registration with weak password"""
        weak_password_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",  # Too short
        }

        response = test_client.post("/auth/register", json=weak_password_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUserLogin:
    """Test user login functionality"""

    def test_login_with_username(self, test_client, test_user, test_user_data):
        """Test successful login with username"""
        response = test_client.post(
            "/auth/login",
            json={
                "email_or_username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"]

    def test_login_with_email(self, test_client, test_user, test_user_data):
        """Test successful login with email"""
        response = test_client.post(
            "/auth/login",
            json={
                "email_or_username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data

    def test_login_invalid_credentials(self, test_client, test_user, test_user_data):
        """Test login with invalid password"""
        response = test_client.post(
            "/auth/login",
            json={
                "email_or_username": test_user_data["username"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, test_client, clean_database):
        """Test login with non-existent user"""
        response = test_client.post(
            "/auth/login",
            json={"email_or_username": "nonexistent", "password": "password123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProtectedEndpoints:
    """Test protected endpoint access"""

    def test_access_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without authentication"""
        response = test_client.get("/tasks")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_protected_endpoint_with_token(self, authenticated_client):
        """Test accessing protected endpoint with valid token"""
        response = authenticated_client.get("/tasks")
        assert response.status_code == status.HTTP_200_OK
        assert "tasks" in response.json()

    def test_access_protected_endpoint_invalid_token(self, test_client):
        """Test accessing protected endpoint with invalid token"""
        test_client.headers.update({"Authorization": "Bearer invalid_token"})
        response = test_client.get("/tasks")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_task_without_auth(self, test_client, test_task_data):
        """Test creating task without authentication"""
        response = test_client.post("/tasks", json=test_task_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_task_with_auth(self, authenticated_client, test_task_data):
        """Test creating task with authentication"""
        response = authenticated_client.post("/tasks", json=test_task_data)
        # Should succeed or return specific error, but not auth error
        assert response.status_code != status.HTTP_403_FORBIDDEN


class TestTokenRefresh:
    """Test token refresh functionality"""

    def test_refresh_token(self, test_client, auth_tokens):
        """Test refreshing access token"""
        response = test_client.post(
            "/auth/refresh", json={"refresh_token": auth_tokens["refresh_token"]}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, test_client):
        """Test refresh with invalid token"""
        response = test_client.post(
            "/auth/refresh", json={"refresh_token": "invalid_refresh_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserProfile:
    """Test user profile endpoints"""

    def test_get_current_user(self, authenticated_client, test_user_data):
        """Test getting current user profile"""
        response = authenticated_client.get("/auth/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]

    def test_get_current_user_without_auth(self, test_client):
        """Test getting current user without authentication"""
        response = test_client.get("/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserLogout:
    """Test user logout functionality"""

    def test_logout(self, authenticated_client):
        """Test user logout"""
        response = authenticated_client.post("/auth/logout")
        assert response.status_code == status.HTTP_200_OK

        # Token should be invalidated (if logout invalidates tokens)
        # This depends on implementation

    def test_logout_without_auth(self, test_client):
        """Test logout without authentication"""
        response = test_client.post("/auth/logout")
        assert response.status_code == status.HTTP_403_FORBIDDEN
