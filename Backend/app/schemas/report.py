"""
Report-related Pydantic schemas.

This module contains schemas for:
- Report generation requests
- Report responses
- Report formats
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReportFormatEnum(str, Enum):
    """Report format options."""

    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"


class ReportSectionEnum(str, Enum):
    """Report section options."""

    SUMMARY = "summary"
    ARCHITECTURE = "architecture"
    RISKS = "risks"
    SUGGESTIONS = "suggestions"
    DEPENDENCIES = "dependencies"
    MIGRATION_BLOCKERS = "migration_blockers"
    NEXT_STEPS = "next_steps"
    ALL = "all"


class ReportRequest(BaseModel):
    """Request schema for report generation."""

    job_id: str = Field(..., description="Job ID to generate report for")
    format: ReportFormatEnum = Field(ReportFormatEnum.MARKDOWN, description="Report format")
    sections: list[ReportSectionEnum] = Field(
        [ReportSectionEnum.ALL], description="Sections to include in report"
    )
    include_code_snippets: bool = Field(True, description="Include code snippets in report")
    include_dependency_graph: bool = Field(True, description="Include dependency graph visualization")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "format": "markdown",
                "sections": ["summary", "risks", "suggestions"],
                "include_code_snippets": True,
                "include_dependency_graph": False,
            }
        }


class ReportResponse(BaseModel):
    """Response schema for report generation."""

    report_id: str = Field(..., description="Unique report identifier")
    job_id: str = Field(..., description="Associated job ID")
    format: ReportFormatEnum = Field(..., description="Report format")
    download_url: Optional[str] = Field(None, description="URL to download the report")
    content: Optional[str] = Field(None, description="Report content (for markdown/json)")
    size_bytes: int = Field(..., description="Report size in bytes")
    generated_at: str = Field(..., description="Report generation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "r123e456-e89b-12d3-a456-426614174000",
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "format": "markdown",
                "download_url": "/api/v1/report/r123e456-e89b-12d3-a456-426614174000/download",
                "content": "# Modernization Report\n\n## Summary\n...",
                "size_bytes": 15360,
                "generated_at": "2024-01-01T00:00:00Z",
            }
        }


class ReportMetadata(BaseModel):
    """Metadata for generated report."""

    title: str = Field(..., description="Report title")
    job_id: str = Field(..., description="Associated job ID")
    generated_at: str = Field(..., description="Generation timestamp")
    total_files_analyzed: int = Field(..., description="Total files analyzed")
    total_risks_found: int = Field(..., description="Total risks found")
    total_suggestions: int = Field(..., description="Total suggestions")
    primary_language: str = Field(..., description="Primary language")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Legacy Application Modernization Report",
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "generated_at": "2024-01-01T00:00:00Z",
                "total_files_analyzed": 50,
                "total_risks_found": 15,
                "total_suggestions": 25,
                "primary_language": "java",
            }
        }

# Made with Bob
