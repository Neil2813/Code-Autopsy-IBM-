import { apiClient, getApiBaseUrl } from "./client";
import type {
  AnalysisResponse,
  JobDetails,
  JobResults,
  QueryHistory,
  QueryResponse,
  ReportFormat,
  ReportResponse,
  UploadResponse,
} from "@/types/api";

const JOB_CACHE_KEY = "ibm-bob-recent-jobs";

type CachedJob = {
  id: string;
  project_name: string;
  status: string;
  progress: number;
  languages: string[];
  file_count: number;
  total_size_bytes: number;
  created_at: string;
};

const apiPath = (path: string) => `/api/v1${path}`;

const readJobs = (): CachedJob[] => {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(JOB_CACHE_KEY) || "[]");
  } catch {
    return [];
  }
};

const writeJobs = (jobs: CachedJob[]) => {
  if (typeof window !== "undefined") {
    localStorage.setItem(JOB_CACHE_KEY, JSON.stringify(jobs.slice(0, 20)));
  }
};

const rememberUpload = (upload: UploadResponse, projectName?: string) => {
  const languages = upload.detected_languages?.length
    ? upload.detected_languages
    : upload.primary_language
      ? [upload.primary_language]
      : [];
  const cached: CachedJob = {
    id: upload.job_id,
    project_name: projectName || upload.files?.[0]?.filename || `Analysis ${upload.job_id.slice(0, 8)}`,
    status: upload.status,
    progress: 0,
    languages,
    file_count: upload.total_files,
    total_size_bytes: upload.total_size_bytes,
    created_at: new Date().toISOString(),
  };
  writeJobs([cached, ...readJobs().filter((job) => job.id !== upload.job_id)]);
};

const updateCachedJob = (job: Pick<JobDetails, "job_id" | "status" | "progress_percent" | "created_at">) => {
  const jobs = readJobs();
  const index = jobs.findIndex((item) => item.id === job.job_id);
  if (index >= 0) {
    jobs[index] = {
      ...jobs[index],
      status: job.status,
      progress: job.progress_percent,
      created_at: job.created_at || jobs[index].created_at,
    };
    writeJobs(jobs);
  }
};

export const uploadService = {
  uploadFiles: async (files: File[], projectName?: string) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    const response = await apiClient.post<UploadResponse>(apiPath("/upload/files"), formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    rememberUpload(response.data, projectName);
    return response;
  },

  uploadRepository: async (repositoryUrl: string, branch = "main", projectName?: string) => {
    const response = await apiClient.post<UploadResponse>(apiPath("/upload/repository"), {
      repository_url: repositoryUrl,
      branch,
    }, {
      timeout: 0,
    });
    rememberUpload(response.data, projectName);
    return response;
  },

  uploadSnippet: async (code: string, language?: string, projectName?: string, description?: string) => {
    const response = await apiClient.post<UploadResponse>(apiPath("/upload/snippet"), {
      code,
      language: language === "auto" ? undefined : language,
      filename: language && language !== "auto" ? `snippet.${language === "cobol" ? "cbl" : language}` : undefined,
      description,
    });
    rememberUpload(response.data, projectName);
    return response;
  },
};

export const analysisService = {
  start: (jobId: string) =>
    apiClient.post<AnalysisResponse>(apiPath("/analyze"), {
      job_id: jobId,
      config: {
        enable_mcp: true,
        enable_dependency_analysis: true,
        enable_risk_detection: true,
        enable_suggestion_generation: true,
      },
      priority: "normal",
    }),

  getJobStatus: async (jobId: string) => {
    const response = await apiClient.get<JobDetails>(apiPath(`/jobs/${jobId}`));
    updateCachedJob(response.data);
    return response;
  },

  getResults: (jobId: string) => apiClient.get<JobResults>(apiPath(`/jobs/${jobId}/results`)),

  getCodeReview: (jobId: string) => apiClient.get<CodeReview>(apiPath(`/jobs/${jobId}/code-review`)),

  cancelJob: (jobId: string) => apiClient.delete(apiPath(`/jobs/${jobId}`)),

  listJobs: async ({ limit }: { limit?: number } = {}) => {
    const jobs = readJobs();
    return { data: { jobs: typeof limit === "number" ? jobs.slice(0, limit) : jobs } };
  },
};

export const dashboardService = {
  getStats: async () => {
    try {
      // Try to fetch from backend API
      const response = await apiClient.get<{
        analyses_this_month: number;
        avg_risk_score: number | null;
        lines_analyzed: number | null;
        hours_saved: number;
      }>(apiPath("/dashboard/stats"));
      
      return {
        data: {
          analyses_this_month: response.data.analyses_this_month,
          avg_risk_score: response.data.avg_risk_score,
          lines_analyzed: response.data.lines_analyzed,
          hours_saved: response.data.hours_saved,
        },
      };
    } catch (error) {
      // Fallback to local cache if backend is unavailable
      const jobs = readJobs();
      const completed = jobs.filter((job) => job.status === "completed");
      return {
        data: {
          analyses_this_month: jobs.length,
          avg_risk_score: null,
          lines_analyzed: null,
          hours_saved: completed.length ? completed.length * 4 : 0,
        },
      };
    }
  },
};

export const queryService = {
  ask: (jobId: string, question: string) =>
    apiClient.post<QueryResponse>(apiPath("/query"), {
      job_id: jobId,
      question,
    }),

  history: async (jobId: string) => {
    const response = await apiClient.get<QueryHistory>(apiPath(`/query/history/${jobId}`));
    return {
      ...response,
      data: {
        ...response.data,
        messages: response.data.queries.flatMap((query) => {
          const timestamp = query.created_at || query.timestamp || new Date().toISOString();
          return [
          {
            id: `${query.query_id}-question`,
            role: "user" as const,
            content: query.question,
            timestamp,
          },
          {
            id: `${query.query_id}-answer`,
            role: "assistant" as const,
            content: query.answer_full ?? query.answer_preview,
            confidence: query.confidence,
            timestamp,
          },
        ];
        }),
      },
    };
  },
};

export const reportService = {
  generate: (jobId: string, format: string, sections: string[]) => {
    const reportSections = sections.filter((section) => section !== "snippets" && section !== "graph");
    return apiClient.post<ReportResponse>(apiPath("/report"), {
      job_id: jobId,
      format: format as ReportFormat,
      sections: reportSections.length ? reportSections : ["all"],
      include_code_snippets: sections.includes("snippets"),
      include_dependency_graph: sections.includes("dependencies") || sections.includes("graph"),
    });
  },

  downloadUrl: (downloadUrl?: string) => {
    if (!downloadUrl) return "";
    return `${getApiBaseUrl()}${downloadUrl}`;
  },

  download: (reportId: string) => apiClient.get(apiPath(`/report/${reportId}/download`), { responseType: "blob" }),
};
