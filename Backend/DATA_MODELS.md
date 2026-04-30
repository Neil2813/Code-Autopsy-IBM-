# Data Models and API Schemas

## Overview

This document defines all data models, API schemas, and database structures for the AI Legacy Modernization Copilot backend.

---

## 1. Core Pydantic Schemas

### 1.1 Upload Schemas

```python
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class UploadType(str, Enum):
    """Type of code upload"""
    ZIP = "zip"
    FILE = "file"
    REPO_URL = "repo_url"
    PASTED_CODE = "pasted_code"

class UploadRequest(BaseModel):
    """Request model for code upload"""
    upload_type: UploadType
    content: Optional[str] = Field(None, description="Pasted code content")
    repo_url: Optional[HttpUrl] = Field(None, description="Git repository URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_type": "zip",
                "metadata": {
                    "project_name": "legacy-app",
                    "description": "Legacy Java application"
                }
            }
        }

class UploadResponse(BaseModel):
    """Response model for successful upload"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Status message")
    file_count: int = Field(..., description="Number of files uploaded")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    detected_languages: List[str] = Field(..., description="Detected programming languages")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 1.2 Analysis Schemas

```python
class AnalysisOptions(BaseModel):
    """Configuration options for analysis"""
    include_dependencies: bool = Field(True, description="Analyze dependencies")
    include_security_scan: bool = Field(True, description="Run security analysis")
    include_architecture_analysis: bool = Field(True, description="Analyze architecture")
    include_refactoring_suggestions: bool = Field(True, description="Generate refactoring suggestions")
    max_file_size_mb: int = Field(10, ge=1, le=100, description="Max file size to analyze")
    languages_to_analyze: Optional[List[str]] = Field(None, description="Specific languages to focus on")
    use_mcp_solutions: bool = Field(True, description="Use MCP for solution retrieval")

class AnalyzeRequest(BaseModel):
    """Request to start code analysis"""
    job_id: str = Field(..., description="Job ID from upload")
    analysis_options: Optional[AnalysisOptions] = Field(default_factory=AnalysisOptions)

class AnalyzeResponse(BaseModel):
    """Response when analysis is queued"""
    job_id: str
    status: str
    message: str
    estimated_duration_seconds: Optional[int] = None
