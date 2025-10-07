"""
Configuration management for ClockIt application.
Handles environment-based configuration for cloud deployment.
"""

import os
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration management"""
    
    # Environment settings
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '8000'))
    
    # Data storage
    DATA_DIR = Path(os.environ.get('CLOCKIT_DATA_DIR', './clockit_data'))
    
    # Database configuration (for future cloud deployment)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'file')  # 'file' or 'postgres'
    
    # PostgreSQL specific settings (when DATABASE_TYPE='postgres')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', '5432'))
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'clockit')
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'clockit')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    
    # Authentication (for future implementation)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'test-secret-key-for-development-only')
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '24'))
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    BCRYPT_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', '12'))
    

    MS_TENANT_ID = os.environ.get('MS_TENANT_ID')
    MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID')
    MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # CORS configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    ALLOWED_ORIGINS = CORS_ORIGINS  # Alias for CORS_ORIGINS.upper()
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json' if ENVIRONMENT == 'production' else 'text')
    
    # Cloud-specific settings
    CLOUD_PROVIDER = os.environ.get('CLOUD_PROVIDER')  # 'aws', 'gcp', 'azure', None
    REDIS_URL = os.environ.get('REDIS_URL')  # For session storage/caching
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration and log warnings for missing required settings"""
        valid = True
        
        # Create data directory if using file storage
        if cls.DATABASE_TYPE == 'file':
            try:
                cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
                logger.info("Data directory configured: %s", cls.DATA_DIR)
            except Exception as e:
                logger.error("Cannot create data directory %s: %s", cls.DATA_DIR, e)
                valid = False
        
        # Validate database configuration
        if cls.DATABASE_TYPE == 'postgres':
            if not cls.POSTGRES_PASSWORD:
                logger.warning("POSTGRES_PASSWORD not set - this may cause connection issues")
            if not cls.DATABASE_URL:
                cls.DATABASE_URL = (
                    f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@"
                    f"{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
                )
                logger.info("Generated DATABASE_URL from individual postgres settings")
        
        # Production environment validations
        if cls.ENVIRONMENT == 'production':
            if not cls.SECRET_KEY or cls.SECRET_KEY == 'test-secret-key-for-development-only':
                logger.error("SECRET_KEY must be set in production")
                valid = False
            if cls.DEBUG:
                logger.warning("DEBUG is enabled in production - this is not recommended")
        
        # Log configuration summary
        logger.info("Configuration loaded - Environment: %s, Database: %s, Debug: %s", 
                   cls.ENVIRONMENT, cls.DATABASE_TYPE, cls.DEBUG)
        
        return valid
    
    @classmethod
    def get_database_url(cls) -> Optional[str]:
        """Get the appropriate database URL based on configuration"""
        if cls.DATABASE_TYPE == 'postgres':
            # Generate DATABASE_URL if not set
            if not cls.DATABASE_URL:
                cls.DATABASE_URL = (
                    f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@"
                    f"{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
                )
            return cls.DATABASE_URL
        elif cls.DATABASE_TYPE == 'file':
            # Generate SQLite URL for file-based storage
            db_path = cls.DATA_DIR / "clockit.db"
            return f"sqlite:///{db_path}"
        return None
    
    @classmethod
    def is_cloud_deployment(cls) -> bool:
        """Check if this is a cloud deployment"""
        return cls.CLOUD_PROVIDER is not None or cls.DATABASE_TYPE == 'postgres'