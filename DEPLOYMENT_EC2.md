# ClockIt EC2 Deployment Instructions

## Quick Deployment to EC2 Server

### Prerequisites
- SSH access configured with `docker_srv` alias
- EC2 instance running Ubuntu/Debian
- Cloudflare tunnel already configured

### Deployment Steps

1. **Copy deployment script to server:**
   ```bash
   scp deploy-ec2.sh docker_srv:~/
   ```

2. **SSH into the server:**
   ```bash
   ssh docker_srv
   ```

3. **Run the deployment script:**
   ```bash
   chmod +x ~/deploy-ec2.sh
   ./deploy-ec2.sh
   ```

### What the script does:
- ✅ Installs Docker and Docker Compose
- ✅ Clones the ClockIt repository from GitHub
- ✅ Builds the full-stack application (React + FastAPI)
- ✅ Sets up PostgreSQL database
- ✅ Configures Nginx reverse proxy
- ✅ Sets up firewall rules
- ✅ Creates systemd service for auto-restart
- ✅ Sets up log rotation and backups

### Post-Deployment

**Application URLs:**
- Local testing: `http://172.31.14.175`
- Production: Via your existing Cloudflare tunnel

**Management Commands:**
```bash
# Check application status
cd /opt/clockit && docker-compose ps

# View logs
cd /opt/clockit && docker-compose logs -f

# Restart application
cd /opt/clockit && docker-compose restart

# Update application
cd /opt/clockit && git pull && docker-compose build --no-cache && docker-compose up -d
```

**Important Files:**
- Application: `/opt/clockit/`
- Environment: `/opt/clockit/.env` (contains generated passwords)
- Nginx config: `/etc/nginx/sites-available/clockit`
- Service: `/etc/systemd/system/clockit.service`

### Monitoring

**Health Check:**
```bash
curl http://172.31.14.175/health
```

**Database Backup:**
```bash
# Manual backup
/opt/clockit/backup.sh

# Backups are stored in: /opt/backups/clockit/
```

### Troubleshooting

**Check service status:**
```bash
sudo systemctl status clockit
sudo systemctl status nginx
sudo systemctl status docker
```

**View container logs:**
```bash
cd /opt/clockit
docker-compose logs clockit-app
docker-compose logs clockit-db
```

**Restart services:**
```bash
# Restart ClockIt
sudo systemctl restart clockit

# Restart Nginx
sudo systemctl restart nginx
```

### Security Notes

- The deployment script generates secure random passwords
- Firewall is configured to only allow SSH and HTTP/HTTPS
- Application runs as non-root user in containers
- Database is only accessible within the Docker network
- Save the `.env` file - it contains important credentials

### Cloudflare Tunnel

Since you're using an existing Cloudflare tunnel, make sure it's configured to point to:
- **Target**: `http://172.31.14.175:80`
- **Path**: `/` (or specific subdomain if needed)

The local Nginx will handle the reverse proxy to the Docker containers.