"""
LangGraph Agent State Definition.

This module defines the state structure for the modernization agent workflow.
The state is passed through all agent nodes and accumulates analysis results.
"""

from typing import Any, Dict, List, Optional, TypedDict, Union

from app.schemas.common import DependencyGraph, LanguageEnum


class FileInfo(TypedDict):
    """Information about a single file."""

    file_id: str
    file_path: str
    language: str  # Normalized to string for consistency across pipeline
    file_type: str
    content: str
    size_bytes: int
    lines_of_code: int
    complexity_score: Optional[float]


class ParsedFile(TypedDict):
    """Parsed file structure."""

    file_id: str
    file_path: str
    language: str  # Normalized to string for consistency
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    imports: List[str]
    dependencies: List[str]
    ast_data: Optional[Dict[str, Any]]
    nodes: List[Dict[str, Any]]  # Parsed code nodes from parser
    parse_success: bool
    parse_errors: List[str]


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


class AgentState(TypedDict):
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

    # Job metadata (required)
    job_id: str
    status: str
    current_stage: str
    progress_percent: float

    error_message: Optional[str]

    # Input data (required)
    uploaded_files: List[FileInfo]
    analysis_config: Dict[str, Any]

    # Stage 1: Ingest (required)
    ingested_files: List[FileInfo]
    detected_languages: List[str]  # Normalized to strings
    primary_language: Optional[str]  # Normalized to string
    total_files: int
    total_lines: int
    total_size_bytes: int

    # Stage 2: Parse (required)
    parsed_files: List[ParsedFile]
    parse_errors: List[Dict[str, str]]
    successfully_parsed: int

    # Stage 3: Classify (required)
    file_classifications: Dict[str, str]  # file_id -> classification
    entry_points: List[str]
    test_files: List[str]
    config_files: List[str]
    source_files: List[str]

    # Stage 4: Analyze (required)
    dependency_graph: Optional[DependencyGraph]
    detected_frameworks: List[str]
    architecture_patterns: List[str]
    project_type: str
    layers: Dict[str, List[str]]
    risks: List[RiskItem]
    code_smells: List[Dict[str, Any]]
    security_issues: List[Dict[str, Any]]
    complexity_metrics: Dict[str, Any]

    # Stage 5: Explain (required)
    summary: str
    architecture_explanation: str
    file_explanations: Dict[str, str]  # file_id -> explanation
    data_flow_explanation: str

    # Stage 6: Recommend (required)
    suggestions: List[SuggestionItem]
    migration_blockers: List[str]
    recommended_next_steps: List[str]
    prioritized_actions: List[Dict[str, Any]]

    # Stage 7: Validate (required)
    validation_results: Dict[str, Any]
    confidence_scores: Dict[str, float]
    mcp_solutions_used: int
    fallback_used: bool

    # Stage 8: Report (required)
    report_generated: bool
    report_content: Optional[str]
    report_metadata: Dict[str, Any]

    # MCP integration (required)
    mcp_queries: List[Dict[str, Any]]
    mcp_solutions: List[Dict[str, Any]]

    # Timestamps (required)
    started_at: str
    completed_at: Optional[str]
    stage_timings: Dict[str, float]


