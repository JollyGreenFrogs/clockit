#!/bin/bash

# ClockIt Docker Context Deployment Script
# Simplified deployment using Docker contexts for dev and prod environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="clockit"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[DEPLOY]${NC} $1"
}

# Help function
show_help() {
    echo "ClockIt Docker Context Deployment"
    echo
    echo "Usage: $0 [CONTEXT] [COMMAND]"
    echo
    echo "CONTEXT:"
    echo "  dev     Deploy to development environment"
    echo "  prod    Deploy to production environment"
    echo
    echo "COMMAND:"
    echo "  build   Build and deploy the application (default)"
    echo "  logs    Show logs from running containers"
    echo "  stop    Stop the application"
    echo "  restart Restart the application"
    echo "  status  Show status of running containers"
    echo "  clean   Clean up stopped containers and unused images"
    echo "  reset-db Reset database (WARNING: DELETES ALL DATA!)"
    echo
    echo "Examples:"
    echo "  $0 dev build    # Build and deploy to dev"
    echo "  $0 prod logs    # Show prod logs"
    echo "  $0 dev status   # Check dev status"
    echo
    echo "Available Docker contexts:"
    docker context ls
}

# Check arguments
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

CONTEXT="$1"
COMMAND="${2:-build}"

# Validate context
if [[ "$CONTEXT" != "dev" && "$CONTEXT" != "prod" ]]; then
    print_error "Invalid context: $CONTEXT"
    echo "Valid contexts are: dev, prod"
    exit 1
fi

# Validate command
case "$COMMAND" in
    build|logs|stop|restart|status|clean|reset-db)
        # Valid commands
        ;;
    *)
        print_error "Invalid command: $COMMAND"
        echo "Valid commands are: build, logs, stop, restart, status, clean, reset-db"
        exit 1
        ;;
esac

print_header "Starting ClockIt deployment to $CONTEXT environment"

# Check if Docker context exists
if ! docker context ls --format "{{.Name}}" | grep -q "^$CONTEXT$"; then
    print_error "Docker context '$CONTEXT' not found"
    echo "Available contexts:"
    docker context ls
    exit 1
fi

# Switch to the specified context
print_status "Switching to Docker context: $CONTEXT"
docker context use "$CONTEXT"

# Set environment variables based on context (but don't override COMPOSE_PROJECT_NAME to avoid network conflicts)
if [ "$CONTEXT" = "prod" ]; then
    ENVIRONMENT="production"
    DEBUG="false"
else
    ENVIRONMENT="development"
    DEBUG="true"
fi

# Export environment variables for docker-compose
export ENVIRONMENT
export DEBUG

