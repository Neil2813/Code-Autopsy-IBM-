"""
MCP Type Definitions

Pydantic models for MCP solution server data structures.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MCPViolation(BaseModel):
    """Represents a code violation detected by analysis."""
    
    violation_name: str = Field(..., description="Name of the violation")
    description: Optional[str] = Field(None, description="Violation description")
    category: Optional[str] = Field(None, description="Violation category")
    labels: List[str] = Field(default_factory=list, description="Associated labels")
    file_path: str = Field(..., description="File where violation occurred")
    line_number: Optional[int] = Field(None, description="Line number")
    code_snippet: Optional[str] = Field(None, description="Code snippet")


class MCPSolution(BaseModel):
    """Represents a solved migration example from MCP."""
    
    solution_id: str = Field(..., description="Unique solution identifier")
    violation: MCPViolation = Field(..., description="Original violation")
    
    # Solution details
    original_code: str = Field(..., description="Original legacy code")
    updated_code: str = Field(..., description="Modernized code")
    explanation: Optional[str] = Field(None, description="Explanation of changes")
    
    # Metadata
    language: str = Field(..., description="Programming language")
    framework_from: Optional[str] = Field(None, description="Source framework")
    framework_to: Optional[str] = Field(None, description="Target framework")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Usage tracking
    times_used: int = Field(default=0, description="Number of times solution was used")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional context
    tags: List[str] = Field(default_factory=list)
    related_violations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPQuery(BaseModel):
    """Query parameters for searching MCP solutions."""
    
    # Search criteria
    violation_name: Optional[str] = None
    category: Optional[str] = None
    labels: Optional[List[str]] = None
    language: Optional[str] = None
    framework_from: Optional[str] = None
    framework_to: Optional[str] = None
    
    # Code similarity
    code_snippet: Optional[str] = None
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Filtering
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    min_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Pagination
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MCPSearchResult(BaseModel):
    """Result of MCP solution search."""
    
    solutions: List[MCPSolution] = Field(default_factory=list)
    total_count: int = Field(default=0, description="Total matching solutions")
    query: MCPQuery = Field(..., description="Original query")
    search_time_ms: float = Field(default=0.0, description="Search duration")


class MCPStoreSolutionRequest(BaseModel):
    """Request to store a new solution in MCP."""
    
    violation: MCPViolation
    original_code: str
    updated_code: str
    explanation: Optional[str] = None
    language: str
    framework_from: Optional[str] = None
    framework_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPSolutionFeedback(BaseModel):
    """Feedback on solution usage."""
    
    solution_id: str
    was_helpful: bool
    was_applied: bool
    user_notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Made with Bob
