"""
Main FastAPI application entry point.

This module initializes the FastAPI application with:
- CORS middleware
- Error handling middleware
- Logging middleware
- API routers
- Health check endpoints
- Application lifecycle events
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
    setup_logging,
)

settings = get_settings()

# Setup logging
setup_logging(log_level=settings.log_level, log_format="text")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting AI Legacy Modernization Copilot Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'SQLite'}")
    logger.info(f"API: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"Docs: http://{settings.api_host}:{settings.api_port}/docs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Legacy Modernization Copilot Backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered legacy code modernization platform with LangGraph and MCP",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register exception handlers
register_exception_handlers(app)

# Add middleware (order matters - last added is executed first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api.v1 import analyze, jobs, query, report, upload

app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(report.router, prefix="/api/v1", tags=["Report"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Legacy Modernization Copilot API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "status": "/status",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/status")
async def status_check():
    """
    Detailed status endpoint with component health checks.
    
    TODO: Add actual health checks for:
    - Database connectivity
    - Redis connectivity
    - MCP server connectivity
    - LLM provider availability
    """
    return {
        "status": "operational",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "components": {
            "api": "healthy",
            "database": "unknown",  # TODO: Add actual database check
            "redis": "unknown",  # TODO: Add actual Redis check
            "mcp": "unknown",  # TODO: Add actual MCP check
            "llm_providers": {
                "primary": "unknown",  # TODO: Add actual LLM check
                "groq": "unknown",
                "rule_based": "available",
            },
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )

# Made with Bob
