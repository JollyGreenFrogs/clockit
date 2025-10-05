#!/bin/bash

# ClockIt - Deploy to EC2 Server
# This script deploys ClockIt to your EC2 server using the docker_srv SSH alias

set -e

echo "🚀 Deploying ClockIt to EC2 server..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if we can connect to the server
print_status "Testing SSH connection to docker_srv..."
if ! ssh -o ConnectTimeout=10 docker_srv "echo 'Connection successful'" >/dev/null 2>&1; then
    echo "❌ Cannot connect to docker_srv. Please check your SSH configuration."
    exit 1
fi

print_status "✅ SSH connection successful"

# Copy deployment script to server
print_status "Copying deployment script to server..."
scp deploy-ec2.sh docker_srv:~/

# Run deployment on server
print_status "Starting deployment on server..."
ssh docker_srv "chmod +x ~/deploy-ec2.sh && ./deploy-ec2.sh"

print_status "🎉 Deployment completed!"
echo
echo "==========================================="
echo "ClockIt Deployment Summary"
echo "==========================================="
echo
echo "🌐 Local Access: http://172.31.14.175"
echo "🔗 Production Access: Via your Cloudflare tunnel"
echo "📊 Health Check: http://172.31.14.175/health"
echo "📚 API Documentation: http://172.31.14.175/docs"
echo
echo "📁 Server Location: /opt/clockit"
echo "🔧 Management Commands:"
echo "   ssh docker_srv"
echo "   cd /opt/clockit"
echo "   docker-compose logs -f    # View logs"
echo "   docker-compose restart    # Restart app"
echo "   docker-compose ps         # Check status"
echo

# Test the deployment
print_status "Testing deployment..."
if ssh docker_srv "curl -sf http://172.31.14.175/health" >/dev/null 2>&1; then
    echo "✅ Application is healthy and responding"
else
    print_warning "⚠️  Health check failed - check logs on server"
    echo "Run: ssh docker_srv 'cd /opt/clockit && docker-compose logs'"
fi