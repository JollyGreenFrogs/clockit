#!/usr/bin/env python3
"""
Database initialization script for ClockIt deployment
This script handles:
1. Database table creation
2. Schema migrations
3. Default data seeding
4. Health checks

Run this during deployment to ensure database is properly set up.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add src directory to path first
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Database imports
from database.connection import get_db, engine, Base
from database.models import Task, Category, TimeEntry, UserConfig, Currency
from database.auth_models import User
from sqlalchemy import text

def setup_logging():
    """Configure logging for deployment"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/db_init.log')
        ]
    )
    return logging.getLogger(__name__)

def wait_for_database(max_retries=30, retry_delay=2):
    """Wait for database to be available"""
    logger = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        try:
            
            
            db = next(get_db())
            db.execute(text("SELECT 1"))
            db.close()
            logger.info("✅ Database connection successful!")
            return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("❌ Database connection failed after all retries")
                return False
    
    return False

def check_and_create_tables():
    """Check if tables exist and create them if needed"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import all models to register them (already imported at top)
        logger.info("Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        return False

def run_migrations():
    """Run any pending database migrations"""
    logger = logging.getLogger(__name__)
    
    try:
        # Check if we need to run the category structure migration
        db = next(get_db())
        
        # Check if new category columns exist
        try:
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'categories' AND column_name = 'day_rate'
            """))
            
            if not result.fetchone():
                logger.info("Running category structure migration...")
                from scripts.migrate_category_structure import migrate_category_structure
                migrate_category_structure()
                logger.info("✅ Category structure migration completed!")
            else:
                logger.info("Category structure migration already applied")
                
        except Exception as e:
            logger.warning(f"Migration check failed (this is normal for new databases): {e}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def seed_default_data():
    """Seed database with default data"""
    logger = logging.getLogger(__name__)
    
    try:
        db = next(get_db())
        
        # Check if currencies already exist
        currency_count = db.execute(text("SELECT COUNT(*) FROM currencies")).scalar()
        
        if currency_count == 0:
            logger.info("Seeding default currencies...")
            
            default_currencies = [
                {'code': 'USD', 'symbol': '$', 'name': 'US Dollar'},
                {'code': 'EUR', 'symbol': '€', 'name': 'Euro'},
                {'code': 'GBP', 'symbol': '£', 'name': 'British Pound'},
                {'code': 'CAD', 'symbol': 'C$', 'name': 'Canadian Dollar'},
                {'code': 'AUD', 'symbol': 'A$', 'name': 'Australian Dollar'},
                {'code': 'JPY', 'symbol': '¥', 'name': 'Japanese Yen'},
            ]
            
            for curr in default_currencies:
                currency = Currency(
                    code=curr['code'],
                    symbol=curr['symbol'],
                    name=curr['name'],
                    is_active=True
                )
                db.add(currency)
            
            db.commit()
            logger.info(f"✅ Seeded {len(default_currencies)} default currencies")
        else:
            logger.info("Default currencies already exist")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to seed default data: {e}")
        return False

def verify_database_health():
    """Verify database is healthy and ready"""
    logger = logging.getLogger(__name__)
    
    try:
        db = next(get_db())
        
        # Test basic operations
        tables_to_check = ['users', 'categories', 'tasks', 'time_entries', 'currencies', 'user_configs']
        
        for table in tables_to_check:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            logger.info(f"Table '{table}': {result} rows")
        
        db.close()
        logger.info("✅ Database health check passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False

def main():
    """Main initialization function"""
    logger = setup_logging()
    
    logger.info("🗄️  Starting ClockIt database initialization...")
    
    # Step 1: Wait for database to be available
    logger.info("Step 1: Waiting for database...")
    if not wait_for_database():
        logger.error("Database is not available. Exiting.")
        sys.exit(1)
    
    # Step 2: Create tables
    logger.info("Step 2: Creating database tables...")
    if not check_and_create_tables():
        logger.error("Failed to create database tables. Exiting.")
        sys.exit(1)
    
    # Step 3: Run migrations
    logger.info("Step 3: Running database migrations...")
    if not run_migrations():
        logger.error("Failed to run migrations. Exiting.")
        sys.exit(1)
    
    # Step 4: Seed default data
    logger.info("Step 4: Seeding default data...")
    if not seed_default_data():
        logger.error("Failed to seed default data. Exiting.")
        sys.exit(1)
    
    # Step 5: Health check
    logger.info("Step 5: Database health check...")
    if not verify_database_health():
        logger.error("Database health check failed. Exiting.")
        sys.exit(1)
    
    logger.info("🎉 Database initialization completed successfully!")
    
    # Print summary
    print("\n" + "="*50)
    print("ClockIt Database Initialization Complete")
    print("="*50)
    print("✅ Database tables created")
    print("✅ Migrations applied")
    print("✅ Default data seeded")
    print("✅ Health check passed")
    print("\n🚀 ClockIt is ready to serve!")

if __name__ == "__main__":
    main()