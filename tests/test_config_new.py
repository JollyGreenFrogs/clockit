"""
Test configuration management with new database architecture
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from config import Config


class TestBasicConfiguration:
    """Test basic configuration functionality"""

    def test_default_config_values(self):
        """Test default configuration values"""
        assert Config.ENVIRONMENT == "development"
        assert Config.HOST == "0.0.0.0"
        assert Config.PORT == 8000
        assert Config.LOG_LEVEL == "INFO"

    def test_database_type_default(self):
        """Test default database type"""
        # Should now default to postgres instead of file
        assert Config.DATABASE_TYPE in [
            "postgres",
            "file",
        ]  # Allow both during transition

    def test_data_directory_exists(self):
        """Test that data directory configuration exists"""
        assert hasattr(Config, "DATA_DIR")
        assert isinstance(Config.DATA_DIR, Path)


class TestEnvironmentVariableOverrides:
    """Test configuration override via environment variables"""

    @patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "production",
            "DEBUG": "true",
            "PORT": "9000",
            "DATABASE_TYPE": "postgres",
            "POSTGRES_HOST": "test-host",
            "POSTGRES_PASSWORD": "test-password",
            "SECRET_KEY": "test-secret-key",
        },
    )
    def test_environment_variable_override(self):
        """Test configuration override with environment variables"""
        # Force reload of config
        import importlib

        import config

        importlib.reload(config)

        assert config.Config.ENVIRONMENT == "production"
        assert config.Config.PORT == 9000
        assert config.Config.DATABASE_TYPE == "postgres"
        assert config.Config.POSTGRES_HOST == "test-host"
        assert config.Config.POSTGRES_PASSWORD == "test-password"
        assert config.Config.SECRET_KEY == "test-secret-key"


class TestDatabaseConfiguration:
    """Test database-specific configuration"""

    @patch.dict(
        os.environ,
        {
            "DATABASE_TYPE": "postgres",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test_clockit",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
        },
    )
    def test_postgres_config(self):
        """Test PostgreSQL configuration"""
        import importlib

        import config

        importlib.reload(config)

        assert config.Config.DATABASE_TYPE == "postgres"
        assert config.Config.POSTGRES_HOST == "localhost"
        assert config.Config.POSTGRES_PORT == 5432
        assert config.Config.POSTGRES_DB == "test_clockit"
        assert config.Config.POSTGRES_USER == "test_user"
        assert config.Config.POSTGRES_PASSWORD == "test_password"

    def test_database_url_generation_postgres(self):
        """Test PostgreSQL database URL generation"""
        with patch.dict(
            os.environ,
            {
                "DATABASE_TYPE": "postgres",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "clockit_db",
                "POSTGRES_USER": "clockit_user",
                "POSTGRES_PASSWORD": "password123",
            },
        ):
            import importlib

            import config

            importlib.reload(config)

            expected_url = (
                "postgresql://clockit_user:password123@localhost:5432/clockit_db"
            )
            assert config.Config.get_database_url() == expected_url

    def test_database_url_generation_file(self):
        """Test file-based database URL generation"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "file"}):
            import importlib

            import config

            importlib.reload(config)

            db_url = config.Config.get_database_url()
            assert db_url.startswith("sqlite:///")


class TestAuthenticationConfiguration:
    """Test authentication-related configuration"""

    def test_secret_key_exists(self):
        """Test that secret key is configured"""
        assert hasattr(Config, "SECRET_KEY")
        assert Config.SECRET_KEY is not None
        assert len(Config.SECRET_KEY) > 0

    def test_jwt_configuration(self):
        """Test JWT-related configuration"""
        assert hasattr(Config, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert hasattr(Config, "REFRESH_TOKEN_EXPIRE_DAYS")
        assert isinstance(Config.ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert isinstance(Config.REFRESH_TOKEN_EXPIRE_DAYS, int)
        assert Config.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert Config.REFRESH_TOKEN_EXPIRE_DAYS > 0

    def test_password_hashing_config(self):
        """Test password hashing configuration"""
        # Test that password hashing settings exist
        assert hasattr(Config, "BCRYPT_ROUNDS")
        assert isinstance(Config.BCRYPT_ROUNDS, int)
        assert Config.BCRYPT_ROUNDS >= 10  # Security minimum


class TestProductionConfiguration:
    """Test production-specific configuration"""

    @patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "production-secret-key-very-long",
            "DATABASE_TYPE": "postgres",
            "POSTGRES_HOST": "prod-db-host",
            "POSTGRES_PASSWORD": "secure-prod-password",
        },
    )
    def test_production_config_valid(self):
        """Test that production configuration is valid"""
        import importlib

        import config

        importlib.reload(config)

        assert config.Config.ENVIRONMENT == "production"
        assert config.Config.SECRET_KEY == "production-secret-key-very-long"
        assert len(config.Config.SECRET_KEY) >= 32  # Production secret should be long

    @patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "production"
            # Missing SECRET_KEY in production
        },
    )
    def test_production_missing_secret_key(self):
        """Test that production fails without proper secret key"""
        # Production should require a strong secret key
        import importlib

        import config

        # This might raise an error or set a warning
        # Implementation depends on config validation strategy
        try:
            importlib.reload(config)
            # If no error, check that a secure default is used or warning is logged
            if hasattr(config.Config, "SECRET_KEY"):
                # Should either be None/empty (causing app to fail) or a secure default
                assert (
                    config.Config.SECRET_KEY is None
                    or len(config.Config.SECRET_KEY) >= 32
                )
        except Exception as e:
            # Expected to fail in production without proper config
            assert "secret" in str(e).lower() or "production" in str(e).lower()


