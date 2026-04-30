"""
LangGraph Agent State Definition.

This module defines the state structure for the modernization agent workflow.
The state is passed through all agent nodes and accumulates analysis results.
"""

from typing import Any, Dict, List, Optional, TypedDict

from app.schemas.common import DependencyGraph, LanguageEnum


class FileInfo(TypedDict, total=False):
    """Information about a single file."""

    file_id: str
    file_path: str
    language: LanguageEnum
    file_type: str
    content: str
    size_bytes: int
    lines_of_code: int
    complexity_score: Optional[float]


class ParsedFile(TypedDict, total=False):
    """Parsed file structure."""

    file_id: str
    file_path: str
    language: LanguageEnum
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    imports: List[str]
    dependencies: List[str]
    ast_data: Optional[Dict[str, Any]]


class RiskItem(TypedDict, total=False):
    """Detected risk item."""

    risk_id: str
    title: str
    description: str
    severity: str
    category: str
    affected_files: List[str]
    line_numbers: Optional[List[int]]
    recommendation: str
    confidence: float
    mcp_solution_available: bool


class SuggestionItem(TypedDict, total=False):
    """Modernization suggestion."""

    suggestion_id: str
    title: str
    description: str
    priority: str
    category: str
    affected_files: List[str]
    implementation_guide: str
    estimated_effort: str
    benefits: List[str]
    risks: List[str]
    confidence: float
    mcp_solution_available: bool


class AgentState(TypedDict, total=False):
    """
    Complete state for the modernization agent workflow.
    
    This state is passed through all agent nodes:
    1. Ingest
    2. Parse
    3. Classify
    4. Analyze
    5. Explain
    6. Recommend
    7. Validate
    8. Report
    """

    # Job metadata
    job_id: str
    status: str
    current_stage: str
    progress_percent: float
    error_message: Optional[str]

    # Input data
    uploaded_files: List[FileInfo]
    analysis_config: Dict[str, Any]

    # Stage 1: Ingest
    ingested_files: List[FileInfo]
    detected_languages: List[LanguageEnum]
    primary_language: Optional[LanguageEnum]
    total_files: int
    total_lines: int

    # Stage 2: Parse
    parsed_files: List[ParsedFile]
    parse_errors: List[Dict[str, str]]
    successfully_parsed: int

    # Stage 3: Classify
    file_classifications: Dict[str, str]  # file_id -> classification
    entry_points: List[str]
    test_files: List[str]
    config_files: List[str]
    source_files: List[str]

    # Stage 4: Analyze
    dependency_graph: Optional[DependencyGraph]
    detected_frameworks: List[str]
    architecture_patterns: List[str]
    project_type: str
    layers: Dict[str, List[str]]
    risks: List[RiskItem]
    code_smells: List[Dict[str, Any]]
    security_issues: List[Dict[str, Any]]
    complexity_metrics: Dict[str, Any]

    # Stage 5: Explain
    summary: str
    architecture_explanation: str
    file_explanations: Dict[str, str]  # file_id -> explanation
    data_flow_explanation: str

    # Stage 6: Recommend
    suggestions: List[SuggestionItem]
    migration_blockers: List[str]
    recommended_next_steps: List[str]
    prioritized_actions: List[Dict[str, Any]]

    # Stage 7: Validate
    validation_results: Dict[str, Any]
    confidence_scores: Dict[str, float]
    mcp_solutions_used: int
    fallback_used: bool

    # Stage 8: Report
    report_generated: bool
    report_content: Optional[str]
    report_metadata: Dict[str, Any]

    # MCP integration
    mcp_queries: List[Dict[str, Any]]
    mcp_solutions: List[Dict[str, Any]]

    # Timestamps
    started_at: str
    completed_at: Optional[str]
    stage_timings: Dict[str, float]


def create_initial_state(
    job_id: str,
    uploaded_files: List[FileInfo],
    analysis_config: Dict[str, Any],
) -> AgentState:
    """
    Create initial agent state.
    
    Args:
        job_id: Unique job identifier
        uploaded_files: List of uploaded files
        analysis_config: Analysis configuration
    
    Returns:
        Initial agent state
    """
    from datetime import datetime

    return AgentState(
        # Job metadata
        job_id=job_id,
        status="pending",
        current_stage="ingest",
        progress_percent=0.0,
        error_message=None,
        # Input data
        uploaded_files=uploaded_files,
        analysis_config=analysis_config,
        # Initialize empty collections
        ingested_files=[],
        detected_languages=[],
        primary_language=None,
        total_files=0,
        total_lines=0,
        parsed_files=[],
        parse_errors=[],
        successfully_parsed=0,
        file_classifications={},
        entry_points=[],
        test_files=[],
        config_files=[],
        source_files=[],
        dependency_graph=None,
        detected_frameworks=[],
        architecture_patterns=[],
        project_type="unknown",
        layers={},
        risks=[],
        code_smells=[],
        security_issues=[],
        complexity_metrics={},
        summary="",
        architecture_explanation="",
        file_explanations={},
        data_flow_explanation="",
        suggestions=[],
        migration_blockers=[],
        recommended_next_steps=[],
        prioritized_actions=[],
        validation_results={},
        confidence_scores={},
        mcp_solutions_used=0,
        fallback_used=False,
        report_generated=False,
        report_content=None,
        report_metadata={},
        mcp_queries=[],
        mcp_solutions=[],
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        stage_timings={},
    )

# Made with Bob
