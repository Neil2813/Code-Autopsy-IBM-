"""
Pydantic schemas package.

This package contains all request/response schemas for the API.
"""

from app.schemas.analyze import AnalysisConfig, AnalyzeRequest, AnalyzeResponse
from app.schemas.common import (
    ConfidenceScore,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DetailedStatus,
    EffortEnum,
    ErrorDetail,
    ErrorResponse,
    FileReference,
    FileTypeEnum,
    HealthStatus,
    JobStatusEnum,
    LanguageEnum,
    PaginatedResponse,
    PaginationParams,
    PriorityEnum,
    SeverityEnum,
    TimestampMixin,
)
from app.schemas.job import (
    ArchitectureSummary,
    JobResultResponse,
    JobStageProgress,
    JobStatusResponse,
    ModernizationSuggestion,
    RiskItem,
)
from app.schemas.query import (
    QueryHistoryItem,
    QueryHistoryResponse,
    QueryRequest,
    QueryResponse,
)
from app.schemas.report import (
    ReportFormatEnum,
    ReportMetadata,
    ReportRequest,
    ReportResponse,
    ReportSectionEnum,
)
from app.schemas.upload import (
    CodeSnippetUploadRequest,
    FileUploadRequest,
    RepositoryUploadRequest,
    UploadedFile,
    UploadResponse,
    UploadValidationError,
)

__all__ = [
    # Common
    "ConfidenceScore",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyNode",
    "DetailedStatus",
    "EffortEnum",
    "ErrorDetail",
    "ErrorResponse",
    "FileReference",
    "FileTypeEnum",
    "HealthStatus",
    "JobStatusEnum",
    "LanguageEnum",
    "PaginatedResponse",
    "PaginationParams",
    "PriorityEnum",
    "SeverityEnum",
    "TimestampMixin",
    # Upload
    "CodeSnippetUploadRequest",
    "FileUploadRequest",
    "RepositoryUploadRequest",
    "UploadedFile",
    "UploadResponse",
    "UploadValidationError",
    # Analyze
    "AnalysisConfig",
    "AnalyzeRequest",
    "AnalyzeResponse",
    # Job
    "ArchitectureSummary",
    "JobResultResponse",
    "JobStageProgress",
    "JobStatusResponse",
    "ModernizationSuggestion",
    "RiskItem",
    # Query
    "QueryHistoryItem",
    "QueryHistoryResponse",
    "QueryRequest",
    "QueryResponse",
    # Report
    "ReportFormatEnum",
    "ReportMetadata",
    "ReportRequest",
    "ReportResponse",
    "ReportSectionEnum",
]

# Made with Bob
