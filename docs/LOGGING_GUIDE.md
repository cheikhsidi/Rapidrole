# Logging & Tracing Guide

## Overview

This backend implements comprehensive logging, tracing, and monitoring following production SaaS best practices. Every operation is logged with context, traced across the system, and monitored with metrics.

## Logging Architecture

### Structured Logging

All logs are structured JSON in production for easy parsing and analysis:

```json
{
  "timestamp": "2025-10-05T19:31:25.123Z",
  "level": "INFO",
  "logger": "api.jobs",
  "message": "Job search completed",
  "request_id": "abc-123-def-456",
  "user_id": "user-789",
  "environment": "production",
  "results_count": 15,
  "duration_ms": 234.56
}
```

### Log Levels

- **DEBUG**: Detailed debugging information (disabled in production)
- **INFO**: General informational messages
- **WARNING**: Warning messages (slow requests, deprecated features)
- **ERROR**: Error messages with full context
- **CRITICAL**: Critical system errors

### Context Propagation

Every log includes:
- **request_id**: Unique ID for request tracing
- **user_id**: User performing the action (when available)
- **environment**: Current environment (development/production)
- **duration_ms**: Operation duration
- **Custom metadata**: Operation-specific context

## Distributed Tracing

### Request Tracing

Every HTTP request is automatically traced:

```python
# Middleware automatically adds request ID
X-Request-ID: abc-123-def-456

# All logs for this request include the request_id
logger.info("Processing request", extra={"request_id": "abc-123-def-456"})
```

### Function Tracing

Use the `@trace_function` decorator for automatic tracing:

```python
from utils.tracing import trace_function

@trace_function("my_module.my_function")
async def my_function():
    # Function execution is automatically logged
    # with start time, end time, and duration
    pass
```

### Context Managers

For complex operations, use trace context managers:

```python
from utils.tracing import AsyncTraceContext

async with AsyncTraceContext("operation_name", {"key": "value"}):
    # Operation is traced with metadata
    await do_something()
```

## Logging by Component

### API Endpoints

All API endpoints log:
- Request received (INFO)
- Request parameters
- Response status
- Duration
- Errors (if any)

Example from `api/jobs.py`:

```python
logger.info(
    "Job search requested",
    extra={
        "user_id": str(user_id),
        "limit": limit,
        "min_score": min_score,
    }
)

# ... operation ...

logger.info(
    "Job search completed",
    extra={
        "user_id": str(user_id),
        "results_count": response["total"],
        "duration_ms": round((time.time() - start_time) * 1000, 2),
    }
)
```

### AI Agents

All agents log:
- Agent initialization
- Execution start
- LLM API calls
- Execution completion
- Errors with full context

Example from `agents/job_analyzer.py`:

```python
logger.info(
    "Starting job analysis",
    extra={
        "job_title": job.get("title"),
        "company": job.get("company"),
    }
)

# ... LLM call ...

log_api_call(
    provider="openai",
    model=settings.openai_model,
    duration=api_duration,
)

log_agent_execution(
    agent_name="JobAnalyzerAgent",
    stage="analyze",
    duration=time.time() - start_time,
    success=True,
    metadata={
        "required_skills_count": len(state["required_skills"]),
    }
)
```

### Database Operations

Database operations are logged with:
- Operation type (select, insert, update, delete)
- Table name
- Duration
- Rows affected
- Errors

Example:

```python
log_database_query(
    operation="select",
    table="job_postings",
    duration=duration,
    rows_affected=len(results),
)
```

### Embeddings & Vector Search

Embedding operations log:
- Text length
- Batch size
- Token usage
- API duration
- Cost estimation

Example from `embeddings/service.py`:

```python
logger.info(
    f"Generated {len(embeddings)} embeddings",
    extra={
        "batch_size": len(embeddings),
        "tokens": tokens,
        "duration_ms": round(duration * 1000, 2),
    }
)
```

## Prometheus Metrics

### Available Metrics

#### HTTP Metrics
- `http_requests_total` - Total requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current requests in progress

#### Database Metrics
- `db_queries_total` - Total queries by operation, table, status
- `db_query_duration_seconds` - Query duration histogram
- `db_connection_pool_size` - Connection pool size
- `db_connection_pool_available` - Available connections

#### LLM Metrics
- `llm_api_calls_total` - Total API calls by provider, model, status
- `llm_api_duration_seconds` - API call duration histogram
- `llm_tokens_total` - Total tokens used
- `llm_estimated_cost_usd` - Estimated API costs

#### Agent Metrics
- `agent_executions_total` - Total agent executions by name, stage, status
- `agent_execution_duration_seconds` - Agent execution duration

#### Business Metrics
- `applications_total` - Total applications by status
- `jobs_processed_total` - Total jobs processed by platform
- `users_total` - Total users
- `active_users_total` - Active users (last 24h)

