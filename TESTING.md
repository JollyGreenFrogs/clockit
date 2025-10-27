# Testing Guide for ClockIt

This guide provides detailed instructions for setting up and running tests locally.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Troubleshooting](#troubleshooting)
- [Continuous Integration](#continuous-integration)

## Prerequisites

Before running tests, ensure you have the following installed:

- **Python 3.12+** (recommended: 3.12.3 or later)
- **pip** (Python package manager)
- **Git** (for cloning the repository)

Optional for full testing:
- **Node.js 18+** and **npm** (for frontend tests)
- **PostgreSQL** (only if testing with production database configuration)

## Quick Start

For the fastest way to run tests locally:

```bash
# 1. Clone the repository
git clone https://github.com/JollyGreenFrogs/clockit.git
cd clockit

# 2. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the test environment configuration
cp .env.example .env

# 5. Run the tests
pytest
```

That's it! The tests should now run successfully.

## Detailed Setup

### 1. Environment Configuration

The repository includes a `.env.example` file with test-friendly defaults. For local testing:

```bash
# Copy the example environment file
cp .env.example .env
```

**Key settings for testing:**

```bash
# Application Environment
ENVIRONMENT=test          # Disables rate limiting in tests
DEBUG=true

# Database Configuration - SQLite for testing (no PostgreSQL needed)
DEV_MODE=sqlite          # Uses SQLite instead of PostgreSQL
DATABASE_TYPE=file       # File-based storage

# Authentication (test keys only)
SECRET_KEY=test-secret-key-for-development-only-do-not-use-in-production
```

### 2. Install Python Dependencies

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Install all dependencies including test tools
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `pytest` - Testing framework
- `httpx` - HTTP client for API testing
- `fastapi` and `uvicorn` - Web framework
- All application dependencies

### 3. Database Setup

**For local testing (recommended):** The tests use SQLite automatically when `DEV_MODE=sqlite` is set. No additional database setup is required.

**For production-like testing with PostgreSQL (optional):**

If you want to test with PostgreSQL instead of SQLite:

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Create test database
sudo -u postgres createdb clockit_test_db
sudo -u postgres createuser clockit_user
sudo -u postgres psql -c "ALTER USER clockit_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE clockit_test_db TO clockit_user;"

# Update .env file
DATABASE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=clockit_test_db
POSTGRES_USER=clockit_user
POSTGRES_PASSWORD=your_password
```

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run all tests with minimal output
pytest

# Run with coverage report
pytest --cov=src tests/
```

### Run Specific Tests

```bash
# Run a specific test file
pytest tests/test_config.py

# Run a specific test class
pytest tests/test_auth.py::TestUserRegistration

# Run a specific test function
pytest tests/test_auth.py::TestUserRegistration::test_register_new_user

# Run tests matching a pattern
pytest -k "auth"
pytest -k "task and not integration"
```

### Run Tests with Different Output Levels

```bash
# Quiet mode (only show failures)
pytest -q

# Verbose mode (show all test names)
pytest -v

# Very verbose mode (show full test output)
pytest -vv

# Show print statements
pytest -s

# Show full traceback on failures
pytest --tb=long
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"
```

## Test Categories

### Backend Tests (Python)

Located in the `tests/` directory:

- **`test_auth.py`** - Authentication and authorization tests
- **`test_api_endpoints.py`** - API endpoint tests
- **`test_api_new.py`** - Extended API tests
- **`test_config.py`** - Configuration management tests
- **`test_repositories.py`** - Database repository tests
- **`test_task_manager.py`** - Task management business logic
- **`test_invoice_fix.py`** - Invoice generation tests
- **`test_url_encoding_fix.py`** - URL encoding and special character tests

### Frontend Tests (React)

If the frontend is present (`react-frontend/` directory):

```bash
cd react-frontend

# Install dependencies (first time only)
npm ci

# Run component tests (Vitest)
npm run test          # Watch mode
npm run test:run      # Single run

# Run E2E tests (Playwright)
npm run test:e2e

# Run linter
npm run lint
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Tests fail with "Database connection failed"

**Solution:** Ensure you have the correct environment configuration:

```bash
# Check your .env file has these settings
ENVIRONMENT=test
DEV_MODE=sqlite
DATABASE_TYPE=file
```

If using PostgreSQL, verify the database is running:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL if needed
sudo systemctl start postgresql
```

#### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution:** Run pytest from the project root directory, not from the `src/` or `tests/` directory:

```bash
cd /path/to/clockit
pytest
```

#### Issue: Rate limit errors (429 Too Many Requests)

**Solution:** Ensure `ENVIRONMENT=test` is set in your `.env` file. This disables rate limiting during tests.

```bash
# Add to .env
ENVIRONMENT=test
```

#### Issue: Import errors or missing dependencies

**Solution:** Reinstall dependencies:

```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### Issue: Permission denied when creating data directory

**Solution:** Ensure the application has write permissions:

```bash
# Create data directory manually
mkdir -p clockit_data
chmod 755 clockit_data

# Or run with appropriate permissions
sudo chown -R $USER:$USER clockit_data
```

#### Issue: SQLite database is locked

**Solution:** Close any other processes using the database:

```bash
# Remove test database files
rm -f /tmp/clockit_test/*.db
rm -f data/clockit.db

# Rerun tests
pytest
```

### Getting More Information

For more detailed error information:

```bash
# Show full traceback
pytest --tb=long

# Show local variables in traceback
pytest --showlocals

# Increase verbosity
pytest -vv

# Show print statements and logging
pytest -s --log-cli-level=INFO
```

## Continuous Integration

### GitHub Actions

The project uses GitHub Actions for CI/CD. Tests run automatically on:
- Every push to main branch
- Every pull request

The CI pipeline runs:
1. Backend tests with pytest
2. Code quality checks (black, isort, flake8)
3. Frontend tests (if applicable)

### Local CI Simulation

To run the same checks as CI locally:

```bash
# Install dev dependencies
pip install black isort flake8

# Run code formatter (check only)
black --check .

# Run import sorter (check only)
isort --check-only .

# Run linter
flake8

# Run all tests
pytest --cov=src tests/

# Or use the test script
./test.sh
```

## Test Script

The repository includes a `test.sh` script for convenience:

```bash
# Make executable (first time only)
chmod +x test.sh

# Run all tests and quality checks
./test.sh
```

This script:
- Creates a virtual environment if needed
- Installs dependencies
- Runs backend tests
- Runs code quality checks
- Runs frontend tests (if available)

## Test Coverage

To generate a coverage report:

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html tests/

# Open coverage report in browser
# The report will be in htmlcov/index.html
firefox htmlcov/index.html  # or your preferred browser
```

## Writing New Tests

When adding new features, please include tests:

1. **Unit tests** - Test individual functions/methods in isolation
2. **Integration tests** - Test how components work together
3. **API tests** - Test endpoints with various inputs

Example test structure:

```python
import pytest
from fastapi.testclient import TestClient

def test_my_feature(test_client, test_user):
    """Test description"""
    # Arrange
    data = {"key": "value"}
    
    # Act
    response = test_client.post("/endpoint", json=data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["result"] == "expected"
```

## Support

If you encounter issues not covered in this guide:

1. Check the [main README](README.md) for general setup information
2. Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment-specific guidance
3. Open an issue on GitHub with:
   - Your Python version (`python --version`)
   - Your OS
   - Full error message
   - Steps to reproduce

## Summary

**Quick Reference:**

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run tests
pytest                    # All tests
pytest -v                # Verbose
pytest -k "auth"         # Specific tests
pytest --cov=src tests/  # With coverage

# Common environment variables
ENVIRONMENT=test         # Disables rate limiting
DEV_MODE=sqlite         # Uses SQLite instead of PostgreSQL
DATABASE_TYPE=file      # File-based storage
```

Happy testing! 🧪
