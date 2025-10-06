import json

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str
    redis_max_connections: int = 50

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # Application
    app_env: str = "development"
    secret_key: str
    cors_origins: str = '["http://localhost:3000"]'

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Monitoring
    enable_metrics: bool = True
    log_level: str = "INFO"
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1

    # Performance
    slow_request_threshold: float = 1.0

    # Email/SMTP (optional - for production)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@jobcopilot.com"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from JSON string with error handling."""
        try:
            return json.loads(self.cors_origins)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse CORS_ORIGINS: {self.cors_origins!r}. "
                "Please ensure it is a valid JSON array of origins. "
                f"Error: {e}"
            ) from e

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
