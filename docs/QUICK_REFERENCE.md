# Quick Reference Card

## 🚀 Common Commands

```bash
# Setup
./scripts/setup.sh

# Start server
uv run uvicorn main:app --reload

# Run tests
./scripts/test.sh

# Run migrations
uv run alembic upgrade head

# View logs (development)
tail -f logs/app.log

# View metrics
curl http://localhost:8000/metrics
```

## 📊 Key Endpoints

```bash
# Health checks
GET /health
GET /health/ready

# API docs
GET /docs
GET /redoc

# Metrics
GET /metrics

# Jobs
GET /api/v1/jobs/search?user_id={id}&limit=20
GET /api/v1/jobs/{job_id}
POST /api/v1/jobs/analyze/{job_id}

# Applications
POST /api/v1/applications/
GET /api/v1/applications/{id}
GET /api/v1/applications/user/{user_id}

# Users
POST /api/v1/users/
POST /api/v1/users/{id}/profile

# Intelligence
GET /api/v1/intelligence/compatibility/{user_id}/{job_id}
GET /api/v1/intelligence/recommendations/{user_id}
```

## 🔍 Logging Quick Reference

### Add Logging to New Code

```python
from utils.logging import get_logger

logger = get_logger(__name__)

# Info log
logger.info("Operation completed", extra={"key": "value"})

# Error log
logger.error("Operation failed", exc_info=True)

# Debug log
logger.debug("Debug info", extra={"data": data})
```

### Add Tracing

```python
from utils.tracing import trace_function, AsyncTraceContext

# Decorator
@trace_function("module.function")
async def my_function():
    pass

# Context manager
async with AsyncTraceContext("operation_name", {"key": "value"}):
    await do_something()
```

### Log Specialized Events

```python
from utils.logging import (
    log_api_call,
    log_database_query,
    log_agent_execution,
    log_security_event,
)

# LLM API call
log_api_call("openai", "gpt-4o", duration=1.5, tokens=1000)

# Database query
log_database_query("select", "users", duration=0.05, rows_affected=10)

# Agent execution
log_agent_execution("JobAnalyzer", "analyze", duration=2.0, success=True)

# Security event
log_security_event("login_failure", "medium", {"user": "john"})
```

## 📈 Monitoring Quick Reference

### Key Metrics to Watch

```promql
# Error rate
rate(http_requests_total{status_code=~"5.."}[5m])

# P95 latency
histogram_quantile(0.95, http_request_duration_seconds)

# Database pool usage
db_connection_pool_available

# LLM cost
rate(llm_estimated_cost_usd[1h])

# Agent success rate
rate(agent_executions_total{status="success"}[5m])
```

### Common Log Queries

```bash
# Find logs for request
grep "request_id:abc-123" logs/*.log

# Find errors
grep "ERROR" logs/*.log

# Find slow requests
grep "duration_ms" logs/*.log | awk '$NF > 1000'

# Find user activity
grep "user_id:user-123" logs/*.log
```

## 🐛 Troubleshooting

### Database Issues

```bash
# Check connection
docker exec job_copilot_db psql -U postgres -d job_copilot -c "SELECT 1;"

# Check pool status
curl http://localhost:8000/metrics | grep db_connection_pool
```

### Redis Issues

```bash
# Check connection
docker exec job_copilot_redis redis-cli ping

# Check operations
curl http://localhost:8000/metrics | grep redis_operations
```

### LLM API Issues

```bash
# Check API calls
curl http://localhost:8000/metrics | grep llm_api_calls

# Check logs
grep "openai" logs/*.log | grep "ERROR"
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...

# Optional
LOG_LEVEL=INFO
SENTRY_DSN=https://...
ENABLE_METRICS=true
SLOW_REQUEST_THRESHOLD=1.0
```

### Logging Levels

```bash
# Development
LOG_LEVEL=DEBUG

# Production
LOG_LEVEL=INFO

# Troubleshooting
LOG_LEVEL=DEBUG
```

## 📚 Documentation Links

- [README](../README.md) - Overview
- [Getting Started](../GETTING_STARTED.md) - Quick start
- [Architecture](ARCHITECTURE.md) - System design
- [Deployment](DEPLOYMENT.md) - Deployment guide
- [Production Readiness](PRODUCTION_READINESS.md) - Checklist
- [Logging Guide](LOGGING_GUIDE.md) - Logging details

## 🎯 Quick Tips

1. **Always include request_id in logs**
2. **Use trace decorators for functions**
3. **Log errors with exc_info=True**
4. **Monitor Prometheus metrics**
5. **Check Sentry for errors**
6. **Use structured logging**
7. **Include context in logs**
8. **Track LLM costs**

## 🚨 Emergency Procedures

### High Error Rate

```bash
# Check error logs
grep "ERROR" logs/*.log | tail -100

# Check Sentry
# Visit Sentry dashboard

# Check metrics
curl http://localhost:8000/metrics | grep error
```

### Slow Requests

```bash
# Find slow requests
grep "duration_ms" logs/*.log | awk '$NF > 2000'

# Check P95 latency
curl http://localhost:8000/metrics | grep quantile

# Enable debug logging
export LOG_LEVEL=DEBUG
```

### Database Issues

```bash
# Check health
curl http://localhost:8000/health/ready

# Check pool
curl http://localhost:8000/metrics | grep db_connection_pool

# Restart database
docker-compose restart postgres
```

---

**Keep this handy for quick reference!** 📋
