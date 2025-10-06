"""
Centralized logging configuration with structured logging and tracing.

This module provides:
- Structured JSON logging for production
- Request ID tracking across all operations
- Correlation IDs for distributed tracing
- Performance metrics logging
- Error tracking with context
"""

import logging
import sys
import time
from contextvars import ContextVar
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from datetime import datetime

from config.settings import settings

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        
        # Add request context
        request_id = request_id_var.get()
        if request_id:
            log_record["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_record["user_id"] = user_id
        
        # Add environment
        log_record["environment"] = settings.app_env
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging() -> None:
    """Configure application logging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter for production, simple format for development
    if settings.app_env == "production":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin to add logging capabilities to classes"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return get_logger(self.__class__.__name__)


def log_execution_time(func_name: str, start_time: float) -> None:
    """Log execution time for a function"""
    duration = time.time() - start_time
    logger = get_logger("performance")
    logger.info(
        f"Function execution completed",
        extra={
            "function": func_name,
            "duration_ms": round(duration * 1000, 2),
        }
    )


def log_api_call(
    provider: str,
    model: str,
    tokens: Optional[int] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """Log external API calls (OpenAI, Anthropic, etc.)"""
    logger = get_logger("api_calls")
    
    log_data = {
        "provider": provider,
        "model": model,
    }
    
    if tokens:
        log_data["tokens"] = tokens
    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)
    if error:
        log_data["error"] = error
        logger.error("API call failed", extra=log_data)
    else:
        logger.info("API call completed", extra=log_data)


def log_database_query(
    operation: str,
    table: str,
    duration: float,
    rows_affected: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """Log database operations"""
    logger = get_logger("database")
    
    log_data = {
        "operation": operation,
        "table": table,
        "duration_ms": round(duration * 1000, 2),
    }
    
    if rows_affected is not None:
        log_data["rows_affected"] = rows_affected
    if error:
        log_data["error"] = error
        logger.error("Database operation failed", extra=log_data)
    else:
        logger.info("Database operation completed", extra=log_data)


def log_agent_execution(
    agent_name: str,
    stage: str,
    duration: Optional[float] = None,
    success: bool = True,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Log AI agent execution"""
    logger = get_logger("agents")
    
    log_data = {
        "agent": agent_name,
        "stage": stage,
        "success": success,
    }
    
    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)
    if error:
        log_data["error"] = error
    if metadata:
        log_data.update(metadata)
    
    if success:
        logger.info("Agent execution completed", extra=log_data)
    else:
        logger.error("Agent execution failed", extra=log_data)


def log_security_event(
    event_type: str,
    severity: str,
    details: Dict[str, Any],
) -> None:
    """Log security-related events"""
    logger = get_logger("security")
    
    log_data = {
        "event_type": event_type,
        "severity": severity,
        **details,
    }
    
    if severity in ["high", "critical"]:
        logger.error("Security event", extra=log_data)
    else:
        logger.warning("Security event", extra=log_data)


# Initialize logging on module import
setup_logging()
