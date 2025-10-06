"""
Distributed tracing and request tracking utilities.

Provides:
- Request ID generation and propagation
- Performance monitoring decorators
- Context management for async operations
- Trace correlation across services
"""

import time
import uuid
import functools
from typing import Callable, Any, Optional
from contextvars import ContextVar

from utils.logging import (
    request_id_var,
    user_id_var,
    log_execution_time,
    get_logger,
)

logger = get_logger(__name__)


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())


def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """Set request context for tracing"""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def get_request_id() -> Optional[str]:
    """Get current request ID from context"""
    return request_id_var.get()


def get_user_id() -> Optional[str]:
    """Get current user ID from context"""
    return user_id_var.get()


def trace_function(func_name: Optional[str] = None):
    """
    Decorator to trace function execution time and log errors.
    
    Usage:
        @trace_function()
        async def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        name = func_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                logger.debug(f"Starting {name}")
                result = await func(*args, **kwargs)
                log_execution_time(name, start_time)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function {name} failed",
                    extra={
                        "function": name,
                        "duration_ms": round(duration * 1000, 2),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                logger.debug(f"Starting {name}")
                result = func(*args, **kwargs)
                log_execution_time(name, start_time)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function {name} failed",
                    extra={
                        "function": name,
                        "duration_ms": round(duration * 1000, 2),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                raise
        
        # Return appropriate wrapper based on function type
        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class TraceContext:
    """Context manager for tracing operations"""
    
    def __init__(self, operation_name: str, metadata: Optional[dict] = None):
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.start_time = None
        self.logger = get_logger("tracing")
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(
            f"Starting operation: {self.operation_name}",
            extra={"operation": self.operation_name, **self.metadata}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_ms": round(duration * 1000, 2),
                    "success": True,
                    **self.metadata,
                }
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_ms": round(duration * 1000, 2),
                    "success": False,
                    "error": str(exc_val),
                    "error_type": exc_type.__name__,
                    **self.metadata,
                },
                exc_info=True,
            )
        
        return False  # Don't suppress exceptions


class AsyncTraceContext:
    """Async context manager for tracing operations"""
    
    def __init__(self, operation_name: str, metadata: Optional[dict] = None):
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.start_time = None
        self.logger = get_logger("tracing")
    
    async def __aenter__(self):
        self.start_time = time.time()
        self.logger.debug(
            f"Starting async operation: {self.operation_name}",
            extra={"operation": self.operation_name, **self.metadata}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                f"Async operation completed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_ms": round(duration * 1000, 2),
                    "success": True,
                    **self.metadata,
                }
            )
        else:
            self.logger.error(
                f"Async operation failed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_ms": round(duration * 1000, 2),
                    "success": False,
                    "error": str(exc_val),
                    "error_type": exc_type.__name__,
                    **self.metadata,
                },
                exc_info=True,
            )
        
        return False  # Don't suppress exceptions
