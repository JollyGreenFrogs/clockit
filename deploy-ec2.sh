#!/bin/bash

# ClockIt EC2 Deployment Script
# Simple deployment: clone repo on server and build with Docker

set -e  # Exit on any error

echo "🚀 ClockIt EC2 Deployment Starting..."

# Configuration
APP_NAME="clockit"
APP_DIR="$HOME/clockit"
SERVICE_NAME="clockit"
PRIVATE_IP="172.31.14.175"
GIT_REPO="git@github.com:JollyGreenFrogs/clockit.git"
GIT_BRANCH="main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   print_status "Please run as a regular user with sudo privileges"
   exit 1
fi

print_status "Installing system dependencies..."

# Update system
sudo apt-get update

# Install Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    print_status "Docker already installed"
fi

if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    print_status "Docker Compose already installed"
fi

# Install other dependencies
sudo apt-get install -y \
    nginx \
    git \
    curl \
    htop \
    ufw

print_status "Setting up application directory..."

# Create application directory in user's home
mkdir -p $APP_DIR

# Clone or update the repository
if [ -d "$APP_DIR/.git" ]; then
    print_status "Updating existing repository..."
    cd $APP_DIR
    git fetch origin
    git checkout $GIT_BRANCH
    git pull origin $GIT_BRANCH
else
    print_status "Cloning repository..."
    git clone -b $GIT_BRANCH $GIT_REPO $APP_DIR
    cd $APP_DIR
fi

print_status "Creating environment configuration..."

# Create production environment file with safe password generation
cat > .env << EOF
# ClockIt Production Configuration
DATABASE_TYPE=postgres
POSTGRES_HOST=clockit-db
POSTGRES_PORT=5432
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD="$(openssl rand -base64 32 | tr -d '/+' | head -c 32)"

# Application Settings
CLOCKIT_DATA_DIR=/app/data
CLOCKIT_DEV_MODE=false
PYTHONPATH=/app

# Security
JWT_SECRET_KEY="$(openssl rand -base64 64 | tr -d '/+' | head -c 64)"
SECRET_KEY="$(openssl rand -base64 32 | tr -d '/+' | head -c 32)"
EOF

print_status "Building and starting Docker containers..."

# Build and start the application
docker-compose down || true
docker-compose build --no-cache
docker-compose up -d

print_status "Configuring Nginx reverse proxy..."

# Create Nginx configuration for Cloudflare tunnel
sudo tee /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $PRIVATE_IP localhost;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx

print_status "Configuring firewall..."

# Configure UFW firewall
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

print_status "SSL will be handled by Cloudflare tunnel - skipping local SSL setup"

print_status "Creating systemd service for monitoring..."

# Create systemd service for auto-restart
sudo tee /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=ClockIt Time Tracker
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

print_status "Setting up log rotation..."

# Configure log rotation
sudo tee /etc/logrotate.d/$APP_NAME << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f $APP_DIR/docker-compose.yml restart clockit-app
    endscript
}
EOF

print_status "Creating backup script..."

# Create backup script
cat > $APP_DIR/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/clockit"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL database
docker-compose exec -T clockit-db pg_dump -U clockit clockit | gzip > $BACKUP_DIR/clockit_db_$DATE.sql.gz

# Backup application data
tar -czf $BACKUP_DIR/clockit_data_$DATE.tar.gz -C /opt/clockit data

# Keep only last 7 backups
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x $APP_DIR/backup.sh

# Add backup cron job
(crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh") | crontab -

print_status "Deployment completed successfully! 🎉"
echo
echo "====================================="
echo "ClockIt is now running!"
echo "====================================="
echo
echo "🌐 Web Application (local): http://$PRIVATE_IP"
echo "🌐 Web Application (tunnel): Access via your Cloudflare tunnel"
echo "📊 Health Check: http://$PRIVATE_IP/health"
echo "📚 API Docs: http://$PRIVATE_IP/docs"
echo
echo "📁 Application Directory: $APP_DIR"
echo "📝 Logs: docker-compose logs -f"
echo "🔄 Restart: docker-compose restart"
echo "🛑 Stop: docker-compose down"
echo
echo "⚠️  IMPORTANT: Save your .env file - it contains generated passwords!"
echo "📋 Database Password: $(grep POSTGRES_PASSWORD $APP_DIR/.env | cut -d'=' -f2)"
echo
print_warning "You may need to log out and back in for Docker group membership to take effect"

# Final status check
sleep 10
if curl -sf http://localhost:8000/health > /dev/null; then
    print_status "✅ Application is healthy and responding"
else
    print_error "❌ Application health check failed"
    echo "Check logs with: cd $APP_DIR && docker-compose logs"
fi