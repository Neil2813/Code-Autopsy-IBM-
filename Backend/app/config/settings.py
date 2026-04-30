"""
Application Settings and Configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "AI Legacy Modernization Copilot"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Database
    database_type: str = "postgresql"
    database_url: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    
    # LLM Providers
    primary_llm_provider: str = "openai"
    primary_llm_model: str = "gpt-4"
    primary_llm_api_key: str
    
    groq_llm_api_key: str
    groq_llm_model: str = "mixtral-8x7b-32768"
    
    # MCP
    mcp_server_path: str = "./mcp_server"
    mcp_db_dsn: str
    
    # Storage
    storage_type: str = "local"
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    max_upload_size_mb: int = 100
    
    # Security
    secret_key: str
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Job Queue
    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Made with Bob
