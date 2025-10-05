# ClockIt Cloud Deployment Guide

This guide covers deploying ClockIt to various cloud environments with both file-based and database storage options.

## Quick Start

### Local Development with Docker

1. **Clone and Configure**
   ```bash
   git clone <repository-url>
   cd clockit
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the Application**
   - Web Interface: http://localhost:8000
   - Health Check: http://localhost:8000/health

### Configuration Options

#### File-Based Storage (Default)
```env
DATABASE_TYPE=file
CLOCKIT_DATA_DIR=/app/data
```

#### PostgreSQL Cloud Storage
```env
DATABASE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=clockit
POSTGRES_USER=clockit
POSTGRES_PASSWORD=your_password_here
```

## Cloud Deployment Options

### 1. Docker Container Deployment

#### Build Production Image
```bash
docker build -t clockit:latest .
```

#### Run Container
```bash
docker run -d \
  --name clockit \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_TYPE=postgres \
  -e POSTGRES_HOST=your-db-host \
  -e POSTGRES_PASSWORD=your-password \
  -v clockit_data:/app/data \
  clockit:latest
```

### 2. Kubernetes Deployment

#### Basic Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clockit
spec:
  replicas: 3
  selector:
    matchLabels:
      app: clockit
  template:
    metadata:
      labels:
        app: clockit
    spec:
      containers:
      - name: clockit
        image: clockit:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_TYPE
          value: "postgres"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: clockit-secrets
              key: postgres-password
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: clockit-service
spec:
  selector:
    app: clockit
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. AWS Deployment

#### ECS with Fargate
1. **Create Task Definition**
   ```json
   {
     "family": "clockit-task",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "clockit",
         "image": "your-account.dkr.ecr.region.amazonaws.com/clockit:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "ENVIRONMENT",
             "value": "production"
           }
         ],
         "secrets": [
           {
             "name": "POSTGRES_PASSWORD",
             "valueFrom": "arn:aws:secretsmanager:region:account:secret:clockit/postgres-password"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/clockit",
             "awslogs-region": "us-west-2",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

#### Lambda Deployment (Serverless)
For serverless deployment, use AWS Lambda with Application Load Balancer:

```python
# lambda_handler.py
from mangum import Mangum
from src.main import app

handler = Mangum(app)
```

### 4. Google Cloud Platform

#### Cloud Run Deployment
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/clockit

# Deploy to Cloud Run
gcloud run deploy clockit \
  --image gcr.io/PROJECT-ID/clockit \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,DATABASE_TYPE=postgres \
  --set-env-vars POSTGRES_HOST=your-cloud-sql-ip
```

### 5. Azure Deployment

#### Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name clockit \
  --image clockit:latest \
  --dns-name-label clockit-app \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
    DATABASE_TYPE=postgres \
  --secure-environment-variables \
    POSTGRES_PASSWORD=your-password
```

## Database Setup

### PostgreSQL Cloud Databases

#### AWS RDS
```bash
aws rds create-db-instance \
  --db-instance-identifier clockit-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username clockit \
  --master-user-password your-password \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxxx
```

#### Google Cloud SQL
```bash
gcloud sql instances create clockit-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=us-central1
```

#### Azure Database for PostgreSQL
```bash
az postgres server create \
  --resource-group myResourceGroup \
  --name clockit-db \
  --location westus2 \
  --admin-user clockit \
  --admin-password your-password \
  --sku-name GP_Gen5_2
```

## Environment Variables Reference

### Required for Production
- `ENVIRONMENT=production`
- `SECRET_KEY` - Generate with `openssl rand -hex 32`
- `DATABASE_TYPE` - Either 'file' or 'postgres'

### Database Configuration (if using postgres)
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

### Optional
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR
- `LOG_FORMAT` - text or json
- `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET` - For Planner integration

## Monitoring and Health Checks

### Health Check Endpoint
```bash
curl http://your-app-url/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0",
  "data_directory_accessible": true,
  "tasks_loadable": true
}
```

### Logging
Application logs are structured and can be consumed by:
- CloudWatch (AWS)
- Stackdriver (GCP)
- Azure Monitor (Azure)
- ELK Stack
- Datadog, New Relic, etc.

## Security Considerations

1. **Secrets Management**
   - Use cloud secret managers (AWS Secrets Manager, Azure Key Vault, etc.)
   - Never commit secrets to version control

2. **Network Security**
   - Use VPCs/VNets for database isolation
   - Configure security groups/firewalls appropriately
   - Use SSL/TLS for database connections

3. **Authentication**
   - Implement authentication for production deployments
   - Use strong, unique SECRET_KEY values

4. **HTTPS**
   - Always use HTTPS in production
   - Configure SSL certificates properly

## Troubleshooting

### Common Issues

1. **Health Check Failing**
   ```bash
   docker logs clockit
   # Check data directory permissions
   # Verify database connectivity
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connectivity
   docker run --rm postgres:15 psql -h hostname -U username -d database
   ```

3. **Permission Issues**
   ```bash
   # Check data directory permissions in container
   docker exec clockit ls -la /app/data
   ```

### Debug Mode
For troubleshooting, enable debug mode:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Migration from Development

1. **Export Data** (if using file storage)
   ```bash
   docker cp clockit:/app/data ./backup-data
   ```

2. **Database Migration** (when switching to postgres)
   - Implement database migration scripts
   - Export JSON data and import to PostgreSQL

3. **Configuration**
   - Update environment variables
   - Test in staging environment first

## Support

For deployment issues:
1. Check application logs
2. Verify environment configuration
3. Test health check endpoint
4. Review cloud provider documentation