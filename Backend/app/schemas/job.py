# for IBM hackathon
"""
Job-related Pydantic schemas.

This module contains schemas for:
- Job status tracking
- Job progress updates
- Job results
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import (
    DependencyGraph,
    FileReference,
    JobStatusEnum,
    LanguageEnum,
    PriorityEnum,
    SeverityEnum,
    TimestampMixin,
)


class JobStageProgress(BaseModel):
    """Progress information for a job stage."""

    stage_name: str = Field(..., description="Stage name")
    status: str = Field(..., description="Stage status (pending, running, completed, failed)")
    progress_percent: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    started_at: Optional[datetime] = Field(None, description="Stage start time")
    completed_at: Optional[datetime] = Field(None, description="Stage completion time")

    class Config:
        json_schema_extra = {
            "example": {
                "stage_name": "parse",
                "status": "completed",
                "progress_percent": 100.0,
                "message": "Parsed 10 files successfully",
                "started_at": "2024-01-01T00:00:00Z",
                "completed_at": "2024-01-01T00:01:00Z",
            }
        }


class JobStatusResponse(TimestampMixin, BaseModel):
    """Response schema for job status queries."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusEnum = Field(..., description="Current job status")
    progress_percent: float = Field(0.0, ge=0.0, le=100.0, description="Overall progress percentage")
    message: str = Field(..., description="Current status message")
    stages: List[JobStageProgress] = Field(default_factory=list, description="Progress of each stage")
    current_stage: Optional[str] = Field(None, description="Currently executing stage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "status": "running",
                "progress_percent": 45.0,
                "message": "Analyzing code structure...",
                "stages": [
                    {
                        "stage_name": "ingest",
                        "status": "completed",
                        "progress_percent": 100.0,
                        "message": "Ingested 10 files",
                    },
                    {
                        "stage_name": "parse",
                        "status": "running",
                        "progress_percent": 50.0,
                        "message": "Parsing file 5 of 10",
                    },
                ],
                "current_stage": "parse",
                "estimated_completion": "2024-01-01T00:10:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:05:00Z",
            }
        }


class RiskItem(BaseModel):
    """Schema for a detected risk."""

    risk_id: str = Field(..., description="Unique risk identifier")
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="Detailed risk description")
    severity: SeverityEnum = Field(..., description="Risk severity level")
    category: str = Field(..., description="Risk category (security, maintainability, performance, etc.)")
    affected_files: List[FileReference] = Field(..., description="Files affected by this risk")
    recommendation: str = Field(..., description="Recommendation to address the risk")
    line_start: Optional[int] = Field(None, description="Primary affected line number")
    line_end: Optional[int] = Field(None, description="Primary affected ending line number")
    code_snippet: Optional[str] = Field(None, description="Minimal affected code snippet")
    mcp_solution_available: bool = Field(False, description="Whether MCP has a solution for this risk")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "risk_id": "r123e456-e89b-12d3-a456-426614174000",
                "title": "Hard-coded database credentials",
                "description": "Database credentials are hard-coded in the source file",
                "severity": "critical",
                "category": "security",
                "affected_files": [
                    {
                        "file_path": "src/main/java/com/example/DatabaseConfig.java",
                        "line_start": 15,
                        "line_end": 17,
                    }
                ],
                "recommendation": "Move credentials to environment variables or secure vault",
                "mcp_solution_available": True,
                "confidence": 0.95,
            }
        }


class ModernizationSuggestion(BaseModel):
    """Schema for a modernization suggestion."""

    suggestion_id: str = Field(..., description="Unique suggestion identifier")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed suggestion description")
    priority: PriorityEnum = Field(..., description="Suggestion priority")
    category: str = Field(..., description="Suggestion category (refactoring, architecture, framework, etc.)")
    affected_files: List[FileReference] = Field(..., description="Files affected by this suggestion")
    implementation_guide: str = Field(..., description="Step-by-step implementation guide")
    estimated_effort: str = Field(..., description="Estimated effort (small, medium, large, xlarge)")
    benefits: List[str] = Field(..., description="Expected benefits")
    risks: List[str] = Field(default_factory=list, description="Potential risks of implementing")
    mcp_solution_available: bool = Field(False, description="Whether MCP has a solution")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "suggestion_id": "s123e456-e89b-12d3-a456-426614174000",
                "title": "Extract database logic to repository pattern",
                "description": "Database access is scattered across service classes",
                "priority": "high",
                "category": "refactoring",
                "affected_files": [
                    {"file_path": "src/main/java/com/example/UserService.java"},
                    {"file_path": "src/main/java/com/example/OrderService.java"},
                ],
                "implementation_guide": "1. Create repository interfaces\n2. Implement repositories\n3. Inject into services",
                "estimated_effort": "medium",
                "benefits": ["Improved testability", "Better separation of concerns", "Easier to maintain"],
                "risks": ["Requires refactoring existing tests"],
                "mcp_solution_available": True,
                "confidence": 0.88,
            }
        }


class ArchitectureSummary(BaseModel):
    """Schema for architecture summary."""

    project_type: str = Field(..., description="Detected project type (monolith, microservice, etc.)")
    primary_language: LanguageEnum = Field(..., description="Primary programming language")
    detected_frameworks: List[str] = Field(..., description="Detected frameworks and libraries")
    architecture_patterns: List[str] = Field(..., description="Detected architecture patterns")
    layers: Dict[str, List[str]] = Field(..., description="Detected layers and their components")
    entry_points: List[FileReference] = Field(..., description="Application entry points")
    dependency_graph: DependencyGraph = Field(..., description="Dependency graph")

    class Config:
        json_schema_extra = {
            "example": {
                "project_type": "monolith",
                "primary_language": "java",
                "detected_frameworks": ["Spring Boot 2.5", "Hibernate 5.4"],
                "architecture_patterns": ["MVC", "Repository Pattern"],
                "layers": {
                    "controller": ["UserController", "OrderController"],
                    "service": ["UserService", "OrderService"],
                    "repository": ["UserRepository", "OrderRepository"],
                },
                "entry_points": [{"file_path": "src/main/java/com/example/Application.java"}],
                "dependency_graph": {"nodes": [], "edges": []},
            }
        }


class JobResultResponse(TimestampMixin, BaseModel):
    """Response schema for completed job results."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusEnum = Field(..., description="Job status")
    summary: str = Field(..., description="High-level summary of analysis")
    architecture: ArchitectureSummary = Field(..., description="Architecture analysis")
    risks: List[RiskItem] = Field(..., description="Detected risks")
    suggestions: List[ModernizationSuggestion] = Field(..., description="Modernization suggestions")
    migration_blockers: List[str] = Field(..., description="Critical migration blockers")
    recommended_next_steps: List[str] = Field(..., description="Recommended next steps")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "status": "completed",
                "summary": "Analyzed Java Spring Boot monolith with 50 files. Found 5 critical risks and 12 modernization opportunities.",
                "architecture": {
                    "project_type": "monolith",
                    "primary_language": "java",
                    "detected_frameworks": ["Spring Boot 2.5"],
                    "architecture_patterns": ["MVC"],
                    "layers": {},
                    "entry_points": [],
                    "dependency_graph": {"nodes": [], "edges": []},
                },
                "risks": [],
                "suggestions": [],
                "migration_blockers": ["Hard-coded credentials", "Tight coupling to legacy database"],
                "recommended_next_steps": [
                    "Address critical security risks",
                    "Refactor database access layer",
                    "Update to Spring Boot 3.x",
                ],
                "metadata": {"total_files": 50, "total_lines": 5000},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:10:00Z",
            }
        }

# Made with Bob
