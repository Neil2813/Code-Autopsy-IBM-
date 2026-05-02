# for IBM hackathon
"""
Analysis-related Pydantic schemas.

This module contains schemas for:
- Analysis requests
- Analysis configuration
- Analysis triggers
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import LanguageEnum


class AnalysisConfig(BaseModel):
    """Configuration for analysis job."""

    enable_mcp: bool = Field(True, description="Enable MCP solution retrieval")
    enable_dependency_analysis: bool = Field(True, description="Enable dependency graph generation")
    enable_risk_detection: bool = Field(True, description="Enable risk detection")
    enable_suggestion_generation: bool = Field(True, description="Enable modernization suggestions")
    max_file_size_mb: int = Field(10, ge=1, le=100, description="Maximum file size to analyze (MB)")
    languages_to_analyze: Optional[List[LanguageEnum]] = Field(
        None, description="Specific languages to analyze (None = all detected)"
    )
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Specific focus areas (security, performance, maintainability, etc.)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "enable_mcp": True,
                "enable_dependency_analysis": True,
                "enable_risk_detection": True,
                "enable_suggestion_generation": True,
                "max_file_size_mb": 10,
                "languages_to_analyze": ["java"],
                "focus_areas": ["security", "maintainability"],
            }
        }


class AnalyzeRequest(BaseModel):
    """Request schema for starting analysis."""

    job_id: str = Field(..., description="Job ID from upload response")
    config: Optional[AnalysisConfig] = Field(None, description="Analysis configuration")
    priority: str = Field("normal", description="Job priority (low, normal, high)")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "config": {
                    "enable_mcp": True,
                    "enable_dependency_analysis": True,
                    "enable_risk_detection": True,
                    "enable_suggestion_generation": True,
                    "focus_areas": ["security"],
                },
                "priority": "high",
            }
        }


class AnalyzeResponse(BaseModel):
    """Response schema for analysis completion (synchronous execution)."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Final status (completed or failed)")
    message: str = Field(..., description="Status message")
    estimated_duration_seconds: Optional[int] = Field(
        None,
        description="Not applicable for synchronous execution (always None)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "status": "completed",
                "message": "Analysis completed successfully",
                "estimated_duration_seconds": None,
            }
        }

# Made with Bob