# Execute the requested command
case "$COMMAND" in
    build)
        print_status "Building and deploying ClockIt to $CONTEXT..."
        
        # Reset environment variables to prevent conflicts with .env files
        print_status "Resetting environment variables to use .env file values..."
        unset API_KEY CORS_ALLOW_CREDENTIALS CORS_ORIGINS DATABASE_IP DATABASE_TYPE ENVIRONMENT \
              JWT_ACCESS_TOKEN_EXPIRE_MINUTES JWT_ALGORITHM JWT_EXPIRATION_HOURS JWT_REFRESH_TOKEN_EXPIRE_DAYS \
              JWT_SECRET_KEY POSTGRES_DB POSTGRES_HOST POSTGRES_PASSWORD POSTGRES_PORT POSTGRES_USER \
              SECRET_KEY ACCESS_TOKEN_EXPIRE_MINUTES RATE_LIMIT_ENABLED RATE_LIMIT_REQUESTS_PER_MINUTE \
              DISABLE_HTTPS_REDIRECT LOG_LEVEL LOG_FORMAT BACKUP_ENABLED MONITORING_ENABLED \
              ENABLE_DEBUG_ENDPOINTS CLOCKIT_DATA_DIR PYTHONPATH
        
        # Handle environment-specific .env files
        if [ "$CONTEXT" = "prod" ]; then
            ENV_FILE="$SCRIPT_DIR/.env.prod"
            if [ ! -f "$ENV_FILE" ]; then
                print_error "Production environment file .env.prod not found!"
                print_status "Creating template .env.prod file..."
                print_warning "YOU MUST EDIT .env.prod WITH SECURE VALUES BEFORE PRODUCTION DEPLOYMENT!"
                echo
                print_warning "Required actions:"
                echo "1. Generate secure POSTGRES_PASSWORD (min 16 chars)"
                echo "2. Generate secure SECRET_KEY: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                echo "3. Generate secure JWT_SECRET_KEY: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                echo "4. Update CORS_ORIGINS with your actual domain"
                echo "5. Review all settings in .env.prod"
                exit 1
            fi
            
            # Validate critical production settings
            if grep -q "CHANGE_ME" "$ENV_FILE"; then
                print_error "Production .env.prod file contains default CHANGE_ME values!"
                print_warning "Please update all CHANGE_ME values in .env.prod before deploying to production"
                exit 1
            fi
            
            # Database protection for production - check if database exists and password is changing
            if docker volume inspect clockit_postgres_data >/dev/null 2>&1; then
                print_status "🔒 Database protection: Existing production database detected"
                if [ -f "$SCRIPT_DIR/.env" ]; then
                    CURRENT_DB_PASS=$(grep "^POSTGRES_PASSWORD=" "$SCRIPT_DIR/.env" 2>/dev/null | cut -d'=' -f2 || echo "")
                    NEW_DB_PASS=$(grep "^POSTGRES_PASSWORD=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 || echo "")
                    if [ -n "$CURRENT_DB_PASS" ] && [ -n "$NEW_DB_PASS" ] && [ "$CURRENT_DB_PASS" != "$NEW_DB_PASS" ]; then
                        print_error "🚨 DATABASE PASSWORD CHANGE DETECTED!"
                        print_warning "Changing the database password will break access to existing data."
                        print_warning "If you need to change the password, use: $0 $CONTEXT reset-db"
                        print_warning "WARNING: reset-db will DELETE ALL DATABASE DATA!"
                        exit 1
                    fi
                fi
            fi
            
            # Copy prod env file to .env for docker-compose
            print_status "Using production environment configuration (.env.prod)"
            cp "$ENV_FILE" "$SCRIPT_DIR/.env"
        else
            # Development environment
            ENV_FILE="$SCRIPT_DIR/.env.dev"
            if [ ! -f "$ENV_FILE" ]; then
                print_warning "Development .env.dev file not found. Creating from .env.example..."
                cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
                print_warning "Please edit .env.dev file with your development configuration"
            fi
            # Copy dev env file to .env for docker-compose
            print_status "Using development environment configuration (.env.dev)"
            cp "$ENV_FILE" "$SCRIPT_DIR/.env"
        fi
        
        # Remove and recreate Docker network to ensure correct settings
        print_status "Resetting Docker network for $CONTEXT..."
        docker network rm clockit-network 2>/dev/null || true
        
        # Pull latest images and build
        print_status "Pulling latest base images..."
        docker-compose pull --ignore-pull-failures
        
        print_status "Building application images..."
        docker-compose build --no-cache
        
        print_status "Starting services..."
        docker-compose up -d
        
        print_status "Waiting for services to be healthy..."
        sleep 10
        
        # Show status
        print_status "Deployment status:"
        docker-compose ps
        
        print_status "🎉 Deployment to $CONTEXT completed!"
        
        if [ "$CONTEXT" = "dev" ]; then
            echo
            echo "🌐 Development Access: http://10.0.27.159:3000"
            echo "📊 API Health Check: http://10.0.27.159:8000/health"
            echo "📚 API Documentation: http://10.0.27.159:8000/docs"
        else
            echo
            echo "🌐 Production Access: http://172.31.14.175:3000"
            echo "📊 API Health Check: http://172.31.14.175:8000/health"
            echo "📚 API Documentation: http://172.31.14.175:8000/docs"
        fi
        ;;
        
    logs)
        print_status "Showing logs for $CONTEXT environment..."
        docker-compose logs -f --tail=100
        ;;
        
    stop)
        print_status "Stopping ClockIt services in $CONTEXT..."
        docker-compose down
        print_status "Services stopped"
        ;;
        
    restart)
        print_status "Restarting ClockIt services in $CONTEXT..."
        docker-compose restart
        print_status "Services restarted"
        docker-compose ps
        ;;
        
    status)
        print_status "ClockIt status in $CONTEXT environment:"
        docker-compose ps
        echo
        print_status "Docker system info:"
        docker system df
        ;;
        
    clean)
        print_status "Cleaning up Docker resources in $CONTEXT..."
        print_warning "This will remove stopped containers and unused images"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down --remove-orphans
            docker system prune -f
            docker image prune -f
            print_status "Cleanup completed"
        else
            print_status "Cleanup cancelled"
        fi
        ;;
        
    reset-db)
        print_error "🚨 DATABASE RESET WARNING!"
        print_warning "This will PERMANENTLY DELETE ALL DATABASE DATA in $CONTEXT environment!"
        print_warning "This action cannot be undone!"
        echo
        if [ "$CONTEXT" = "prod" ]; then
            print_error "⚠️  PRODUCTION DATABASE RESET ⚠️"
            print_warning "You are about to delete the PRODUCTION database!"
            echo
            read -p "Type 'DELETE PRODUCTION DATA' to confirm: " -r
            if [ "$REPLY" != "DELETE PRODUCTION DATA" ]; then
                print_status "Database reset cancelled - confirmation text did not match"
                exit 0
            fi
        else
            read -p "Type 'DELETE' to confirm database reset: " -r
            if [ "$REPLY" != "DELETE" ]; then
                print_status "Database reset cancelled"
                exit 0
            fi
        fi
        
        print_status "Stopping services and removing database volumes..."
        docker-compose down -v
        print_status "🗑️  Database volumes removed - all data deleted"
        print_status "You can now run '$0 $CONTEXT build' to create a fresh database"
        ;;
esac