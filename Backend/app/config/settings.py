# for IBM hackathon
"""
Application Settings and Configuration
"""
from typing import List, Optional, Union
from pydantic import field_validator, validator
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
    database_type: str = "sqlite"
    database_url: str = "sqlite:///./legacy_modernization.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    
    # LLM Providers - Consolidated keys (set via environment variables)
    # IBM watsonx.ai (Primary)
    watsonx_api_key: Optional[str] = None
    watsonx_project_id: Optional[str] = None
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_model: str = "ibm/granite-13b-chat-v2"
    
    # OpenAI (Secondary)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    
    # Groq (Tertiary)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"
    
    # Primary provider selection
    primary_llm_provider: str = "watsonx"
    
    # MCP (Model Context Protocol) - Knowledge Layer
    mcp_enabled: bool = False  # MVP: Disabled by default, mock-only implementation
    mcp_server_path: str = "./mcp_server"
    mcp_db_dsn: str = "sqlite:///./mcp.db"
    mcp_timeout: int = 30  # Connection timeout in seconds
    mcp_max_retries: int = 3  # Maximum connection retry attempts
    mcp_retry_delay: int = 5  # Delay between retries in seconds
    mcp_mock_mode: bool = True  # MVP: Always use mock responses
    
    # Storage
    storage_type: str = "local"
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    max_upload_size_mb: int = 100
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    allowed_origins: Union[List[str], str] = "http://localhost:3000,http://localhost:8000"
    allow_credentials: bool = True
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse allowed_origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allow_credentials', always=True)
    @classmethod
    def validate_cors_credentials(cls, v, values):
        """
        Validate CORS configuration to prevent security issues.
        Setting allow_credentials=True with allow_origins=["*"] is not allowed.
        """
        origins = values.get('allowed_origins', [])
        if v and origins == ["*"]:
            raise ValueError(
                "allow_credentials=True cannot be used with allow_origins=['*']. "
                "Either set specific origins or disable credentials."
            )
        return v
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Job Queue
    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow validation to pass even if .env file doesn't exist
        env_file_encoding = 'utf-8'
        extra = 'ignore'


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()  # type: ignore[call-arg]


# Create a global settings instance
settings = get_settings()

# Made with Bob
