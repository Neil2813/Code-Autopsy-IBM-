# for IBM hackathon
"""
Query-related Pydantic schemas.

This module contains schemas for:
- Natural language queries
- Query responses
- Query history
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import FileReference, TimestampMixin


class QueryRequest(BaseModel):
    """Request schema for natural language queries."""

    job_id: str = Field(..., description="Job ID to query about")
    question: str = Field(..., description="Natural language question", min_length=1, max_length=1000)
    context: Optional[str] = Field(None, description="Additional context for the question")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "question": "What are the most critical security risks in this codebase?",
                "context": "Focus on authentication and authorization",
            }
        }


class QueryResponse(TimestampMixin, BaseModel):
    """Response schema for query results."""

    query_id: str = Field(..., description="Unique query identifier")
    job_id: str = Field(..., description="Associated job ID")
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    references: List[FileReference] = Field(default_factory=list, description="Referenced files and locations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    mcp_solutions_used: int = Field(0, description="Number of MCP solutions referenced")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "q123e456-e89b-12d3-a456-426614174000",
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "question": "What are the most critical security risks?",
                "answer": "The most critical security risks are: 1. Hard-coded credentials in DatabaseConfig.java...",
                "references": [
                    {
                        "file_path": "src/main/java/com/example/DatabaseConfig.java",
                        "line_start": 15,
                        "line_end": 17,
                    }
                ],
                "confidence": 0.92,
                "mcp_solutions_used": 2,
                "follow_up_suggestions": [
                    "How can I fix the hard-coded credentials?",
                    "What other security issues should I address first?",
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }


class QueryHistoryItem(BaseModel):
    """Schema for query history item."""

    query_id: str = Field(..., description="Query identifier")
    question: str = Field(..., description="Question asked")
    answer_preview: str = Field(..., description="Preview of the answer (first 200 chars)")
    answer_full: Optional[str] = Field(None, description="Full answer text")
    confidence: float = Field(..., description="Confidence score")
    created_at: str = Field(..., description="Query timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "q123e456-e89b-12d3-a456-426614174000",
                "question": "What are the most critical security risks?",
                "answer_preview": "The most critical security risks are: 1. Hard-coded credentials...",
                "confidence": 0.92,
                "created_at": "2024-01-01T00:00:00Z",
            }
        }


class QueryHistoryResponse(BaseModel):
    """Response schema for query history."""

    job_id: str = Field(..., description="Job ID")
    queries: List[QueryHistoryItem] = Field(..., description="List of queries")
    total_queries: int = Field(..., description="Total number of queries")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "queries": [
                    {
                        "query_id": "q123e456-e89b-12d3-a456-426614174000",
                        "question": "What are the most critical security risks?",
                        "answer_preview": "The most critical security risks are...",
                        "confidence": 0.92,
                        "created_at": "2024-01-01T00:00:00Z",
                    }
                ],
                "total_queries": 1,
            }
        }

# Made with Bob
