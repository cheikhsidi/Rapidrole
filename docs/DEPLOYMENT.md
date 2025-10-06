# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- uv package manager
- PostgreSQL 16 with pgvector
- Redis 7+

## Local Development

### 1. Quick Setup

```bash
cd backend
./scripts/setup.sh
```

### 2. Manual Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Start infrastructure
docker-compose up -d

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

## Production Deployment

### Docker Deployment

```bash
# Build image
docker build -t job-copilot-backend:latest .

# Run container
docker run -d \
  --name job-copilot-api \
  -p 8000:8000 \
  --env-file .env \
  job-copilot-backend:latest
```

### Docker Compose (Production)

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/job_copilot
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: job_copilot
      POSTGRES_USER: user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### AWS Deployment (ECS)

1. **Build and push image**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t job-copilot-backend .
docker tag job-copilot-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/job-copilot:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/job-copilot:latest
```

2. **Infrastructure**
- RDS PostgreSQL 16 with pgvector
- ElastiCache Redis cluster
- ECS Fargate for API containers
- Application Load Balancer
- CloudWatch for logging

3. **Environment Variables**
Store in AWS Secrets Manager or Parameter Store

### GCP Deployment (Cloud Run)

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/job-copilot-backend
gcloud run deploy job-copilot-api \
  --image gcr.io/PROJECT_ID/job-copilot-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...,REDIS_URL=...
```

## Environment Configuration

### Required Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=50

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Application
APP_ENV=production
SECRET_KEY=<generate-secure-key>
CORS_ORIGINS=["https://yourdomain.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

## Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Monitoring

### Prometheus Metrics

Available at `/metrics`:
- Request count and latency
- Database connection pool stats
- Redis connection stats
- LLM API call metrics

### Health Checks

- `/health` - Basic health check
- `/health/db` - Database connectivity
- `/health/redis` - Redis connectivity

### Logging

Structured JSON logs with:
- Request ID
- User ID
- Endpoint
- Duration
- Status code
- Error details

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up -d --scale api=4

# Kubernetes
kubectl scale deployment job-copilot-api --replicas=4
```

### Performance Tuning

1. **Database Connection Pool**
   - Adjust `DATABASE_POOL_SIZE` based on load
   - Monitor connection usage

2. **Redis Connection Pool**
   - Adjust `REDIS_MAX_CONNECTIONS`
   - Enable connection pooling

3. **Worker Processes**
   - Gunicorn: `workers = (2 * CPU_cores) + 1`
   - Uvicorn workers for async handling

4. **Caching Strategy**
   - Cache LLM responses
   - Cache embedding results
   - Cache job search results

## Security Checklist

- [ ] Use HTTPS/TLS in production
- [ ] Rotate API keys regularly
- [ ] Enable rate limiting
- [ ] Implement request authentication
- [ ] Encrypt sensitive data at rest
- [ ] Use secrets management (AWS Secrets Manager, etc.)
- [ ] Enable CORS with specific origins
- [ ] Implement input validation
- [ ] Set up WAF rules
- [ ] Enable audit logging
- [ ] Regular security updates

## Backup Strategy

### Database Backups

```bash
# Automated daily backups
pg_dump -h host -U user -d job_copilot | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip < backup.sql.gz | psql -h host -U user -d job_copilot
```

### Redis Persistence

Enable AOF (Append Only File) in redis.conf:
```
appendonly yes
appendfsync everysec
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check DATABASE_URL format
   - Verify network connectivity
   - Check connection pool settings

2. **Redis connection errors**
   - Verify REDIS_URL
   - Check Redis server status
   - Review connection limits

3. **LLM API errors**
   - Verify API keys
   - Check rate limits
   - Review error logs

4. **Vector search slow**
   - Create IVFFlat indexes
   - Optimize embedding dimensions
   - Review query patterns

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uv run uvicorn main:app --reload --log-level debug
```
