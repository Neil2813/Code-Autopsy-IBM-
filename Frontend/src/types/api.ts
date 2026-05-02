/**
 * TypeScript Type Definitions for IBM BOB API
 * These types match the Backend Pydantic schemas
 */

// ============================================================================
// Common Types
// ============================================================================

export type JobStatus = 
  | 'pending'
  | 'queued'
  | 'running'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'partial_success'
  | 'uploaded';

export type AnalysisStage = 
  | 'parsing'
  | 'complexity_analysis'
  | 'dependency_analysis'
  | 'risk_assessment'
  | 'pattern_detection'
  | 'recommendation'
  | 'report_generation'
  | 'completed';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type SuggestionPriority = 'low' | 'medium' | 'high' | 'critical';

export type ReportFormat = 'markdown' | 'json' | 'html' | 'pdf';

// ============================================================================
// Upload Types
// ============================================================================

export interface FileUploadRequest {
  file: File;
  language?: string;
  metadata?: Record<string, any>;
}

export interface RepositoryUploadRequest {
  repository_url: string;
  branch?: string;
  subdirectory?: string;
  include_patterns?: string[];
  exclude_patterns?: string[];
}

export interface SnippetUploadRequest {
  code: string;
  language?: string;
  filename?: string;
  description?: string;
}

export interface UploadedFile {
  file_id: string;
  filename: string;
  file_path: string;
  size_bytes: number;
  detected_language?: string;
  file_type?: string;
}

export interface UploadResponse {
  job_id: string;
  upload_id: string;
  status: JobStatus;
  message: string;
  files: UploadedFile[];
  total_files: number;
  total_size_bytes: number;
  detected_languages: string[];
  primary_language?: string;
}

// ============================================================================
// Analysis Types
// ============================================================================

export interface AnalysisRequest {
  job_id: string;
  config?: {
    enable_mcp?: boolean;
    enable_dependency_analysis?: boolean;
    enable_risk_detection?: boolean;
    enable_suggestion_generation?: boolean;
    max_file_size_mb?: number;
    languages_to_analyze?: string[];
    focus_areas?: string[];
  };
  priority?: 'low' | 'normal' | 'high';
}

export interface AnalysisResponse {
  job_id: string;
  status: JobStatus;
  message: string;
  estimated_duration_seconds?: number;
}

// ============================================================================
// Job Types
// ============================================================================

export interface JobDetails {
  job_id: string;
  status: JobStatus;
  progress_percent: number;
  message: string;
  stages: Array<{
    stage_name: string;
    status: string;
    progress_percent: number;
    message?: string;
    started_at?: string;
    completed_at?: string;
  }>;
  current_stage?: string;
  estimated_completion?: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

export interface ComplexityMetrics {
  cyclomatic_complexity: number;
  cognitive_complexity: number;
  lines_of_code: number;
  comment_ratio: number;
  maintainability_index: number;
}

export interface DependencyInfo {
  name: string;
  version?: string;
  type: 'internal' | 'external' | 'system';
  usage_count: number;
  is_deprecated?: boolean;
  replacement_suggestion?: string;
}

export interface RiskItem {
  risk_id: string;
  title: string;
  description: string;
  severity: RiskLevel | 'info';
  category: string;
  affected_files: Array<{
    file_path: string;
    line_start?: number;
    line_end?: number;
    snippet?: string;
  }>;
  recommendation: string;
  mcp_solution_available: boolean;
  confidence: number;
}

export interface SuggestionItem {
  suggestion_id: string;
  title: string;
  description: string;
  priority: SuggestionPriority;
  category: string;
  affected_files: Array<{
    file_path: string;
    line_start?: number;
    line_end?: number;
    snippet?: string;
  }>;
  implementation_guide: string;
  effort_estimate?: string;
  benefits?: string[];
  risks?: string[];
  mcp_solution_available: boolean;
  confidence: number;
}

export interface JobResults {
  job_id: string;
  status: JobStatus;
  summary: string;
  architecture: {
    project_type: string;
    primary_language: string;
    detected_frameworks: string[];
    architecture_patterns: string[];
    layers: Record<string, string[]>;
    entry_points: Array<{ file_path: string; line_start?: number; line_end?: number }>;
    dependency_graph: { nodes: any[]; edges: any[] };
  };
  risks: RiskItem[];
  suggestions: SuggestionItem[];
  migration_blockers: string[];
  recommended_next_steps: string[];
  metadata: {
    total_files?: number;
    total_lines_of_code?: number;
    languages?: string[];
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Query Types
// ============================================================================

export interface QueryRequest {
  job_id: string;
  question: string;
  context?: string;
}

export interface QueryResponse {
  query_id: string;
  job_id: string;
  question: string;
  answer: string;
  confidence: number;
  references: Array<{
    file_path: string;
    line_start?: number;
    line_end?: number;
    snippet?: string;
  }>;
  mcp_solutions_used: number;
  follow_up_suggestions: string[];
  created_at: string;
  updated_at: string;
}

export interface QueryHistory {
  job_id: string;
  queries: Array<{
    query_id: string;
    question: string;
    answer_preview: string;
    answer_full?: string;
    confidence: number;
    created_at?: string;
    timestamp?: string;
  }>;
  total_queries: number;
  messages?: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    references?: string[];
    confidence?: number;
    timestamp: string;
  }>;
}

// ============================================================================
// Report Types
// ============================================================================

export interface ReportGenerationRequest {
  job_id: string;
  format: ReportFormat;
  sections?: string[];
  include_code_snippets?: boolean;
  include_dependency_graph?: boolean;
}

export interface ReportResponse {
  report_id: string;
  job_id: string;
  format: ReportFormat;
  download_url?: string;
  content?: string;
  size_bytes: number;
  generated_at: string;
}

export interface ReportMetadata {
  report_id: string;
  job_id: string;
  format: ReportFormat;
  size_bytes: number;
  generated_at: string;
  expires_at?: string;
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'operational';
  service?: string;
  version: string;
  environment?: string;
  components?: Record<string, any>;
}

// ============================================================================
// Error Types
// ============================================================================

export interface APIError {
  detail: string;
  status_code: number;
  error_code?: string;
  timestamp?: string;
}

export interface ValidationError {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

// Made with Bob

// ============================================================================
// Code Review Types
// ============================================================================

export type IssueSeverity = "HIGH" | "MEDIUM" | "LOW";

export type IssueType =
  | "runtime_safety"
  | "logic_bug"
  | "type_safety"
  | "performance"
  | "maintainability"
  | "security"
  | "reliability";

export interface CodeIssue {
  line: number | null;
  severity: IssueSeverity;
  type: IssueType;
  title: string;
  code_snippet: string;
  problem: string;
  fix: string;
}

export interface CodeReviewFile {
  file_path: string;
  issues: CodeIssue[];
}

export interface CodeReview {
  summary: {
    total_files: number;
    total_issues: number;
    high: number;
    medium: number;
    low: number;
  };
  files: CodeReviewFile[];
}
