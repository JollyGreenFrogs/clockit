"""
Database migration to add onboarding fields to existing User table
"""

import sys
import os
import logging
from sqlalchemy import text

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import get_db

logger = logging.getLogger(__name__)


def run_onboarding_migration():
    """Add onboarding fields to the users table"""
    db = next(get_db())
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('onboarding_completed', 'default_category')
        """))
        
        existing_columns = [row[0] for row in result.fetchall()]
        
        # Add onboarding_completed column if it doesn't exist
        if 'onboarding_completed' not in existing_columns:
            logger.info("Adding onboarding_completed column to users table")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE
            """))
            
        # Add default_category column if it doesn't exist
        if 'default_category' not in existing_columns:
            logger.info("Adding default_category column to users table")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN default_category VARCHAR(100) NULL
            """))
            
        db.commit()
        logger.info("Onboarding migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Onboarding migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("Running onboarding migration...")
    success = run_onboarding_migration()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed. Check logs for details.")