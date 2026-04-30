"""
AI Legacy Modernization Copilot - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config.settings import get_settings
from app.middleware.error_handler import error_handler_middleware
from app.middleware.logging_middleware import logging_middleware
from app.api.v1 import upload, analyze, jobs, query, report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered legacy code modernization platform with LangGraph and MCP",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(error_handler_middleware)
app.middleware("http")(logging_middleware)

# Include API routers
app.include_router(upload.router, prefix=settings.api_prefix, tags=["Upload"])
app.include_router(analyze.router, prefix=settings.api_prefix, tags=["Analysis"])
app.include_router(jobs.router, prefix=settings.api_prefix, tags=["Jobs"])
app.include_router(query.router, prefix=settings.api_prefix, tags=["Query"])
app.include_router(report.router, prefix=settings.api_prefix, tags=["Report"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Legacy Modernization Copilot API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }


@app.get(f"{settings.api_prefix}/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.app_version
    }


@app.get(f"{settings.api_prefix}/status")
async def status_check():
    """Detailed status check including LLM providers and MCP"""
    # TODO: Add actual health checks for dependencies
    return {
        "api": "operational",
        "database": "operational",
        "redis": "operational",
        "llm_providers": {
            "primary": "operational",
            "groq": "operational",
            "rule_based": "operational"
        },
        "mcp_server": "operational"
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    # TODO: Initialize database connections, Redis, MCP client


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down application")
    # TODO: Close database connections, Redis, MCP client


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

# Made with Bob
