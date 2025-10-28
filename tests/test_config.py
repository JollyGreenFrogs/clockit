"""
Tests for configuration management
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from config import Config


def test_default_config_values():
    """Test default configuration values"""
    # During testing, ENVIRONMENT is set to 'test'
    expected_env = "test" if Config.ENVIRONMENT == "test" else "development"
    assert Config.ENVIRONMENT == expected_env
    assert Config.HOST == "0.0.0.0"
    assert Config.PORT == 8000
    assert Config.DATABASE_TYPE == "postgres"
    assert Config.LOG_LEVEL in ["INFO", "DEBUG"]  # Can be either based on environment


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
def test_environment_variable_override():
    """Test that environment variables override default values"""
    # Need to reload config to pick up new env vars
    import importlib

    import config

    importlib.reload(config)

    assert config.Config.ENVIRONMENT == "production"
    assert config.Config.DEBUG is True
    assert config.Config.PORT == 9000
    assert config.Config.DATABASE_TYPE == "postgres"
    assert config.Config.POSTGRES_HOST == "test-host"
    assert config.Config.POSTGRES_PASSWORD == "test-password"
    assert config.Config.SECRET_KEY == "test-secret-key"


def test_config_validation_file_storage():
    """Test configuration validation for file storage"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.object(Config, "DATABASE_TYPE", "file"):
            with patch.object(Config, "DATA_DIR", Path(temp_dir)):
                assert Config.validate() is True
                assert Path(temp_dir).exists()


@patch.dict(
    os.environ, {"DATABASE_TYPE": "postgres", "POSTGRES_PASSWORD": "test-password"}
)
def test_config_validation_postgres():
    """Test configuration validation for PostgreSQL storage"""
    import importlib

    import config

    importlib.reload(config)

    assert config.Config.validate() is True
    assert config.Config.get_database_url() is not None


@patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False)
@patch.dict(os.environ, {"SECRET_KEY": ""}, clear=False)
def test_config_validation_production_missing_secret():
    """Test configuration validation fails in production without secret key"""
    import importlib

    import config

    importlib.reload(config)

    # Should return False due to missing SECRET_KEY in production
    assert config.Config.validate() is False


def test_database_url_generation():
    """Test database URL generation for PostgreSQL"""
    with patch.object(Config, "DATABASE_TYPE", "postgres"):
        with patch.object(Config, "POSTGRES_USER", "testuser"):
            with patch.object(Config, "POSTGRES_PASSWORD", "testpass"):
                with patch.object(Config, "POSTGRES_HOST", "testhost"):
                    with patch.object(Config, "POSTGRES_PORT", 5432):
                        with patch.object(Config, "POSTGRES_DB", "testdb"):
                            with patch.object(
                                Config, "DATABASE_URL", None
                            ):  # Start with None
                                Config.validate()  # This should generate the URL
                                url = Config.get_database_url()
                                expected = "postgresql://testuser:testpass@testhost:5432/testdb"
                                assert url == expected


def test_is_cloud_deployment():
    """Test cloud deployment detection"""
    # Test with cloud provider set
    with patch.object(Config, "CLOUD_PROVIDER", "aws"):
        assert Config.is_cloud_deployment() is True

    # Test with postgres database
    with patch.object(Config, "DATABASE_TYPE", "postgres"):
        assert Config.is_cloud_deployment() is True

    # Test with file storage and no cloud provider
    with patch.object(Config, "DATABASE_TYPE", "file"):
        with patch.object(Config, "CLOUD_PROVIDER", None):
            assert Config.is_cloud_deployment() is False
