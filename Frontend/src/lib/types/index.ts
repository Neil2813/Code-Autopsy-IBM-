export type JobStatus = "queued" | "processing" | "completed" | "failed" | "cancelled";

export type RiskSeverity = "critical" | "high" | "medium" | "low";

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  organization?: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  organization?: string;
  role?: string;
}

export interface ProfileData {
  name?: string;
  email?: string;
  organization?: string;
}

export interface Job {
  id: string;
  project_name: string;
  status: JobStatus;
  progress?: number;
  current_stage?: string;
  languages?: string[];
  risk_score?: number;
  created_at: string;
}

export interface AnalysisResults {
  summary: {
    total_files: number;
    lines_of_code: number;
    risk_score: number;
    maintainability_index: number;
    technical_debt_hours: number;
    languages: string[];
  };
  architecture: {
    pattern: string;
    frameworks: string[];
    technologies: string[];
    entry_points: string[];
  };
  files: FileNode[];
  risks: Risk[];
  suggestions: Suggestion[];
  dependencies: { nodes: any[]; edges: any[] };
}

export interface FileNode {
  path: string;
  language: string;
  loc: number;
  complexity: number;
  risk: RiskSeverity;
}

export interface Risk {
  id: string;
  title: string;
  category: string;
  severity: RiskSeverity;
  files: string[];
  recommendation: string;
  mcp_solution?: boolean;
}

export interface Suggestion {
  id: string;
  title: string;
  description: string;
  priority: number;
  effort: "low" | "medium" | "high";
  benefits: string[];
  risks: string[];
  before?: string;
  after?: string;
  mcp_based?: boolean;
}

export interface QueryMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  references?: string[];
  confidence?: number;
  timestamp: string;
}