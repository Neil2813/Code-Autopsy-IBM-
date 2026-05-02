# for IBM hackathon
"""
MCP Type Definitions

Pydantic models for MCP solution server data structures.

These types define the contract between the application and the MCP server.
For real MCP implementation, ensure all fields match the actual server schema.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MCPViolation(BaseModel):
    """
    Represents a code violation detected by analysis.
    
    This matches the violation structure from analysis results and
    provides the context needed for solution matching.
    """
    
    violation_name: str = Field(..., description="Name of the violation")
    description: Optional[str] = Field(None, description="Violation description")
    category: Optional[str] = Field(None, description="Violation category")
    severity: Optional[str] = Field(None, description="Violation severity (low, medium, high, critical)")
    labels: List[str] = Field(default_factory=list, description="Associated labels")
    file_path: str = Field(..., description="File where violation occurred")
    line_number: Optional[int] = Field(None, description="Line number")
    line_end: Optional[int] = Field(None, description="End line number for multi-line violations")
    code_snippet: Optional[str] = Field(None, description="Code snippet")
    
    # Additional fields for real MCP server
    violation_id: Optional[str] = Field(None, description="Unique violation identifier")
    rule_id: Optional[str] = Field(None, description="Rule that triggered the violation")


class MCPSolution(BaseModel):
    """
    Represents a solved migration example from MCP.
    
    This is the core data structure for storing and retrieving
    modernization solutions from the knowledge base.
    """
    
    solution_id: str = Field(..., description="Unique solution identifier")
    violation: MCPViolation = Field(..., description="Original violation")
    
    # Solution details
    original_code: str = Field(..., description="Original legacy code")
    updated_code: str = Field(..., description="Modernized code")
    explanation: Optional[str] = Field(None, description="Explanation of changes")
    diff: Optional[str] = Field(None, description="Unified diff of changes")
    
    # Metadata
    language: str = Field(..., description="Programming language")
    framework_from: Optional[str] = Field(None, description="Source framework")
    framework_to: Optional[str] = Field(None, description="Target framework")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="AI confidence in solution")
    
    # Usage tracking
    times_used: int = Field(default=0, description="Number of times solution was used")
    times_helpful: int = Field(default=0, description="Number of times marked as helpful")
    times_applied: int = Field(default=0, description="Number of times actually applied")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate based on feedback")
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = Field(None, description="Last time solution was retrieved")
    
    # Additional context
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    related_violations: List[str] = Field(default_factory=list, description="Related violation IDs")
    related_solutions: List[str] = Field(default_factory=list, description="Related solution IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Vector search fields (for real MCP implementation)
    embedding_vector: Optional[List[float]] = Field(None, description="Code embedding for similarity search")
    embedding_model: Optional[str] = Field(None, description="Model used for embedding")
    
    # Provenance
    source: Optional[str] = Field(None, description="Source of solution (ai, human, hybrid)")
    author: Optional[str] = Field(None, description="Author or system that created solution")
    version: int = Field(default=1, description="Solution version number")


class MCPQuery(BaseModel):
    """
    Query parameters for searching MCP solutions.
    
    Supports both metadata-based filtering and semantic code similarity search.
    """
    
    # Search criteria
    violation_name: Optional[str] = Field(None, description="Exact or partial violation name match")
    violation_id: Optional[str] = Field(None, description="Specific violation ID")
    category: Optional[str] = Field(None, description="Violation category filter")
    severity: Optional[str] = Field(None, description="Violation severity filter")
    labels: Optional[List[str]] = Field(None, description="Filter by labels (AND logic)")
    language: Optional[str] = Field(None, description="Programming language filter")
    framework_from: Optional[str] = Field(None, description="Source framework filter")
    framework_to: Optional[str] = Field(None, description="Target framework filter")
    
    # Code similarity (vector search)
    code_snippet: Optional[str] = Field(None, description="Code for similarity search")
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1)"
    )
    use_semantic_search: bool = Field(
        default=True,
        description="Use vector similarity search vs exact match"
    )
    
    # Filtering
    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score"
    )
    min_success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum success rate"
    )
    min_times_used: int = Field(default=0, ge=0, description="Minimum usage count")
    
    # Sorting
    sort_by: Optional[str] = Field(
        default="relevance",
        description="Sort field: relevance, confidence, success_rate, times_used, created_at"
    )
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")
    
    # Pagination
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    
    # Advanced options
    include_related: bool = Field(default=False, description="Include related solutions")
    exclude_solution_ids: List[str] = Field(
        default_factory=list,
        description="Solution IDs to exclude from results"
    )


class MCPSearchResult(BaseModel):
    """
    Result of MCP solution search.
    
    Contains matched solutions and metadata about the search operation.
    """
    
    solutions: List[MCPSolution] = Field(default_factory=list, description="Matched solutions")
    total_count: int = Field(default=0, description="Total matching solutions (before pagination)")
    query: MCPQuery = Field(..., description="Original query parameters")
    search_time_ms: float = Field(default=0.0, description="Search duration in milliseconds")
    
    # Additional metadata for real implementation
    has_more: bool = Field(default=False, description="Whether more results are available")
    next_offset: Optional[int] = Field(None, description="Offset for next page")
    search_method: Optional[str] = Field(None, description="Search method used (vector, metadata, hybrid)")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")


class MCPStoreSolutionRequest(BaseModel):
    """
    Request to store a new solution in MCP.
    
    Used when creating new solutions from analysis results or user contributions.
    """
    
    violation: MCPViolation = Field(..., description="Violation this solution addresses")
    original_code: str = Field(..., description="Original legacy code")
    updated_code: str = Field(..., description="Modernized code")
    explanation: Optional[str] = Field(None, description="Explanation of changes")
    diff: Optional[str] = Field(None, description="Unified diff of changes")
    language: str = Field(..., description="Programming language")
    framework_from: Optional[str] = Field(None, description="Source framework")
    framework_to: Optional[str] = Field(None, description="Target framework")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Additional fields for real implementation
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")
    source: Optional[str] = Field(None, description="Source of solution (ai, human, hybrid)")
    author: Optional[str] = Field(None, description="Author or system identifier")
    generate_embedding: bool = Field(default=True, description="Whether to generate embedding vector")


class MCPSolutionFeedback(BaseModel):
    """
    Feedback on solution usage.
    
    Used to track solution effectiveness and improve recommendations.
    """
    
    solution_id: str = Field(..., description="Solution being rated")
    was_helpful: bool = Field(..., description="Whether solution was helpful")
    was_applied: bool = Field(..., description="Whether solution was actually applied")
    user_notes: Optional[str] = Field(None, description="Optional user comments")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Feedback timestamp")
    
    # Additional fields for real implementation
    user_id: Optional[str] = Field(None, description="User providing feedback")
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Optional 1-5 star rating")
    modifications_made: Optional[str] = Field(None, description="Modifications user made to solution")


class MCPBatchStorageRequest(BaseModel):
    """
    Request to store multiple solutions in batch.
    
    For efficient bulk loading of solutions into MCP.
    """
    
    solutions: List[MCPStoreSolutionRequest] = Field(..., description="Solutions to store")
    skip_duplicates: bool = Field(default=True, description="Skip duplicate solutions")
    update_existing: bool = Field(default=False, description="Update existing solutions if found")


class MCPBatchStorageResult(BaseModel):
    """Result of batch storage operation."""
    
    total_requested: int = Field(..., description="Total solutions requested to store")
    stored: int = Field(default=0, description="Successfully stored solutions")
    skipped: int = Field(default=0, description="Skipped (duplicates)")
    updated: int = Field(default=0, description="Updated existing solutions")
    failed: int = Field(default=0, description="Failed to store")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    solution_ids: List[str] = Field(default_factory=list, description="IDs of stored solutions")

# Made with Bob
