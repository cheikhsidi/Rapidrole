# 🐳 Docker Quick Reference

## TL;DR

```bash
# 1. Add API keys to .env
cp .env.docker .env
# Edit .env with your keys

# 2. Start everything
docker-compose up -d

# 3. Done!
open http://localhost:8000/docs
```

---

## Common Commands

### Start/Stop
```bash
docker-compose up -d        # Start all services
docker-compose down         # Stop all services
docker-compose restart      # Restart all services
```

### Logs
```bash
docker-compose logs -f      # All logs
docker-compose logs -f api  # API logs only
```

### Database
```bash
# Run migrations
docker-compose exec api uv run alembic upgrade head

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d job_copilot

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

### Testing
```bash
# Run tests
docker-compose exec api uv run pytest tests/ -v

# Run with coverage
docker-compose exec api uv run pytest tests/ --cov
```

### Shell Access
```bash
# API container shell
docker-compose exec api /bin/bash

# PostgreSQL shell
docker-compose exec postgres psql -U postgres -d job_copilot

# Redis CLI
docker-compose exec redis redis-cli
```

---

## Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **PostgreSQL** | localhost:5432 | postgres/postgres |
| **Redis** | localhost:6379 | - |

---

## Makefile Commands

```bash
make up             # Start services
make down           # Stop services
make logs           # View logs
make shell          # API shell
make test           # Run tests
make migrate        # Run migrations
make health         # Check health
```

See `make help` for all commands.

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it or change port in docker-compose.yml
```

### Services Won't Start
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs

# Restart
docker-compose restart
```

### Clean Start
```bash
# Remove everything
docker-compose down -v
docker system prune -f

# Start fresh
docker-compose up -d
```

---

## Full Documentation

See [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) for complete guide.
