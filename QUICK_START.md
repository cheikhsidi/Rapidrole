# 🚀 Quick Start Guide

## Get Running in 5 Minutes

### Option 1: Docker (Recommended) 🐳

```bash
cd backend

# 1. Configure API keys
cp .env.docker .env
# Edit .env and add your OPENAI_API_KEY and ANTHROPIC_API_KEY

# 2. Start everything
docker-compose up -d

# 3. Check it's working
curl http://localhost:8000/health
```

**Done!** Visit: http://localhost:8000/docs

See [Docker Setup Guide](backend/docs/DOCKER_SETUP.md) for details.

### Option 2: Local Development

```bash
cd backend

# 1. Setup (one command)
./scripts/setup.sh

# 2. Configure API keys
cp .env.example .env
# Edit .env and add your API keys

# 3. Start the server
uv run uvicorn main:app --reload
```

Visit: http://localhost:8000/docs

---

## 📋 Essential Commands

### Development

**With Docker:**
```bash
# Start services
make up

# View logs
make logs

# Run tests
make test

# Access shell
make shell

# Stop services
make down
```

**Without Docker:**
```bash
# Start server
uv run uvicorn main:app --reload

# Run tests
./scripts/test.sh

# Verify setup
./scripts/verify.sh
```

### Database

```bash
# Run migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Rollback
uv run alembic downgrade -1
```

### Docker

```bash
# Start all services (API, PostgreSQL, Redis)
make up

# Start with development tools (pgAdmin, Redis Commander)
make up-dev

# View logs
make logs

# Stop services
make down

# Rebuild
make build
make up

# Clean everything
make clean
```

See [Docker Setup Guide](backend/docs/DOCKER_SETUP.md) for complete documentation.

---

## 🔍 Quick Checks

### Is Everything Working?

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Check readiness
curl http://localhost:8000/health/ready

# 3. Check metrics
curl http://localhost:8000/metrics

# 4. Check API docs
open http://localhost:8000/docs
```

### Test API Endpoints

```bash
# Create a user
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","full_name":"Test User"}'

# Get OpenAPI spec
curl http://localhost:8000/openapi.json
```

---

## 🐛 Troubleshooting

### Database Connection Error

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Redis Connection Error

```bash
# Check if Redis is running
docker-compose ps

# Restart Redis
docker-compose restart redis

# Test connection
docker exec job_copilot_redis redis-cli ping
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uv run uvicorn main:app --reload --port 8001
```

---

## 📚 Next Steps

1. **Read Documentation**
   - [Architecture](backend/docs/ARCHITECTURE.md)
   - [Deployment](backend/docs/DEPLOYMENT.md)
   - [Logging Guide](backend/docs/LOGGING_GUIDE.md)

2. **Run Examples**
   ```bash
   uv run python examples/test_agents.py
   uv run python examples/example_usage.py
   ```

3. **Import Postman Collection**
   - File: `examples/api_test_collection.json`

4. **Set Up Monitoring**
   - Configure Sentry DSN
   - Set up Grafana dashboards
   - Configure alerts

---

## 🎯 Common Tasks

### Add a New Endpoint

1. Create function in `api/your_module.py`
2. Add logging and documentation
3. Add tests in `tests/test_api.py`
4. Test with `./scripts/test.sh`

### Add a New Agent

1. Create class in `agents/your_agent.py`
2. Add logging and tracing
3. Add tests in `tests/test_agents.py`
4. Update workflow if needed

### Deploy to Production

1. Update `.env` with production values
2. Build Docker image: `docker build -t job-copilot .`
3. Push to registry
4. Deploy to cloud platform
5. Run migrations: `uv run alembic upgrade head`

---

## 💡 Pro Tips

- Use `--reload` for development (auto-restart on changes)
- Check `/metrics` for performance monitoring
- Use `/health/ready` for load balancer health checks
- Enable DEBUG logging for troubleshooting: `LOG_LEVEL=DEBUG`
- Use `uv run pytest -k test_name` to run specific tests
- Check `docs/QUICK_REFERENCE.md` for more commands

---

## ✅ Verification Checklist

Before deploying:

- [ ] All tests pass: `./scripts/test.sh`
- [ ] Setup verified: `./scripts/verify.sh`
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Health checks pass: http://localhost:8000/health
- [ ] Metrics available: http://localhost:8000/metrics
- [ ] Environment configured: `.env` file with API keys
- [ ] Database migrations run: `uv run alembic upgrade head`

---

**Ready to build something amazing!** 🚀

For detailed documentation, see [README.md](README.md)
