"""
Database connection and session management
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()


# Build database URL from environment variables
def get_database_url():
    """Build database URL from environment variables"""
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "clockit_db")
    db_user = os.getenv("POSTGRES_USER", "clockit_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "")

    if db_password:
        # URL encode the password to handle special characters
        encoded_password = quote_plus(db_password)
        return (
            f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
        )
    else:
        return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"


# Database URL - can be overridden by environment variable
DATABASE_URL = os.getenv("DATABASE_URL") or get_database_url()

# For development, allow SQLite fallback
if os.getenv("DEV_MODE") == "sqlite":
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite:///{data_dir}/clockit.db"

engine = create_engine(
    DATABASE_URL,
    # Connection pool settings to prevent timeouts
    pool_size=20,  # Base number of connections to keep open
    max_overflow=30,  # Additional connections allowed
    pool_timeout=30,  # Time to wait for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Validate connections before use
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