```

### 1.3 Job Status Schemas

```python
class JobStatus(str, Enum):
    """Job processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"

class JobStage(str, Enum):
    """Analysis pipeline stages"""
    INGESTION = "ingestion"
    PARSING = "parsing"
    CLASSIFICATION = "classification"
    ANALYSIS = "analysis"
    EXPLANATION = "explanation"
    RECOMMENDATION = "recommendation"
    VALIDATION = "validation"
    REPORT_GENERATION = "report_generation"

class JobStatusResponse(BaseModel):
    """Detailed job status information"""
    job_id: str
    status: JobStatus
    progress_percentage: float = Field(..., ge=0, le=100)
    current_stage: Optional[JobStage] = None
    stages_completed: List[JobStage] = Field(default_factory=list)
    estimated_time_remaining_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 1.4 Analysis Result Schemas

```python
class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskCategory(str, Enum):
    """Categories of risks"""
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    TECHNICAL_DEBT = "technical_debt"
    DEPRECATED_API = "deprecated_api"

class RiskItem(BaseModel):
    """Individual risk or issue"""
    id: str
    title: str
    description: str
    category: RiskCategory
    level: RiskLevel
    affected_files: List[str]
    line_numbers: Optional[List[int]] = None
    code_snippet: Optional[str] = None
    recommendation: str
    effort_estimate: str = Field(..., description="e.g., 'low', 'medium', 'high'")
    confidence: float = Field(..., ge=0, le=1)
    mcp_solution_available: bool = Field(False, description="Whether MCP has similar solution")

class SuggestionType(str, Enum):
    """Types of modernization suggestions"""
    REFACTORING = "refactoring"
    FRAMEWORK_UPGRADE = "framework_upgrade"
    ARCHITECTURE_CHANGE = "architecture_change"
    DEPENDENCY_UPDATE = "dependency_update"
    CODE_CLEANUP = "code_cleanup"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"

class ModernizationSuggestion(BaseModel):
    """Modernization recommendation"""
    id: str
    type: SuggestionType
    title: str
    description: str
    rationale: str
    affected_files: List[str]
    before_snippet: Optional[str] = None
    after_snippet: Optional[str] = None
    priority: int = Field(..., ge=1, le=5, description="1=highest, 5=lowest")
    effort_estimate: str
    benefits: List[str]
    risks: List[str]
    confidence: float = Field(..., ge=0, le=1)
    mcp_based: bool = Field(False, description="Based on MCP solution")

class MigrationBlocker(BaseModel):
    """Critical blocker for migration"""
    id: str
    title: str
    description: str
    affected_components: List[str]
    severity: RiskLevel
    resolution_steps: List[str]
    estimated_effort: str

class FileAnalysis(BaseModel):
    """Analysis of a single file"""
    file_path: str
    language: str
    file_type: str = Field(..., description="e.g., controller, service, model, config")
    lines_of_code: int
    complexity_score: float = Field(..., ge=0, le=10)
    risk_level: RiskLevel
    issues: List[RiskItem]
    dependencies: List[str]
    summary: str
    framework_detected: Optional[str] = None

class DependencyNode(BaseModel):
    """Node in dependency graph"""
    id: str
    name: str
    type: str = Field(..., description="module, class, function, file")
    file_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DependencyEdge(BaseModel):
    """Edge in dependency graph"""
    source_id: str
    target_id: str
    relationship_type: str = Field(..., description="imports, calls, extends, implements")
    strength: float = Field(..., ge=0, le=1, description="Coupling strength")

class DependencyGraph(BaseModel):
    """Complete dependency graph"""
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Graph metrics like cyclomatic complexity, coupling"
    )

class ArchitectureOverview(BaseModel):
    """High-level architecture summary"""
    pattern: str = Field(..., description="e.g., layered, microservices, monolith")
    layers: List[str] = Field(..., description="e.g., controller, service, repository")
    frameworks: List[str]
    technologies: List[str]
    entry_points: List[str]
    key_components: List[str]
    architecture_smells: List[str] = Field(default_factory=list)

class AnalysisSummary(BaseModel):
    """High-level analysis summary"""
    total_files: int
    total_lines: int
    languages: List[str]
    project_type: str
    risk_score: float = Field(..., ge=0, le=10)
    maintainability_index: float = Field(..., ge=0, le=100)
    technical_debt_hours: Optional[int] = None

class Reference(BaseModel):
    """Reference to source code location"""
    file: str
    line_number: Optional[int] = None
    snippet: Optional[str] = None
    context: Optional[str] = None

class AnalysisMetadata(BaseModel):
    """Metadata about the analysis"""
    analysis_duration_seconds: float
    llm_provider_used: str = Field(..., description="primary, groq, or rule_based")
    mcp_solutions_used: int = Field(0, description="Number of MCP solutions referenced")
    agent_state_transitions: int = Field(0, description="Number of LangGraph state transitions")
    partial_results: bool = Field(False, description="Whether results are partial due to errors")

class ProjectAnalysis(BaseModel):
    """Complete analysis results"""
    job_id: str
    summary: AnalysisSummary
    detected_language: str
    project_type: str
    architecture_overview: ArchitectureOverview
    file_inventory: List[FileAnalysis]
    dependency_graph: DependencyGraph
    risks: List[RiskItem]
    suggestions: List[ModernizationSuggestion]
    migration_blockers: List[MigrationBlocker]
    recommended_next_steps: List[str]
    confidence: float = Field(..., ge=0, le=1)
    references: List[Reference] = Field(default_factory=list)
    metadata: AnalysisMetadata
```

### 1.5 Query Schemas

```python
class QueryRequest(BaseModel):
    """Natural language query about codebase"""
    job_id: str
    question: str = Field(..., min_length=5, max_length=500)
    context_limit: int = Field(5, ge=1, le=20, description="Max context items to retrieve")
    use_mcp: bool = Field(True, description="Use MCP solutions in answer")

class QueryResponse(BaseModel):
    """Response to natural language query"""
    answer: str
    confidence: float = Field(..., ge=0, le=1)
    references: List[Reference]
    related_files: List[str]
    suggested_follow_ups: List[str]
    mcp_solutions_referenced: int = Field(0)
```

### 1.6 Report Schemas

```python
class ReportFormat(str, Enum):
    """Available report formats"""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"

class ReportRequest(BaseModel):
    """Request to generate report"""
    job_id: str
    format: ReportFormat = ReportFormat.MARKDOWN
    include_code_snippets: bool = Field(True)
    include_dependency_graph: bool = Field(True)
    sections: Optional[List[str]] = Field(
        None,
        description="Specific sections to include, or all if None"
    )

class ReportResponse(BaseModel):
    """Generated report information"""
    job_id: str
    format: ReportFormat
    content: Optional[str] = Field(None, description="Inline content for JSON/Markdown")
    download_url: Optional[str] = Field(None, description="Download URL for large reports")
    file_size_bytes: int
    generated_at: datetime
```

### 1.7 Error Schemas

```python
class ErrorCategory(str, Enum):
    """Error categories"""
    VALIDATION_ERROR = "validation_error"
    UPLOAD_ERROR = "upload_error"
    PARSING_ERROR = "parsing_error"
    ANALYSIS_ERROR = "analysis_error"
    LLM_ERROR = "llm_error"
    MCP_ERROR = "mcp_error"
    STORAGE_ERROR = "storage_error"
    QUEUE_ERROR = "queue_error"
    INTERNAL_ERROR = "internal_error"

class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    error_code: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: bool = True
    category: ErrorCategory
    message: str
    details: Optional[List[ErrorDetail]] = None
    job_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

## 2. LangGraph Agent State Schema

```python
from typing import TypedDict, Annotated, List, Dict, Any
import operator

class AgentState(TypedDict):
    """State maintained throughout LangGraph agent execution"""
    
    # Job identification
    job_id: str
    
    # Input data
    files: List[Dict[str, Any]]  # Uploaded files metadata
    upload_metadata: Dict[str, Any]
    
    # Parsing stage
    parsed_data: Dict[str, Any]  # Parsed code structures
    detected_languages: List[str]
    
    # Classification stage
    classified_components: Dict[str, Any]  # Categorized files
    frameworks_detected: List[str]
    
    # Analysis stage
    analysis_results: Dict[str, Any]  # Issues, risks, metrics
    dependency_graph: Dict[str, Any]
    mcp_solutions: List[Dict[str, Any]]  # Retrieved from MCP
    
    # Explanation stage
    explanations: List[str]  # Generated explanations
    architecture_summary: Dict[str, Any]
    
    # Recommendation stage
    recommendations: List[Dict[str, Any]]
    migration_plan: Dict[str, Any]
    
    # Error handling
    errors: Annotated[List[str], operator.add]  # Accumulated errors
    warnings: Annotated[List[str], operator.add]
    
    # Execution metadata
    current_stage: str
    stages_completed: List[str]
    llm_provider: str  # "primary", "groq", or "rule_based"
    retry_count: int
    start_time: float
    
    # Configuration
    analysis_options: Dict[str, Any]
    
    # Output
    final_results: Optional[Dict[str, Any]]
```

---

## 3. Database Models (SQLAlchemy)

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class JobStatusEnum(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"

class Job(Base):
    """Main job tracking table"""
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True)
    status = Column(Enum(JobStatusEnum), nullable=False, default=JobStatusEnum.QUEUED)
    progress = Column(Float, default=0.0)
    current_stage = Column(String(50))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON)
    
    # Relationships
    files = relationship("File", back_populates="job", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="job", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="job", cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="job", cascade="all, delete-orphan")

class File(Base):
    """Uploaded files table"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    language = Column(String(50))
    file_type = Column(String(50))
    content = Column(Text)
    size_bytes = Column(Integer)
    lines_of_code = Column(Integer)
    complexity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="files")

