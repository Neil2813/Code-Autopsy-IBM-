"""
Logging middleware for request/response tracking.

This module provides:
- Request logging with timing
- Response logging with status codes
- Correlation ID tracking
- Structured logging
"""

import logging
import logging.config
import time
import uuid
import json
from typing import Callable, Any, Dict
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation_id and request_id if available
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_data["request_id"] = request_id
        
        # Add extra fields using getattr to avoid type checker warnings
        method = getattr(record, "method", None)
        if method:
            log_data["method"] = method
        
        path = getattr(record, "path", None)
        if path:
            log_data["path"] = path
        
        status_code = getattr(record, "status_code", None)
        if status_code:
            log_data["status_code"] = status_code
        
        process_time = getattr(record, "process_time", None)
        if process_time:
            log_data["process_time"] = process_time
        
        client_host = getattr(record, "client_host", None)
        if client_host:
            log_data["client_host"] = client_host
        
        user_agent = getattr(record, "user_agent", None)
        if user_agent:
            log_data["user_agent"] = user_agent
        
        error_code = getattr(record, "error_code", None)
        if error_code:
            log_data["error_code"] = error_code
        
        exception_type = getattr(record, "exception_type", None)
        if exception_type:
            log_data["exception_type"] = exception_type
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add traceback if available
        traceback_info = getattr(record, "traceback", None)
        if traceback_info:
            log_data["traceback"] = traceback_info
        
        return json.dumps(log_data)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log exception with correlation_id and request_id
            process_time = time.time() - start_time
            request_id = getattr(request.state, "request_id", None)
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": f"{process_time:.3f}s",
                    "exception": str(exc),
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )
            raise

        # Calculate process time
        process_time = time.time() - start_time

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}s"

        # Log response with request_id
        request_id = getattr(request.state, "request_id", None)
        log_level = logging.INFO if response.status_code < 400 else logging.WARNING
        logger.log(
            log_level,
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "correlation_id": correlation_id,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
            },
        )

        return response


def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """
    Configure application logging with structured JSON output support.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'text')
    """
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Choose formatter based on format type
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Configure root logger with handler
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler with chosen formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers = [
        "app",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)

    # Reduce noise from some libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, format={log_format}")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

# Made with Bob