### Accessing Metrics

Metrics are available at: `http://localhost:8000/metrics`

Example output:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/jobs/search",status_code="200"} 1234

# HELP llm_tokens_total Total tokens used
# TYPE llm_tokens_total counter
llm_tokens_total{provider="openai",model="gpt-4o",type="total"} 45678
```

## Error Tracking (Sentry)

### Automatic Error Reporting

All unhandled exceptions are automatically reported to Sentry with:
- Full stack trace
- Request context
- User information
- Environment details
- Custom tags

### Manual Error Reporting

For handled errors that should be tracked:

```python
import sentry_sdk

try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.error("Operation failed", exc_info=True)
```

## Log Aggregation

### ELK Stack Integration

Logs are JSON-formatted for easy ingestion into ELK:

```json
{
  "@timestamp": "2025-10-05T19:31:25.123Z",
  "level": "INFO",
  "logger": "api.jobs",
  "message": "Job search completed",
  "request_id": "abc-123",
  "user_id": "user-789",
  "results_count": 15,
  "duration_ms": 234.56
}
```

### Datadog Integration

Logs include all necessary fields for Datadog:
- `timestamp` - ISO 8601 format
- `level` - Log level
- `logger` - Logger name
- `message` - Log message
- `request_id` - Trace ID
- Custom attributes

## Monitoring Dashboards

### Recommended Grafana Dashboards

1. **API Performance**
   - Request rate by endpoint
   - P50/P95/P99 latency
   - Error rate
   - Requests in progress

2. **Database Health**
   - Query duration
   - Connection pool usage
   - Slow queries
   - Error rate

3. **LLM Operations**
   - API call success rate
   - Token usage over time
   - Cost tracking
   - Response time

4. **Agent Performance**
   - Agent execution success rate
   - Execution duration by agent
   - Error rate by agent

5. **Business Metrics**
   - Applications created
   - Jobs processed
   - Active users
   - Conversion rates

### Alert Rules

Recommended Prometheus alert rules:

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowRequests
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        annotations:
          summary: "95th percentile latency > 2s"
          
      - alert: DatabasePoolExhaustion
        expr: db_connection_pool_available < 2
        for: 1m
        annotations:
          summary: "Database connection pool nearly exhausted"
```

## Best Practices

### DO

✅ Log at appropriate levels
✅ Include context in all logs
✅ Use structured logging
✅ Log errors with full stack traces
✅ Track performance metrics
✅ Use request IDs for tracing
✅ Log business events
✅ Monitor LLM costs

### DON'T

❌ Log sensitive data (passwords, API keys, PII)
❌ Log at DEBUG level in production
❌ Log inside tight loops
❌ Ignore errors silently
❌ Use print() statements
❌ Log without context
❌ Forget to log errors

## Example: Complete Request Flow

```python
# 1. Request arrives
# Middleware logs: "Request started"
logger.info("Request started", extra={"method": "GET", "path": "/api/v1/jobs/search"})

# 2. API endpoint logs
logger.info("Job search requested", extra={"user_id": "user-123", "limit": 20})

# 3. Database query logs
log_database_query("select", "user_profiles", duration=0.05)

# 4. Semantic matching logs
logger.debug("Finding compatible jobs")

# 5. Vector search logs
log_database_query("vector_search", "job_postings", duration=0.15)

# 6. Response logs
logger.info("Job search completed", extra={"results_count": 15, "duration_ms": 234.56})

# 7. Middleware logs: "Request completed"
logger.info("Request completed", extra={"status_code": 200, "duration_ms": 250.00})
```

All logs include the same `request_id` for easy tracing!

## Troubleshooting

### Finding Logs for a Specific Request

```bash
# Using request ID
grep "abc-123-def-456" logs/*.log

# Using ELK
request_id:"abc-123-def-456"

# Using Datadog
@request_id:abc-123-def-456
```

### Finding Slow Requests

```bash
# Logs with duration > 1000ms
grep "duration_ms" logs/*.log | awk '$NF > 1000'

# Using Prometheus
http_request_duration_seconds{quantile="0.95"} > 1
```

### Finding Errors

```bash
# All errors
grep "ERROR" logs/*.log

# Errors for specific user
grep "user-123" logs/*.log | grep "ERROR"

# Using Sentry
# Check Sentry dashboard for automatic error tracking
```

## Summary

This backend implements **production-grade logging and monitoring**:

✅ Structured JSON logging
✅ Distributed tracing with request IDs
✅ Comprehensive metrics (Prometheus)
✅ Error tracking (Sentry)
✅ Performance monitoring
✅ Business metrics
✅ Complete documentation

Every operation is logged, traced, and monitored for maximum observability in production!