class AnalysisResult(Base):
    """Analysis results table"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    result_type = Column(String(50), nullable=False)  # summary, dependency_graph, etc.
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="analysis_results")

class Risk(Base):
    """Detected risks table"""
    __tablename__ = "risks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    risk_id = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(50))
    level = Column(String(20))
    affected_files = Column(JSON)
    line_numbers = Column(JSON)
    recommendation = Column(Text)
    confidence = Column(Float)
    mcp_solution_available = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="risks")

class Suggestion(Base):
    """Modernization suggestions table"""
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    suggestion_id = Column(String(50), unique=True, nullable=False)
    type = Column(String(50))
    title = Column(Text, nullable=False)
    description = Column(Text)
    rationale = Column(Text)
    priority = Column(Integer)
    effort_estimate = Column(String(50))
    affected_files = Column(JSON)
    before_snippet = Column(Text)
    after_snippet = Column(Text)
    confidence = Column(Float)
    mcp_based = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="suggestions")

class Query(Base):
    """Query history table"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    confidence = Column(Float)
    references = Column(JSON)
    mcp_solutions_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 4. MCP Integration Types

```python
from pydantic import BaseModel
from typing import List, Optional

class ExtendedIncident(BaseModel):
    """Incident with extended metadata for MCP"""
    incident_id: Optional[int] = None
    uri: str
    message: str
    code_snip: str = ""
    line_number: int = -1
    variables: Dict[str, Any] = {}
    ruleset_name: str
    ruleset_description: Optional[str] = None
    violation_name: str
    violation_description: Optional[str] = None
    violation_category: str = "potential"
    violation_labels: List[str] = []

class SolutionFile(BaseModel):
    """File in a solution changeset"""
    uri: str
    content: str

class SolutionChangeSet(BaseModel):
    """Changes made in a solution"""
    before: List[SolutionFile]
    after: List[SolutionFile]

class ViolationID(BaseModel):
    """Identifier for a violation"""
    ruleset_name: str
    violation_name: str

class SuccessRateMetric(BaseModel):
    """Success rate for a violation"""
    violation_id: ViolationID
    counted_solutions: int
    accepted_solutions: int
    success_rate: float

class MCPHint(BaseModel):
    """Hint retrieved from MCP"""
    hint_id: int
    hint: str
    ruleset_name: str
    violation_name: str
    success_rate: Optional[float] = None
```

---

## 5. API Response Wrappers

```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorResponse] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
```

---

## 6. Configuration Models

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
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
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Job Queue
    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

## 7. Validation Rules

### File Upload Validation
- Max file size: 100MB (configurable)
- Allowed extensions: `.java`, `.cobol`, `.cbl`, `.rpg`, `.jcl`, `.xml`, `.properties`, `.yaml`, `.yml`
- Max files per upload: 1000
- ZIP archive max size: 500MB

### Analysis Options Validation
- `max_file_size_mb`: 1-100
- `context_limit`: 1-20
- `priority`: 1-5

### Query Validation
- Question length: 5-500 characters
- Context limit: 1-20 items

---

## 8. Example Usage

### Upload Request
```json
{
  "upload_type": "zip",
  "metadata": {
    "project_name": "legacy-banking-app",
    "description": "Legacy Java banking application"
  }
}
```

### Analysis Request
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis_options": {
    "include_dependencies": true,
    "include_security_scan": true,
    "include_architecture_analysis": true,
    "use_mcp_solutions": true
  }
}
```

### Query Request
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Where is authentication handled in this codebase?",
  "use_mcp": true
}
```

---

This comprehensive data model specification ensures type safety, validation, and clear contracts between all system components.
