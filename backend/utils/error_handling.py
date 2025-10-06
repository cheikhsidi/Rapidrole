"""
Centralized error handling and custom exceptions.

This module provides:
- Custom exception classes
- Error response formatting
- Error logging and tracking
- Retry logic for transient failures
"""

from typing import Any

from fastapi import HTTPException, status

from utils.logging import get_logger, log_security_event

logger = get_logger(__name__)


class JobCopilotError(Exception):
    """Base exception for Job Copilot application"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

        # Log the exception
        logger.error(
            f"JobCopilotError: {message}",
            extra={
                "error_code": error_code,
                "details": details,
            },
        )


class DatabaseError(JobCopilotError):
    """Database-related errors"""

    pass


class AIServiceError(JobCopilotError):
    """AI/LLM service errors"""

    pass


class EmbeddingError(JobCopilotError):
    """Embedding generation errors"""

    pass


class ValidationError(JobCopilotError):
    """Data validation errors"""

    pass


class AuthenticationError(JobCopilotError):
    """Authentication errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "AUTH_ERROR", details)

        # Log security event
        log_security_event(
            event_type="authentication_failure", severity="medium", details=details or {}
        )


class AuthorizationError(JobCopilotError):
    """Authorization errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "AUTHZ_ERROR", details)

        # Log security event
        log_security_event(
            event_type="authorization_failure", severity="medium", details=details or {}
        )


class RateLimitError(JobCopilotError):
    """Rate limit exceeded"""

    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(message, "RATE_LIMIT", details)

        # Log security event
        log_security_event(event_type="rate_limit_exceeded", severity="low", details=details or {})


class ResourceNotFoundError(JobCopilotError):
    """Resource not found"""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(
            message, "NOT_FOUND", {"resource_type": resource_type, "resource_id": resource_id}
        )


def handle_database_error(error: Exception, operation: str) -> None:
    """
    Handle database errors with proper logging.

    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
    """
    logger.error(
        f"Database error during {operation}",
        extra={
            "operation": operation,
            "error": str(error),
            "error_type": type(error).__name__,
        },
        exc_info=True,
    )

    raise DatabaseError(
        message=f"Database operation failed: {operation}",
        error_code="DB_ERROR",
        details={"operation": operation, "error": str(error)},
    )


def handle_ai_service_error(error: Exception, service: str, operation: str) -> None:
    """
    Handle AI service errors with proper logging.

    Args:
        error: The exception that occurred
        service: Name of the AI service (openai, anthropic, etc.)
        operation: Description of the operation that failed
    """
    logger.error(
        f"AI service error: {service} - {operation}",
        extra={
            "service": service,
            "operation": operation,
            "error": str(error),
            "error_type": type(error).__name__,
        },
        exc_info=True,
    )

    raise AIServiceError(
        message=f"AI service operation failed: {operation}",
        error_code="AI_SERVICE_ERROR",
        details={"service": service, "operation": operation, "error": str(error)},
    )


def create_http_exception(
    status_code: int,
    message: str,
    error_code: str | None = None,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """
    Create a properly formatted HTTP exception.

    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Application-specific error code
        details: Additional error details

    Returns:
        HTTPException with formatted detail
    """
    detail = {
        "message": message,
        "error_code": error_code,
    }

    if details:
        detail["details"] = details

    return HTTPException(status_code=status_code, detail=detail)


# Common HTTP exceptions
def not_found_exception(resource_type: str, resource_id: str) -> HTTPException:
    """Create a 404 Not Found exception"""
    return create_http_exception(
        status_code=status.HTTP_404_NOT_FOUND,
        message=f"{resource_type} not found",
        error_code="NOT_FOUND",
        details={"resource_type": resource_type, "resource_id": resource_id},
    )


def validation_exception(message: str, details: dict[str, Any] | None = None) -> HTTPException:
    """Create a 422 Validation Error exception"""
    return create_http_exception(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
        error_code="VALIDATION_ERROR",
        details=details,
    )


def unauthorized_exception(message: str = "Unauthorized") -> HTTPException:
    """Create a 401 Unauthorized exception"""
    return create_http_exception(
        status_code=status.HTTP_401_UNAUTHORIZED, message=message, error_code="UNAUTHORIZED"
    )


def forbidden_exception(message: str = "Forbidden") -> HTTPException:
    """Create a 403 Forbidden exception"""
    return create_http_exception(
        status_code=status.HTTP_403_FORBIDDEN, message=message, error_code="FORBIDDEN"
    )


def rate_limit_exception(retry_after: int | None = None) -> HTTPException:
    """Create a 429 Rate Limit Exceeded exception"""
    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "message": "Rate limit exceeded",
            "error_code": "RATE_LIMIT",
            "retry_after": retry_after,
        },
        headers=headers,
    )


def internal_server_exception(message: str = "Internal server error") -> HTTPException:
    """Create a 500 Internal Server Error exception"""
    return create_http_exception(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=message,
        error_code="INTERNAL_ERROR",
    )
