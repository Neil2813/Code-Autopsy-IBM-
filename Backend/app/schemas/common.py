"""
Common Pydantic schemas used across the application.

This module contains shared schemas for:
- Error responses
- Pagination
- Common enums
- Base models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class JobStatusEnum(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LanguageEnum(str, Enum):
    """Supported programming languages."""

    JAVA = "java"
    COBOL = "cobol"
    RPG = "rpg"
    MAINFRAME = "mainframe"
    JCL = "jcl"
    UNKNOWN = "unknown"


class FileTypeEnum(str, Enum):
    """File type classification."""

    SOURCE = "source"
    CONFIG = "config"
    BUILD = "build"
    DOCUMENTATION = "documentation"
    TEST = "test"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class SeverityEnum(str, Enum):
    """Risk severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PriorityEnum(str, Enum):
    """Suggestion priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffortEnum(str, Enum):
    """Effort estimation levels."""

    SMALL = "small"  # < 1 day
    MEDIUM = "medium"  # 1-3 days
    LARGE = "large"  # 3-7 days
    XLARGE = "xlarge"  # > 1 week


# Base Models
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: Dict[str, Any] = Field(
        ...,
        description="Error information",
        example={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": [{"field": "file", "message": "File is required"}]},
        },
    )


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class FileReference(BaseModel):
    """Reference to a file in the codebase."""

    file_path: str = Field(..., description="Relative file path")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    snippet: Optional[str] = Field(None, description="Code snippet")


class DependencyNode(BaseModel):
    """Node in dependency graph."""

    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Module/class/function name")
    type: str = Field(..., description="Node type (module, class, function, etc.)")
    file_path: str = Field(..., description="File path")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DependencyEdge(BaseModel):
    """Edge in dependency graph."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Dependency type (import, call, inheritance, etc.)")
    weight: float = Field(1.0, description="Edge weight/strength")


class DependencyGraph(BaseModel):
    """Complete dependency graph."""

    nodes: List[DependencyNode] = Field(..., description="Graph nodes")
    edges: List[DependencyEdge] = Field(..., description="Graph edges")


class ConfidenceScore(BaseModel):
    """Confidence score for AI-generated content."""

    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    reasoning: Optional[str] = Field(None, description="Reasoning for the score")


class HealthStatus(BaseModel):
    """Health status response."""

    status: str = Field(..., description="Overall status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")


class DetailedStatus(BaseModel):
    """Detailed status response."""

    status: str = Field(..., description="Overall status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment name")
    components: Dict[str, Any] = Field(..., description="Component health status")


# Configuration
class Config:
    """Pydantic model configuration."""

    json_schema_extra = {
        "example": {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
    }

# Made with Bob
