"""
Simple test configuration using SQLite for basic testing
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import Config
from database.connection import get_db
from main import app

# Create simplified SQLite-compatible models for testing
TestBase = declarative_base()


class SimpleUser(TestBase):
    """Simplified User model for SQLite testing"""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class SimpleTask(TestBase):
    """Simplified Task model for SQLite testing"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    time_spent = Column(Float, default=0.0)
    hourly_rate = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


@pytest.fixture(scope="session")
def simple_test_engine():
    """Create a simple SQLite test engine"""
    engine = create_engine(
        "sqlite:///./simple_test.db", connect_args={"check_same_thread": False}
    )
    TestBase.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    try:
        os.remove("./simple_test.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def simple_test_session(simple_test_engine):
    """Create a simple test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=simple_test_engine
    )
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def simple_test_client(simple_test_session):
    """Create a test client with simple database"""

    def override_get_db():
        try:
            yield simple_test_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def simple_clean_db(simple_test_session):
    """Clean simple database before test"""
    simple_test_session.query(SimpleTask).delete()
    simple_test_session.query(SimpleUser).delete()
    simple_test_session.commit()
    yield
    simple_test_session.query(SimpleTask).delete()
    simple_test_session.query(SimpleUser).delete()
    simple_test_session.commit()
