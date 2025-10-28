#!/usr/bin/env python3
"""
Database migration to restructure categories with proper hierarchy

This migration:
1. Adds rate fields to categories table
2. Adds category_id foreign key to tasks table  
3. Migrates existing data from string-based categories to proper relationships
4. Moves rate data from user_configs to categories table
"""

import sys
import os
import logging
import json
from sqlalchemy import text

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import get_db

logger = logging.getLogger(__name__)


def migrate_category_structure():
    """Migrate category structure to proper hierarchy"""
    db = next(get_db())
    
    try:
        logger.info("Starting category structure migration...")
        
        # Step 1: Add new columns to categories table
        logger.info("Adding rate columns to categories table...")
        
        # Check existing columns first
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'categories'
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        
        # Add missing columns to categories
        new_columns = {
            'day_rate': 'ALTER TABLE categories ADD COLUMN day_rate FLOAT DEFAULT 0.0',
            'hourly_rate': 'ALTER TABLE categories ADD COLUMN hourly_rate FLOAT',
            'tags': 'ALTER TABLE categories ADD COLUMN tags VARCHAR(500)',
            'is_active': 'ALTER TABLE categories ADD COLUMN is_active BOOLEAN DEFAULT TRUE',
            'is_default': 'ALTER TABLE categories ADD COLUMN is_default BOOLEAN DEFAULT FALSE',
            'updated_at': 'ALTER TABLE categories ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        for col_name, sql in new_columns.items():
            if col_name not in existing_columns:
                logger.info(f"Adding column: {col_name}")
                db.execute(text(sql))
        
        # Step 2: Create temporary category mapping and populate categories with rates
        logger.info("Migrating rate data from user_configs to categories...")
        
        # Get all users with rate configurations
        rate_configs = db.execute(text("""
            SELECT user_id, config_data 
            FROM user_configs 
            WHERE config_type = 'rates'
        """)).fetchall()
        
        category_mapping = {}  # {user_id: {category_name: category_id}}
        
        for user_id, config_data_str in rate_configs:
            if not config_data_str:
                continue
                
            try:
                rates_data = json.loads(config_data_str)
                if not isinstance(rates_data, dict):
                    continue
                    
                user_categories = {}
                
                for category_name, day_rate in rates_data.items():
                    if not category_name or not isinstance(day_rate, (int, float)):
                        continue
                    
                    # Check if category already exists for this user
                    existing = db.execute(text("""
                        SELECT id FROM categories 
                        WHERE user_id = :user_id AND name = :name
                    """), {"user_id": user_id, "name": category_name}).fetchone()
                    
                    if existing:
                        category_id = existing[0]
                        # Update existing category with rate
                        db.execute(text("""
                            UPDATE categories 
                            SET day_rate = :day_rate, hourly_rate = :hourly_rate, updated_at = CURRENT_TIMESTAMP
                            WHERE id = :id
                        """), {
                            "day_rate": float(day_rate), 
                            "hourly_rate": float(day_rate) / 8.0,
                            "id": category_id
                        })
                    else:
                        # Create new category with rate
                        result = db.execute(text("""
                            INSERT INTO categories (user_id, name, description, day_rate, hourly_rate, color, created_at, updated_at)
                            VALUES (:user_id, :name, :description, :day_rate, :hourly_rate, :color, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            RETURNING id
                        """), {
                            "user_id": user_id,
                            "name": category_name,
                            "description": f"Category migrated from rate configuration",
                            "day_rate": float(day_rate),
                            "hourly_rate": float(day_rate) / 8.0,
                            "color": "#007bff"
                        })
                        category_id = result.fetchone()[0]
                    
                    user_categories[category_name] = category_id
                
                category_mapping[str(user_id)] = user_categories
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse rate config for user {user_id}: {e}")
                continue
        
        # Step 3: Add category_id column to tasks table (if not exists)
        logger.info("Adding category_id column to tasks table...")
        
        task_columns = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tasks'
        """)).fetchall()
        task_column_names = [row[0] for row in task_columns]
        
        if 'category_id' not in task_column_names:
            db.execute(text("""
                ALTER TABLE tasks ADD COLUMN category_id INTEGER REFERENCES categories(id)
            """))
        
        if 'hourly_rate_override' not in task_column_names:
            db.execute(text("""
                ALTER TABLE tasks ADD COLUMN hourly_rate_override FLOAT
            """))
        
        if 'is_completed' not in task_column_names:
            db.execute(text("""
                ALTER TABLE tasks ADD COLUMN is_completed BOOLEAN DEFAULT FALSE
            """))
        
        # Step 4: Migrate existing tasks to use category_id
        logger.info("Migrating tasks to use category foreign keys...")
        
        tasks_to_migrate = db.execute(text("""
            SELECT id, user_id, category, hourly_rate 
            FROM tasks 
            WHERE category IS NOT NULL AND category_id IS NULL
        """)).fetchall()
        
        migrated_tasks = 0
        for task_id, user_id, category_name, hourly_rate in tasks_to_migrate:
            user_id_str = str(user_id)
            
            if user_id_str in category_mapping and category_name in category_mapping[user_id_str]:
                category_id = category_mapping[user_id_str][category_name]
                
                db.execute(text("""
                    UPDATE tasks 
                    SET category_id = :category_id, hourly_rate_override = :hourly_rate
                    WHERE id = :task_id
                """), {
                    "category_id": category_id,
                    "hourly_rate": hourly_rate,
                    "task_id": task_id
                })
                migrated_tasks += 1
            else:
                # Create missing category for this task
                logger.info(f"Creating missing category '{category_name}' for user {user_id}")
                result = db.execute(text("""
                    INSERT INTO categories (user_id, name, description, day_rate, hourly_rate, color, created_at, updated_at)
                    VALUES (:user_id, :name, :description, :day_rate, :hourly_rate, :color, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """), {
                    "user_id": user_id,
                    "name": category_name,
                    "description": "Category created from existing task",
                    "day_rate": (hourly_rate or 0) * 8,  # Estimate day rate from hourly
                    "hourly_rate": hourly_rate or 0,
                    "color": "#6c757d"  # Gray for auto-created categories
                })
                category_id = result.fetchone()[0]
                
                db.execute(text("""
                    UPDATE tasks 
                    SET category_id = :category_id, hourly_rate_override = :hourly_rate
                    WHERE id = :task_id
                """), {
                    "category_id": category_id,
                    "hourly_rate": hourly_rate,
                    "task_id": task_id
                })
                migrated_tasks += 1
        
        logger.info(f"Migrated {migrated_tasks} tasks to use category foreign keys")
        
        # Step 5: Set default categories
        logger.info("Setting default categories based on user preferences...")
        
        users_with_defaults = db.execute(text("""
            SELECT id, default_category FROM users 
            WHERE default_category IS NOT NULL
        """)).fetchall()
        
        for user_id, default_category_name in users_with_defaults:
            db.execute(text("""
                UPDATE categories 
                SET is_default = TRUE 
                WHERE user_id = :user_id AND name = :name
            """), {"user_id": user_id, "name": default_category_name})
        
        db.commit()
        logger.info("Category structure migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🔄 Starting category structure migration...")
    try:
        success = migrate_category_structure()
        if success:
            print("✅ Category structure migration completed successfully!")
            print("\n📋 Summary of changes:")
            print("  • Added rate fields to categories table")
            print("  • Added category_id foreign key to tasks table") 
            print("  • Migrated rate data from user_configs to categories")
            print("  • Updated tasks to reference categories by ID")
            print("  • Set default categories based on user preferences")
        else:
            print("❌ Migration failed!")
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        sys.exit(1)