"""
Global error handling middleware for the FastAPI application.

This module provides centralized error handling with:
- Custom exception handling
- HTTP exception handling
- Validation error handling
- Generic exception handling
- Structured error responses
"""

import logging
import traceback
from typing import Optional, Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error exception."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(APIError):
    """Resource not found exception."""

    def __init__(self, message: str, resource_type: Optional[str] = None):
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class ConflictError(APIError):
    """Resource conflict exception."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class UnauthorizedError(APIError):
    """Unauthorized access exception."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


class ForbiddenError(APIError):
    """Forbidden access exception."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
        )


class ServiceUnavailableError(APIError):
    """Service unavailable exception."""

    def __init__(self, message: str, service_name: Optional[str] = None):
        details = {"service_name": service_name} if service_name else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
        )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors with correlation ID."""
    # Get correlation ID from request state
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"API Error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "correlation_id": correlation_id,
            "request_id": request_id,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": correlation_id,
                "request_id": request_id,
            }
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with correlation ID."""
    # Get correlation ID from request state
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "correlation_id": correlation_id,
            "request_id": request_id,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
                "correlation_id": correlation_id,
                "request_id": request_id,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with correlation ID."""
    # Get correlation ID from request state
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)
    
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation Error: {len(errors)} validation errors",
        extra={
            "errors": errors,
            "path": request.url.path,
            "correlation_id": correlation_id,
            "request_id": request_id,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors},
                "correlation_id": correlation_id,
                "request_id": request_id,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions with proper production/development handling."""
    # Get correlation ID from request state
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "traceback": traceback.format_exc(),
            "correlation_id": correlation_id,
            "request_id": request_id,
        },
    )

    # In production, hide internal error details for security
    # In development, expose details for debugging
    if settings.environment == "production":
        error_message = "An internal error occurred. Please try again later."
        error_details = {}
    else:
        # Development mode: expose error details for debugging
        error_message = f"{type(exc).__name__}: {str(exc)}"
        error_details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc().split("\n") if settings.debug else None,
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": error_message,
                "details": error_details,
                "correlation_id": correlation_id,
                "request_id": request_id,
            }
        },
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

# Made with Bob
