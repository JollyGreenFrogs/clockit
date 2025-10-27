#!/bin/bash
# Run tests with proper environment configuration to disable rate limiting and security features that interfere with testing

export ENVIRONMENT=test
export ENABLE_RATE_LIMITING=false
export SECRET_KEY=test_secret_key_for_testing_only_not_production_use_123456789
export DEBUG=true
export BCRYPT_ROUNDS=4  # Faster password hashing for tests
export PASSWORD_MIN_LENGTH=8  # Reduce minimum for test passwords

echo "Running tests with test configuration..."
echo "Environment: $ENVIRONMENT"
echo "Rate limiting: $ENABLE_RATE_LIMITING"
echo "BCrypt rounds: $BCRYPT_ROUNDS"

cd /home/venura/clockit
/home/venura/clockit/.venv/bin/python -m pytest "$@"