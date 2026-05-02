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
from typing import Dict, Any

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

# Global state for health checks
_health_state: Dict[str, Any] = {
    "database": "initializing",
    "redis": "initializing",
    "mcp": "initializing",
    "llm_providers": {}
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with proper initialization and cleanup."""
    # Startup
    logger.info("Starting AI Legacy Modernization Copilot Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'SQLite'}")
    logger.info(f"API: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"Docs: http://{settings.api_host}:{settings.api_port}/docs")
    
    # Initialize database
    try:
        from app.storage.database import init_db_async
        await init_db_async()
        _health_state["database"] = "healthy"
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        _health_state["database"] = "unhealthy"
        logger.error(f"✗ Database initialization failed: {e}")
    
    # Initialize MCP client
    try:
        from app.mcp.client import initialize_mcp_client
        mcp_client = await initialize_mcp_client()
        if mcp_client.is_available():
            _health_state["mcp"] = "healthy"
            logger.info("✓ MCP client initialized successfully")
        else:
            _health_state["mcp"] = "disabled"
            logger.info("○ MCP client disabled or in mock mode")
    except Exception as e:
        _health_state["mcp"] = "unhealthy"
        logger.error(f"✗ MCP initialization failed: {e}")
    
    # Warmup LLM providers
    try:
        from app.llm.provider_chain import get_llm_chain
        provider_chain = get_llm_chain()
        _health_state["llm_providers"]["rule_based"] = "available"
        
        # Test primary provider availability
        if settings.primary_llm_provider == "watsonx" and settings.watsonx_api_key:
            _health_state["llm_providers"]["watsonx"] = "available"
            logger.info("✓ Watsonx provider configured")
        elif settings.primary_llm_provider == "openai" and settings.openai_api_key:
            _health_state["llm_providers"]["openai"] = "available"
            logger.info("✓ OpenAI provider configured")
        
        if settings.groq_api_key:
            _health_state["llm_providers"]["groq"] = "available"
            logger.info("✓ Groq provider configured")
            
        logger.info("✓ LLM provider chain initialized")
    except Exception as e:
        _health_state["llm_providers"]["error"] = str(e)
        logger.error(f"✗ LLM provider initialization failed: {e}")
    
    # Check Redis connectivity (optional)
    try:
        import redis.asyncio as redis  # type: ignore[import-untyped]
        redis_client = redis.from_url(settings.redis_url, password=settings.redis_password)
        await redis_client.ping()
        await redis_client.close()
        _health_state["redis"] = "healthy"
        logger.info("✓ Redis connection verified")
    except Exception as e:
        _health_state["redis"] = "unavailable"
        logger.warning(f"○ Redis not available: {e}")
    
    logger.info("=" * 60)
    logger.info("Backend startup complete - ready to accept requests")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Legacy Modernization Copilot Backend...")
    
    # Close MCP connection
    try:
        from app.mcp.client import shutdown_mcp_client
        await shutdown_mcp_client()
        logger.info("✓ MCP client shutdown complete")
    except Exception as e:
        logger.error(f"✗ MCP shutdown error: {e}")
    
    # Close database connections
    try:
        from app.storage.database import close_db
        await close_db()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"✗ Database shutdown error: {e}")
    
    logger.info("Shutdown complete")


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

# Configure CORS with proper validation
cors_origins = settings.allowed_origins
cors_credentials = settings.allow_credentials

# Prevent insecure CORS configuration
if cors_origins == ["*"] and cors_credentials:
    logger.warning("Insecure CORS: allow_origins=['*'] with allow_credentials=True")
    logger.warning("Disabling credentials to prevent security issue")
    cors_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api.v1 import analyze, code_review, dashboard, jobs, query, report, upload

app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(report.router, prefix="/api/v1", tags=["Report"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(code_review.router, prefix="/api/v1", tags=["Code Review"])


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
    Detailed status endpoint with real component health checks.
    
    Returns actual connectivity status for:
    - Database connectivity
    - Redis connectivity
    - MCP server connectivity
    - LLM provider availability
    """
    # Perform real-time health checks
    components = {
        "api": "healthy",
        "database": _health_state.get("database", "unknown"),
        "redis": _health_state.get("redis", "unknown"),
        "mcp": _health_state.get("mcp", "unknown"),
        "llm_providers": _health_state.get("llm_providers", {}),
    }
    
    # Check database connectivity in real-time
    try:
        from app.storage.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = "unhealthy"
        logger.error(f"Database health check failed: {e}")
    
    # Check MCP connectivity in real-time
    try:
        from app.mcp.client import get_mcp_client
        mcp_client = get_mcp_client()
        mcp_health = await mcp_client.health_check()
        components["mcp"] = mcp_health.get("status", "unknown")
    except Exception as e:
        components["mcp"] = "unhealthy"
        logger.error(f"MCP health check failed: {e}")
    
    # Determine overall status
    critical_components = ["api", "database"]
    is_operational = all(
        components.get(comp) == "healthy"
        for comp in critical_components
    )
    
    overall_status = "operational" if is_operational else "degraded"
    
    return {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "components": components,
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
