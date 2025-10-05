# Kubernetes Deployment for ClockIt

This directory contains Kubernetes manifests for deploying ClockIt to a Kubernetes cluster.

## Files

- `deployment.yaml` - Main application deployment with 3 replicas
- `service.yaml` - Load balancer and internal service definitions
- `secrets.yaml` - Secret management for sensitive configuration
- `pvc.yaml` - Persistent volume claim for data storage
- `ingress.yaml` - Ingress configuration for external access

## Prerequisites

1. Kubernetes cluster (v1.20+)
2. PostgreSQL database (can be deployed separately or use cloud managed service)
3. Docker image built and pushed to accessible registry

## Quick Deploy

1. **Update Secrets**
   ```bash
   # Generate a secret key
   openssl rand -hex 32
   
   # Edit secrets.yaml with actual values
   vi secrets.yaml
   ```

2. **Apply Manifests**
   ```bash
   kubectl apply -f secrets.yaml
   kubectl apply -f pvc.yaml
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   ```

3. **Check Deployment**
   ```bash
   kubectl get pods -l app=clockit
   kubectl get services
   ```

4. **View Logs**
   ```bash
   kubectl logs -l app=clockit --tail=100
   ```

## Configuration

### Environment Variables
The deployment uses the following environment variables:
- `ENVIRONMENT=production`
- `DATABASE_TYPE=postgres`
- `POSTGRES_HOST` - From secret
- `POSTGRES_PASSWORD` - From secret
- `SECRET_KEY` - From secret

### Resource Limits
- CPU: 250m request, 500m limit
- Memory: 256Mi request, 512Mi limit

### Health Checks
- Readiness probe: `/health` endpoint, starts after 30s
- Liveness probe: `/health` endpoint, starts after 60s

## Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment clockit-app --replicas=5

# Horizontal Pod Autoscaling (requires metrics-server)
kubectl autoscale deployment clockit-app --cpu-percent=70 --min=3 --max=10
```

## Database Setup

### Option 1: External PostgreSQL
Update `secrets.yaml` with your external PostgreSQL details.

### Option 2: Deploy PostgreSQL in cluster
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgresql bitnami/postgresql \
  --set auth.postgresPassword=yourpassword \
  --set auth.database=clockit
```

## SSL/TLS and Ingress

Create an ingress resource for HTTPS access:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: clockit-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - clockit.yourdomain.com
    secretName: clockit-tls
  rules:
  - host: clockit.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: clockit-service-internal
            port:
              number: 8000
```

## Monitoring

Enable monitoring with Prometheus:

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: clockit-monitor
spec:
  selector:
    matchLabels:
      app: clockit
  endpoints:
  - port: http
    path: /metrics  # If metrics endpoint is implemented
```

## Troubleshooting

1. **Pod not starting**
   ```bash
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ```

2. **Health check failing**
   ```bash
   kubectl exec -it <pod-name> -- curl localhost:8000/health
   ```

3. **Database connection issues**
   ```bash
   kubectl exec -it <pod-name> -- env | grep POSTGRES
   ```

4. **Check secrets**
   ```bash
   kubectl get secret clockit-secrets -o yaml
   ```