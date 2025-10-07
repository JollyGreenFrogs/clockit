"""
Test configuration and fixtures for ClockIt test suite
"""

import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import Base, get_db
from database.auth_models import User
from database.models import Task, Category, TimeEntry, UserConfig
from auth.services import AuthService
from main import app
from config import Config


@pytest.fixture(scope="session")
def test_database_url():
    """Create a test database URL - use SQLite for CI, PostgreSQL for local testing"""
    # Check if we're in CI environment or DEV_MODE is sqlite
    if os.getenv("DEV_MODE") == "sqlite" or os.getenv("ENVIRONMENT") == "test":
        # Use SQLite for CI/test environment
        test_dir = Path(tempfile.gettempdir()) / "clockit_test"
        test_dir.mkdir(exist_ok=True)
        return f"sqlite:///{test_dir}/test_clockit.db"
    else:
        # Use PostgreSQL for local testing to match production
        return "postgresql://clockit_user:tTWkfV8JEtx%5E3u@localhost:5432/clockit_test_db"


@pytest.fixture(scope="session") 
def test_engine(test_database_url):
    """Create a test database engine"""
    from sqlalchemy import text
    
    # Configure engine based on database type
    if "sqlite" in test_database_url:
        # SQLite configuration
        engine = create_engine(
            test_database_url, 
            echo=False,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL configuration
        engine = create_engine(test_database_url, echo=False)
    
    # Create test database if it doesn't exist
    try:
        # Try to connect and create tables
        Base.metadata.create_all(bind=engine)
        yield engine
    except Exception as e:
        # If database is not available, skip tests that require it
        pytest.skip(f"Test database not available: {e}")
    finally:
        # Cleanup test database
        try:
            Base.metadata.drop_all(bind=engine)
        except:
            pass


@pytest.fixture
def test_db_session(test_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_client(test_db_session):
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for file-based tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.object(Config, 'DATA_DIR', Path(temp_dir)):
            yield Path(temp_dir)


@pytest.fixture
def test_user_data():
    """Test user data for registration/login"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_user(test_db_session, test_user_data):
    """Create a test user in the database"""
    auth_service = AuthService(test_db_session)
    user = auth_service.register_user(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        full_name=test_user_data.get("full_name")
    )
    test_db_session.commit()
    return user


@pytest.fixture
def auth_tokens(test_client, test_user_data):
    """Get authentication tokens for a test user"""
    # Register user
    response = test_client.post("/auth/register", json=test_user_data)
    assert response.status_code == 200
    
    # Login to get tokens
    login_response = test_client.post("/auth/login", json={
        "email_or_username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "user_id": tokens["user"]["id"]
    }


@pytest.fixture
def authenticated_client(test_client, auth_tokens):
    """Create an authenticated test client"""
    test_client.headers.update({
        "Authorization": f"Bearer {auth_tokens['access_token']}"
    })
    return test_client


@pytest.fixture
def test_task_data():
    """Sample task data for testing"""
    return {
        "name": "Test Task",
        "description": "A task for testing",
        "category": "Development",
        "hourly_rate": 50.0
    }


@pytest.fixture
def sample_category_data():
    """Sample category data for testing"""
    return {
        "name": "Development",
        "description": "Software development tasks",
        "color": "#007bff"
    }


@pytest.fixture
def clean_database(test_db_session):
    """Clean all tables before test"""
    # Delete in correct order to avoid foreign key constraints
    test_db_session.query(TimeEntry).delete()
    test_db_session.query(Task).delete()
    test_db_session.query(Category).delete()
    test_db_session.query(UserConfig).delete()
    test_db_session.query(User).delete()
    test_db_session.commit()
    yield
    # Cleanup after test
    test_db_session.query(TimeEntry).delete()
    test_db_session.query(Task).delete()
    test_db_session.query(Category).delete()
    test_db_session.query(UserConfig).delete()
    test_db_session.query(User).delete()
    test_db_session.commit()