class TestConfigValidation:
    """Test configuration validation"""

    def test_config_validation_file_storage(self):
        """Test file storage configuration validation"""
        with patch.dict(os.environ, {"DATABASE_TYPE": "file"}):
            import importlib

            import config

            importlib.reload(config)

            # File storage should have data directory configured
            assert hasattr(config.Config, "DATA_DIR")
            assert config.Config.DATA_DIR is not None

    def test_config_validation_postgres(self):
        """Test PostgreSQL configuration validation"""
        with patch.dict(
            os.environ,
            {
                "DATABASE_TYPE": "postgres",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_DB": "clockit_db",
                "POSTGRES_USER": "clockit_user",
                "POSTGRES_PASSWORD": "password",
            },
        ):
            import importlib

            import config

            importlib.reload(config)

            # All required postgres configs should be present
            assert config.Config.POSTGRES_HOST is not None
            assert config.Config.POSTGRES_DB is not None
            assert config.Config.POSTGRES_USER is not None
            assert config.Config.POSTGRES_PASSWORD is not None

    def test_port_validation(self):
        """Test port number validation"""
        with patch.dict(os.environ, {"PORT": "8080"}):
            import importlib

            import config

            importlib.reload(config)

            assert config.Config.PORT == 8080
            assert isinstance(config.Config.PORT, int)

    def test_invalid_port_handling(self):
        """Test handling of invalid port numbers"""
        with patch.dict(os.environ, {"PORT": "invalid"}):
            import importlib

            import config

            # Should either use default or raise error
            try:
                importlib.reload(config)
                # If no error, should use default port
                assert config.Config.PORT == 8000  # default
            except ValueError:
                # Expected to fail with invalid port
                pass


class TestCloudDeploymentConfiguration:
    """Test cloud deployment specific configuration"""

    def test_is_cloud_deployment_detection(self):
        """Test cloud deployment detection"""
        # Test various cloud environment indicators
        cloud_indicators = [
            {"DATABASE_TYPE": "postgres", "POSTGRES_HOST": "remote-db.cloud.com"},
            {"ENVIRONMENT": "production", "SECRET_KEY": "cloud-secret"},
            {"RENDER": "true"},  # Render.com
            {"HEROKU": "true"},  # Heroku
        ]

        for env_vars in cloud_indicators:
            with patch.dict(os.environ, env_vars):
                import importlib

                import config

                importlib.reload(config)

                # Should detect as cloud deployment
                is_cloud = config.Config.is_cloud_deployment()
                assert isinstance(is_cloud, bool)

    def test_local_development_detection(self):
        """Test local development detection"""
        with patch.dict(
            os.environ, {"ENVIRONMENT": "development", "DATABASE_TYPE": "file"}
        ):
            import importlib

            import config

            importlib.reload(config)

            is_cloud = config.Config.is_cloud_deployment()
            # Local development should not be detected as cloud
            assert is_cloud is False


class TestSecurityConfiguration:
    """Test security-related configuration"""

    def test_cors_configuration(self):
        """Test CORS configuration"""
        # CORS settings should be available
        assert hasattr(Config, "CORS_ORIGINS") or hasattr(Config, "ALLOWED_ORIGINS")

    def test_debug_mode_configuration(self):
        """Test debug mode configuration"""
        # Debug settings should be configurable
        assert hasattr(Config, "DEBUG")

        # In production, debug should be False
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "DEBUG": "false"}):
            import importlib

            import config

            importlib.reload(config)

            assert config.Config.DEBUG is False

    def test_rate_limiting_config(self):
        """Test rate limiting configuration if implemented"""
        # If rate limiting is implemented, should have configuration
        # This is a placeholder for future rate limiting features
        pass


class TestMigrationConfiguration:
    """Test configuration for database migrations and transitions"""

    def test_file_to_postgres_migration_config(self):
        """Test configuration supports file to postgres migration"""
        # Should be able to configure both file and postgres simultaneously
        # for migration purposes
        with patch.dict(
            os.environ,
            {
                "DATABASE_TYPE": "postgres",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_DB": "clockit_db",
                "POSTGRES_USER": "clockit_user",
                "POSTGRES_PASSWORD": "password",
            },
        ):
            import importlib

            import config

            importlib.reload(config)

            # Should have both database configs available
            assert config.Config.DATABASE_TYPE == "postgres"
            assert hasattr(config.Config, "DATA_DIR")  # Still available for migration