def create_initial_state(
    job_id: str,
    uploaded_files: List[FileInfo],
    analysis_config: Optional[Dict[str, Any]] = None,
) -> AgentState:
    """
    Create initial agent state with all required fields initialized to safe defaults.
    
    Args:
        job_id: Unique job identifier
        uploaded_files: List of uploaded files
        analysis_config: Analysis configuration (optional, defaults to empty dict)
    
    Returns:
        Initial agent state with all fields properly initialized
    """
    from datetime import datetime

    # Ensure analysis_config has safe defaults
    if analysis_config is None:
        analysis_config = {}
    
    # Set default config values
    config = {
        'include_llm_analysis': analysis_config.get('include_llm_analysis', True),
        'include_mcp_solutions': analysis_config.get('include_mcp_solutions', True),
        'risk_threshold': analysis_config.get('risk_threshold', 'medium'),
        'max_file_size_mb': analysis_config.get('max_file_size_mb', 10),
        'timeout_seconds': analysis_config.get('timeout_seconds', 300),
        **analysis_config
    }

    return AgentState(
        # Job metadata
        job_id=job_id,
        status="pending",
        current_stage="ingest",
        progress_percent=0.0,
        error_message=None,
        
        # Input data
        uploaded_files=uploaded_files,
        analysis_config=config,
        
        # Stage 1: Ingest - Initialize with safe defaults
        ingested_files=[],
        detected_languages=[],
        primary_language=None,
        total_files=0,
        total_lines=0,
        total_size_bytes=0,
        
        # Stage 2: Parse - Initialize with safe defaults
        parsed_files=[],
        parse_errors=[],
        successfully_parsed=0,
        
        # Stage 3: Classify - Initialize with safe defaults
        file_classifications={},
        entry_points=[],
        test_files=[],
        config_files=[],
        source_files=[],
        
        # Stage 4: Analyze - Initialize with safe defaults
        dependency_graph=None,
        detected_frameworks=[],
        architecture_patterns=[],
        project_type="unknown",
        layers={},
        risks=[],
        code_smells=[],
        security_issues=[],
        complexity_metrics={
            'total_complexity': 0.0,
            'average_complexity': 0.0,
            'max_complexity': 0.0,
            'files_analyzed': 0
        },
        
        # Stage 5: Explain - Initialize with safe defaults
        summary="Analysis in progress...",
        architecture_explanation="",
        file_explanations={},
        data_flow_explanation="",
        
        # Stage 6: Recommend - Initialize with safe defaults
        suggestions=[],
        migration_blockers=[],
        recommended_next_steps=[],
        prioritized_actions=[],
        
        # Stage 7: Validate - Initialize with safe defaults
        validation_results={
            'overall_confidence': 0.0,
            'validation_passed': False,
            'validation_errors': []
        },
        confidence_scores={},
        mcp_solutions_used=0,
        fallback_used=False,
        
        # Stage 8: Report - Initialize with safe defaults
        report_generated=False,
        report_content=None,
        report_metadata={
            'format': 'json',
            'version': '1.0',
            'generated_by': 'IBM BOB'
        },
        
        # MCP integration - Initialize with safe defaults
        mcp_queries=[],
        mcp_solutions=[],
        
        # Timestamps - Initialize with safe defaults
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        stage_timings={
            'ingest': 0.0,
            'parse': 0.0,
            'classify': 0.0,
            'analyze': 0.0,
            'explain': 0.0,
            'recommend': 0.0,
            'validate': 0.0,
            'report': 0.0
        },
    )


def normalize_language(language: Union[LanguageEnum, str]) -> str:
    """
    Normalize language value to lowercase string for consistency across the pipeline.
    
    This ensures all parts of the system work with the same string representation,
    avoiding enum/string mismatches.
    
    Args:
        language: Language as enum or string
        
    Returns:
        Normalized lowercase language string (e.g., "java", "cobol", "rpg")
    """
    if isinstance(language, LanguageEnum):
        return language.value.lower()
    return str(language).lower().strip()


def ensure_language_enum(language: Union[LanguageEnum, str]) -> LanguageEnum:
    """
    Convert language string to LanguageEnum if needed.
    
    Useful when interfacing with schemas that require enum types.
    
    Args:
        language: Language as enum or string
        
    Returns:
        LanguageEnum value
        
    Raises:
        ValueError: If language string is not valid
    """
    if isinstance(language, LanguageEnum):
        return language
    
    # Normalize and try to match string to enum
    language_normalized = str(language).lower().strip()
    for lang_enum in LanguageEnum:
        if lang_enum.value.lower() == language_normalized or lang_enum.name.lower() == language_normalized:
            return lang_enum
    
    # Default to UNKNOWN if not found
    return LanguageEnum.UNKNOWN


def normalize_file_info(file_info: FileInfo) -> FileInfo:
    """
    Normalize a FileInfo object to ensure consistent language representation.
    
    Args:
        file_info: FileInfo object to normalize
        
    Returns:
        Normalized FileInfo with string language
    """
    normalized = file_info.copy()
    if 'language' in normalized:
        normalized['language'] = normalize_language(normalized['language'])
    return normalized


def normalize_parsed_file(parsed_file: ParsedFile) -> ParsedFile:
    """
    Normalize a ParsedFile object to ensure consistent language representation.
    
    Args:
        parsed_file: ParsedFile object to normalize
        
    Returns:
        Normalized ParsedFile with string language
    """
    normalized = parsed_file.copy()
    if 'language' in normalized:
        normalized['language'] = normalize_language(normalized['language'])
    return normalized

# Made with Bob
