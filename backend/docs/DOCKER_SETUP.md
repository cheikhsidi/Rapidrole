# 🐳 Docker Setup Guide

## Quick Start (3 Commands)

```bash
# 1. Copy environment file and add your API keys
cp .env.docker .env
# Edit .env and add your OPENAI_API_KEY and ANTHROPIC_API_KEY

# 2. Start all services
docker-compose up -d

# 3. Check it's working
curl http://localhost:8000/health
```

**That's it!** API is now running at http://localhost:8000

---

## 📋 Prerequisites

- Docker Desktop installed
- Docker Compose installed (included with Docker Desktop)
- OpenAI API key
- Anthropic API key

---

## 🚀 Getting Started

### 1. Configure Environment

```bash
# Copy the environment template
cp .env.docker .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

Required in `.env`:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### 2. Start Services

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# View logs
docker-compose logs -f

# Or use the Makefile
make up
make logs
```

### 3. Verify Setup

```bash
# Check health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Or use the Makefile
make health
```

---

## 🛠️ Using the Makefile

The Makefile provides convenient commands for development:

### Setup & Run
```bash
make build          # Build Docker images
make up             # Start all services
make up-dev         # Start with pgAdmin and Redis Commander
make down           # Stop all services
make restart        # Restart all services
```

### Logs & Monitoring
```bash
make logs           # View all logs
make logs-api       # View API logs only
make logs-db        # View database logs only
```

### Shell Access
```bash
make shell          # Open shell in API container
make db-shell       # Open PostgreSQL shell
make redis-shell    # Open Redis CLI
```

### Database
```bash
make migrate        # Run database migrations
make migrate-create # Create new migration
make db-reset       # Reset database (WARNING: deletes data)
```

### Testing
```bash
make test           # Run all tests
make test-api       # Run API tests only
make test-cov       # Run tests with coverage
```

### Utilities
```bash
make clean          # Remove containers and volumes
make verify         # Verify setup
make health         # Check service health
```

---

## 📦 Services

### API (FastAPI)
- **URL**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

### PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **Database**: job_copilot
- **User**: postgres
- **Password**: postgres

### Redis
- **Host**: localhost
- **Port**: 6379

### Development Tools (with `make up-dev`)
- **pgAdmin**: http://localhost:5050
  - Email: admin@rapidrole.com
  - Password: admin
- **Redis Commander**: http://localhost:8081

---

## 🔧 Development Workflow

### Hot Reload Development

The API container is configured with hot reload by default:

```bash
# Start services
make up

# Edit any Python file
# Changes are automatically detected and server reloads
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
docker-compose exec api uv run pytest tests/test_api.py -v

# Run with coverage
make test-cov
```

### Database Migrations

```bash
# Run migrations
make migrate

# Create new migration
make migrate-create
# Enter migration message when prompted

# View migration history
docker-compose exec api uv run alembic history
```

### Accessing Services

```bash
# API shell
make shell

# PostgreSQL shell
make db-shell

# Redis CLI
make redis-shell

# View logs
make logs-api
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check if ports are already in use
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Stop conflicting services or change ports in docker-compose.yml
```

### Database Connection Errors

```bash
# Check PostgreSQL is healthy
docker-compose ps

# View PostgreSQL logs
make logs-db

# Restart PostgreSQL
docker-compose restart postgres
```

### API Not Responding

```bash
# Check API logs
make logs-api

# Check health
make health

# Restart API
docker-compose restart api
```

### Migration Errors

```bash
# Reset database (WARNING: deletes all data)
make db-reset

# Or manually:
docker-compose down -v
docker-compose up -d
```

### Clean Start

```bash
# Remove everything and start fresh
make clean
make build
make up
```

---

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Check Health

```bash
# API health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/health/ready

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Service Status

```bash
# List running containers
docker-compose ps

# Check resource usage
docker stats
```

---

## 🔐 Security Notes

### For Development
- Default passwords are used (postgres/postgres)
- API keys are in .env file (not committed to git)
- CORS is open for development

### For Production
- Change all default passwords
- Use secrets management (AWS Secrets Manager, etc.)
- Restrict CORS origins
- Enable HTTPS/TLS
- Use production-grade database credentials

---

## 📝 Environment Variables

### Required
```bash
OPENAI_API_KEY          # Your OpenAI API key
ANTHROPIC_API_KEY       # Your Anthropic API key
```

### Optional
```bash
SENTRY_DSN              # Sentry error tracking
LOG_LEVEL               # Logging level (DEBUG, INFO, WARNING, ERROR)
SLOW_REQUEST_THRESHOLD  # Slow request threshold in seconds
```

### Configured in docker-compose.yml
```bash
DATABASE_URL            # PostgreSQL connection string
REDIS_URL               # Redis connection string
APP_ENV                 # Environment (development, production)
CORS_ORIGINS            # Allowed CORS origins
```

---

## 🚀 Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)

Key differences for production:
- Use production-grade database (RDS, Cloud SQL)
- Use managed Redis (ElastiCache, Cloud Memorystore)
- Enable HTTPS/TLS
- Use secrets management
- Configure proper CORS
- Enable monitoring and alerting
- Use multiple API replicas

---

## 📚 Additional Resources

- [Quick Start Guide](../QUICK_START.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [API Documentation](http://localhost:8000/docs) (when running)

---

## ✅ Checklist

Before starting development:
- [ ] Docker Desktop installed and running
- [ ] `.env` file created with API keys
- [ ] Services started: `make up`
- [ ] Health check passes: `make health`
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Database migrations run: `make migrate`

---

**Happy coding!** 🚀

For issues or questions, check the troubleshooting section or view logs with `make logs`.
