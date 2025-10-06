"""
Prometheus metrics for monitoring application performance.

This module provides:
- Request metrics (count, duration, errors)
- Database metrics (query count, duration, pool stats)
- AI/LLM metrics (API calls, tokens, costs)
- Business metrics (applications, jobs, users)
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# Application info
app_info = Info("job_copilot_app", "Application information")
app_info.info(
    {
        "version": "0.1.0",
        "name": "Job Copilot API",
    }
)

# Request metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress", "Number of HTTP requests in progress", ["method", "endpoint"]
)

# Database metrics
db_queries_total = Counter(
    "db_queries_total", "Total database queries", ["operation", "table", "status"]
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

db_connection_pool_size = Gauge("db_connection_pool_size", "Database connection pool size")

db_connection_pool_available = Gauge(
    "db_connection_pool_available", "Available database connections"
)

# Redis metrics
redis_operations_total = Counter(
    "redis_operations_total", "Total Redis operations", ["operation", "status"]
)

redis_operation_duration_seconds = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1],
)

# AI/LLM metrics
llm_api_calls_total = Counter(
    "llm_api_calls_total", "Total LLM API calls", ["provider", "model", "status"]
)

llm_api_duration_seconds = Histogram(
    "llm_api_duration_seconds",
    "LLM API call duration in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens used",
    ["provider", "model", "type"],  # type: prompt, completion, total
)

llm_estimated_cost_usd = Counter(
    "llm_estimated_cost_usd", "Estimated LLM API cost in USD", ["provider", "model"]
)

# Embedding metrics
embedding_operations_total = Counter(
    "embedding_operations_total", "Total embedding operations", ["status"]
)

embedding_duration_seconds = Histogram(
    "embedding_duration_seconds",
    "Embedding generation duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
)

# Agent metrics
agent_executions_total = Counter(
    "agent_executions_total", "Total agent executions", ["agent_name", "stage", "status"]
)

agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name", "stage"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

# Business metrics
applications_total = Counter("applications_total", "Total job applications", ["status"])

jobs_processed_total = Counter("jobs_processed_total", "Total jobs processed", ["platform"])

users_total = Gauge("users_total", "Total number of users")

active_users_total = Gauge("active_users_total", "Number of active users (last 24h)")

# Vector search metrics
vector_search_operations_total = Counter(
    "vector_search_operations_total", "Total vector search operations", ["status"]
)

vector_search_duration_seconds = Histogram(
    "vector_search_duration_seconds",
    "Vector search duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
)

vector_search_results_count = Histogram(
    "vector_search_results_count",
    "Number of results returned by vector search",
    buckets=[1, 5, 10, 20, 50, 100],
)


def track_request(method: str, endpoint: str, status_code: int, duration: float):
    """Track HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_db_query(operation: str, table: str, duration: float, success: bool = True):
    """Track database query metrics"""
    status = "success" if success else "error"

    db_queries_total.labels(operation=operation, table=table, status=status).inc()

    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def track_llm_call(
    provider: str, model: str, duration: float, tokens: int | None = None, success: bool = True
):
    """Track LLM API call metrics"""
    status = "success" if success else "error"

    llm_api_calls_total.labels(provider=provider, model=model, status=status).inc()

    llm_api_duration_seconds.labels(provider=provider, model=model).observe(duration)

    if tokens:
        llm_tokens_total.labels(provider=provider, model=model, type="total").inc(tokens)

        # Estimate cost (approximate rates)
        cost = estimate_llm_cost(provider, model, tokens)
        if cost:
            llm_estimated_cost_usd.labels(provider=provider, model=model).inc(cost)


def track_agent_execution(agent_name: str, stage: str, duration: float, success: bool = True):
    """Track agent execution metrics"""
    status = "success" if success else "error"

    agent_executions_total.labels(agent_name=agent_name, stage=stage, status=status).inc()

    agent_execution_duration_seconds.labels(agent_name=agent_name, stage=stage).observe(duration)


def track_vector_search(duration: float, results_count: int, success: bool = True):
    """Track vector search metrics"""
    status = "success" if success else "error"

    vector_search_operations_total.labels(status=status).inc()
    vector_search_duration_seconds.observe(duration)
    vector_search_results_count.observe(results_count)


def estimate_llm_cost(provider: str, model: str, tokens: int) -> float | None:
    """
    Estimate LLM API cost based on provider and model.

    Note: These are approximate rates and should be updated regularly.
    """
    # Approximate costs per 1M tokens (as of 2024)
    rates = {
        "openai": {
            "gpt-4o": 0.005,  # $5 per 1M tokens (average)
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.001,
            "text-embedding-3-small": 0.00002,
        },
        "anthropic": {
            "claude-3-5-sonnet-20241022": 0.003,  # $3 per 1M tokens (average)
            "claude-3-opus": 0.015,
        },
    }

    if provider in rates and model in rates[provider]:
        return (tokens / 1_000_000) * rates[provider][model]

    return None
