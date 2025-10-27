#!/bin/bash

# Test runner script for ClockIt
# Runs both backend and frontend tests with proper Python path setup

set -e

echo "🧪 ClockIt Test Suite"
echo "===================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_info "Creating Python virtual environment..."
    python -m venv .venv
fi

# Backend Tests
print_info "Running backend tests..."
echo "------------------------"

source .venv/bin/activate
pip install -q -r requirements.txt

if pytest -q; then
    print_status "Backend tests passed"
else
    print_error "Backend tests failed"
    exit 1
fi

# Code Quality Checks
print_info "Running code quality checks..."
echo "------------------------------"

pip install -q black isort flake8

if black --check . && isort --check-only . && flake8; then
    print_status "Code quality checks passed"
else
    print_error "Code quality checks failed"
    exit 1
fi

# Frontend Tests
if [ -d "react-frontend" ]; then
    print_info "Running frontend tests..."
    echo "-------------------------"
    
    cd react-frontend
    
    if [ ! -d "node_modules" ]; then
        print_info "Installing Node.js dependencies..."
        npm ci
    fi
    
    # Component tests
    if npm run test:run; then
        print_status "Component tests passed"
    else
        print_error "Component tests failed"
        exit 1
    fi
    
    # Lint check
    if npm run lint; then
        print_status "Frontend linting passed"
    else
        print_error "Frontend linting failed"
        exit 1
    fi
    
    # E2E tests (optional - requires backend to be running)
    print_info "Skipping E2E tests (run 'npm run test:e2e' manually with backend running)"
    
    cd ..
else
    print_info "Frontend directory not found, skipping frontend tests"
fi

echo ""
print_status "All tests completed successfully! 🎉"
echo ""
echo "To run E2E tests:"
echo "1. Start the backend: python src/main.py"
echo "2. In another terminal: cd react-frontend && npm run test:e2e"