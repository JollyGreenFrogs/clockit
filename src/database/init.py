"""
Database initialization and migration utilities
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

# Import all models to register them with Base.metadata
from .auth_models import User  # noqa: F401
from .connection import DATABASE_URL, create_tables, engine
from .models import Category, Task, TimeEntry, UserConfig  # noqa: F401
from .repositories import CurrencyRepository

logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with tables and default data"""
    try:
        logger.info(f"Initializing database: {DATABASE_URL}")

        # Create all tables
        create_tables()
        logger.info("Database tables created successfully")

        # Add any default data if needed
        _add_default_data()

        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def _add_default_data():
    """Add default configuration and sample data - Skip for multi-tenant setup"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Initialize currencies in the database
        _initialize_currencies(db)

        # In multi-tenant setup, we don't create global default data
        # Default categories and configs will be created per-user during registration
        logger.info("Default data initialization complete")

    except Exception as e:
        logger.error(f"Failed to add default data: {e}")
        db.rollback()
    finally:
        db.close()


def _initialize_currencies(db):
    """Initialize currencies table with common currencies"""
    currency_repo = CurrencyRepository(db)

    # Common currencies - EUR and GBP first, then alphabetical
    currencies_data = [
        {"code": "EUR", "symbol": "€", "name": "Euro"},
        {"code": "GBP", "symbol": "£", "name": "British Pound"},
        {"code": "USD", "symbol": "$", "name": "US Dollar"},
        {"code": "AUD", "symbol": "A$", "name": "Australian Dollar"},
        {"code": "CAD", "symbol": "C$", "name": "Canadian Dollar"},
        {"code": "CHF", "symbol": "CHF", "name": "Swiss Franc"},
        {"code": "CNY", "symbol": "¥", "name": "Chinese Yuan"},
        {"code": "JPY", "symbol": "¥", "name": "Japanese Yen"},
        {"code": "KRW", "symbol": "₩", "name": "South Korean Won"},
        {"code": "SEK", "symbol": "kr", "name": "Swedish Krona"},
        {"code": "NOK", "symbol": "kr", "name": "Norwegian Krone"},
        {"code": "DKK", "symbol": "kr", "name": "Danish Krone"},
        {"code": "PLN", "symbol": "zł", "name": "Polish Zloty"},
        {"code": "CZK", "symbol": "Kč", "name": "Czech Koruna"},
        {"code": "HUF", "symbol": "Ft", "name": "Hungarian Forint"},
        {"code": "RUB", "symbol": "₽", "name": "Russian Ruble"},
        {"code": "BRL", "symbol": "R$", "name": "Brazilian Real"},
        {"code": "MXN", "symbol": "$", "name": "Mexican Peso"},
        {"code": "ARS", "symbol": "$", "name": "Argentine Peso"},
        {"code": "INR", "symbol": "₹", "name": "Indian Rupee"},
        {"code": "SGD", "symbol": "S$", "name": "Singapore Dollar"},
        {"code": "HKD", "symbol": "HK$", "name": "Hong Kong Dollar"},
        {"code": "NZD", "symbol": "NZ$", "name": "New Zealand Dollar"},
        {"code": "ZAR", "symbol": "R", "name": "South African Rand"},
        {"code": "TRY", "symbol": "₺", "name": "Turkish Lira"},
        {"code": "AED", "symbol": "د.إ", "name": "UAE Dirham"},
        {"code": "SAR", "symbol": "﷼", "name": "Saudi Riyal"},
        {"code": "QAR", "symbol": "﷼", "name": "Qatari Riyal"},
        {"code": "KWD", "symbol": "د.ك", "name": "Kuwaiti Dinar"},
        {"code": "BHD", "symbol": "د.ب", "name": "Bahraini Dinar"},
    ]

    try:
        currency_repo.bulk_create_currencies(currencies_data)
        logger.info(f"Initialized {len(currencies_data)} currencies in database")
    except Exception as e:
        logger.error(f"Failed to initialize currencies: {e}")
        raise


def check_database_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
