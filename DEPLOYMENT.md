# Music RAG Deployment Guide

Complete guide for deploying the Music RAG system in various environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Fastest Way to Get Started

```bash
# 1. Clone and navigate to project
cd music_rag

# 2. Install and initialize
make dev

# 3. Activate environment
source venv/bin/activate

# 4. Load sample data
make init-data

# 5. Run demo
make run-demo
```

## Local Development

### Prerequisites

- Python 3.9+ (3.11 recommended)
- 2GB RAM minimum
- 1GB disk space

### Step-by-Step Setup

#### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

#### 4. Initialize Database

```bash
# Option A: Using CLI
python -m music_rag.cli init-sample-data

# Option B: Using quickstart
python quickstart.py
```

#### 5. Run Development Server

```bash
# CLI mode
python -m music_rag.cli demo

# API mode
python -m uvicorn music_rag.api:app --reload
```

## Docker Deployment

### Simple Docker Deployment

```bash
# 1. Build image
docker build -t music-rag:latest .

# 2. Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  music-rag:latest
```

### Docker Compose (Recommended)

```bash
# 1. Start services
docker-compose up -d

# 2. Check logs
docker-compose logs -f

# 3. Stop services
docker-compose down
```

#### docker-compose.yml Configuration

```yaml
version: '3.8'

services:
  music-rag-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - ENVIRONMENT=production
      - API_KEY=your-secret-key
    restart: unless-stopped
```

## Production Deployment

### Cloud Platforms

#### AWS Deployment

**Option 1: EC2 with Docker**

```bash
# 1. Launch EC2 instance (t3.medium recommended)
# 2. Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start

# 3. Clone and deploy
git clone https://github.com/yourusername/music-rag.git
cd music-rag
docker-compose up -d

# 4. Configure load balancer
# Point ALB to port 8000
```

**Option 2: ECS with Fargate**

```bash
# 1. Build and push to ECR
aws ecr create-repository --repository-name music-rag
docker build -t music-rag .
docker tag music-rag:latest <ecr-url>/music-rag:latest
docker push <ecr-url>/music-rag:latest

# 2. Create ECS task definition
# Use task-definition.json

# 3. Create ECS service
aws ecs create-service --cluster music-rag-cluster \
  --service-name music-rag-api \
  --task-definition music-rag:1 \
  --desired-count 2
```

#### Google Cloud Platform

```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/music-rag

# 2. Deploy to Cloud Run
gcloud run deploy music-rag \
  --image gcr.io/PROJECT_ID/music-rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi
```

#### DigitalOcean App Platform

```bash
# 1. Create app.yaml
spec:
  name: music-rag
  services:
  - name: api
    github:
      repo: yourusername/music-rag
      branch: main
    dockerfile_path: Dockerfile
    http_port: 8000
    instance_count: 2
    instance_size_slug: professional-xs

# 2. Deploy
doctl apps create --spec app.yaml
```

### Kubernetes Deployment

#### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: music-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: music-rag
  template:
    metadata:
      labels:
        app: music-rag
    spec:
      containers:
      - name: api
        image: music-rag:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: music-rag-secrets
              key: api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

#### service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: music-rag-service
spec:
  type: LoadBalancer
  selector:
    app: music-rag
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

## Configuration

### Environment Variables

#### Required Variables

```bash
CHROMADB_PATH=/app/data/chromadb
```

#### Optional Variables

```bash
# Application
ENVIRONMENT=production
DEBUG=false

# API Security
API_KEY=your-secret-api-key

# Performance
MAX_BATCH_SIZE=100
CACHE_ENABLED=true
CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
```

### Configuration File

Create `config.yaml` for advanced configuration:

```yaml
database:
  type: chromadb
  path: /app/data/chromadb

embeddings:
  text_model: all-MiniLM-L6-v2
  audio:
    sample_rate: 22050
    n_mfcc: 40

retrieval:
  default_top_k: 10
  semantic_weight: 0.7

api:
  host: 0.0.0.0
  port: 8000
  workers: 4
```

## Monitoring

### Health Checks

```bash
# Health endpoint
curl http://localhost:8000/health

# Stats endpoint
curl http://localhost:8000/stats \
  -H "X-API-Key: your-api-key"
```

### Logging

#### Application Logs

```bash
# Docker
docker-compose logs -f music-rag-api

# Kubernetes
kubectl logs -f deployment/music-rag
```

#### Log Aggregation

**Using ELK Stack:**

```yaml
# filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### Metrics

**Prometheus Integration:**

```bash
# Install prometheus client
pip install prometheus-fastapi-instrumentator

# Add to api.py
from prometheus_fastapi_instrumentator import Instrumentator

@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)
```

### Alerts

**Example AlertManager Rules:**

```yaml
groups:
- name: music-rag
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status="500"}[5m]) > 0.05
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
```

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up --scale music-rag-api=3

# Kubernetes
kubectl scale deployment music-rag --replicas=5
```

### Load Balancing

**Nginx Configuration:**

```nginx
upstream music_rag {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;

    location / {
        proxy_pass http://music_rag;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security

### API Key Authentication

```bash
# Set API key
export API_KEY=your-secure-api-key

# Use in requests
curl -H "X-API-Key: your-secure-api-key" \
  http://localhost:8000/search \
  -d '{"text_query": "jazz music"}'
```

### HTTPS/TLS

```bash
# Using Let's Encrypt with Nginx
certbot --nginx -d api.musicrag.com
```

### Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## Backup and Recovery

### Database Backup

```bash
# Backup ChromaDB
tar -czf chromadb-backup-$(date +%Y%m%d).tar.gz \
  /app/data/chromadb

# Upload to S3
aws s3 cp chromadb-backup-$(date +%Y%m%d).tar.gz \
  s3://your-bucket/backups/
```

### Automated Backups

```bash
# Cron job (daily at 2 AM)
0 2 * * * /path/to/backup-script.sh
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Symptom: ModuleNotFoundError
# Solution: Install in development mode
pip install -e .
```

#### 2. Memory Issues

```bash
# Symptom: Out of memory
# Solution: Increase Docker memory
docker run -m 4g music-rag

# Or adjust batch size
export MAX_BATCH_SIZE=50
```

#### 3. ChromaDB Permission Errors

```bash
# Symptom: Permission denied
# Solution: Fix permissions
chown -R $(whoami) ./data/chromadb
chmod -R 755 ./data/chromadb
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Run with verbose output
python -m music_rag.cli demo --verbose
```

### Performance Tuning

```bash
# Increase workers
uvicorn music_rag.api:app --workers 4

# Enable caching
export CACHE_ENABLED=true
export CACHE_TTL=3600
```

## Maintenance

### Updates

```bash
# 1. Pull latest code
git pull origin main

# 2. Update dependencies
pip install -r requirements.txt --upgrade

# 3. Restart services
docker-compose restart
```

### Database Maintenance

```bash
# Optimize ChromaDB
# (ChromaDB handles optimization automatically)

# Check database size
du -sh ./data/chromadb
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/music-rag/issues
- Documentation: https://music-rag.readthedocs.io
- Email: support@musicrag.com

---

**Last Updated:** October 2024
**Version:** 0.1.0
