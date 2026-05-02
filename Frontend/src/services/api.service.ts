/**
 * API Service Functions for IBM BOB Legacy Modernization Copilot
 * Provides typed API calls to the Backend
 */

import apiClient, { API_BASE } from '@/lib/api-client';
import type {
  // Upload
  FileUploadRequest,
  RepositoryUploadRequest,
  SnippetUploadRequest,
  UploadResponse,
  // Analysis
  AnalysisRequest,
  AnalysisResponse,
  // Job
  JobDetails,
  JobResults,
  // Query
  QueryRequest,
  QueryResponse,
  QueryHistory,
  // Report
  ReportGenerationRequest,
  ReportResponse,
  ReportMetadata,
  // Health
  HealthCheckResponse,
} from '@/types/api';

// ============================================================================
// Upload API
// ============================================================================

/**
 * Upload a single file for analysis
 */
export const uploadFile = async (request: FileUploadRequest): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('files', request.file);

  const response = await apiClient.post<UploadResponse>('/upload/files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Upload a repository for analysis
 */
export const uploadRepository = async (
  request: RepositoryUploadRequest
): Promise<UploadResponse> => {
  const response = await apiClient.post<UploadResponse>('/upload/repository', request);
  return response.data;
};

/**
 * Upload a code snippet for analysis
 */
export const uploadSnippet = async (
  request: SnippetUploadRequest
): Promise<UploadResponse> => {
  const response = await apiClient.post<UploadResponse>('/upload/snippet', request);
  return response.data;
};

// ============================================================================
// Analysis API
// ============================================================================

/**
 * Start analysis for a job
 */
export const startAnalysis = async (request: AnalysisRequest): Promise<AnalysisResponse> => {
  const response = await apiClient.post<AnalysisResponse>('/analyze', request);
  return response.data;
};

// ============================================================================
// Job API
// ============================================================================

/**
 * Get job details and status
 */
export const getJobDetails = async (jobId: string): Promise<JobDetails> => {
  const response = await apiClient.get<JobDetails>(`/jobs/${jobId}`);
  return response.data;
};

/**
 * Get job analysis results
 */
export const getJobResults = async (jobId: string): Promise<JobResults> => {
  const response = await apiClient.get<JobResults>(`/jobs/${jobId}/results`);
  return response.data;
};

/**
 * Cancel a job
 */
export const cancelJob = async (jobId: string): Promise<{ message: string }> => {
  const response = await apiClient.delete<{ message: string }>(`/jobs/${jobId}`);
  return response.data;
};

// ============================================================================
// Query API
// ============================================================================

/**
 * Ask a question about the analyzed code
 */
export const queryCode = async (request: QueryRequest): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>('/query', request);
  return response.data;
};

/**
 * Get query history for a job
 */
export const getQueryHistory = async (jobId: string): Promise<QueryHistory> => {
  const response = await apiClient.get<QueryHistory>(`/query/history/${jobId}`);
  return response.data;
};

// ============================================================================
// Report API
// ============================================================================

/**
 * Generate a report for a job
 */
export const generateReport = async (
  request: ReportGenerationRequest
): Promise<ReportResponse> => {
  const response = await apiClient.post<ReportResponse>('/report', request);
  return response.data;
};

/**
 * Get report metadata
 */
export const getReportMetadata = async (reportId: string): Promise<ReportMetadata> => {
  const response = await apiClient.get<ReportMetadata>(`/report/${reportId}`);
  return response.data;
};

/**
 * Get download URL for a report
 */
export const getReportDownloadUrl = (reportId: string): string => {
  return `${API_BASE}/report/${reportId}/download`;
};

/**
 * Download a report
 */
export const downloadReport = async (reportId: string): Promise<Blob> => {
  const response = await apiClient.get(`/report/${reportId}/download`, {
    responseType: 'blob',
  });
  return response.data;
};

// ============================================================================
// Health Check API
// ============================================================================

/**
 * Check API health status
 */
export const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await apiClient.get<HealthCheckResponse>('/health');
  return response.data;
};

// ============================================================================
// Polling Utilities
// ============================================================================

/**
 * Poll job status until completion or failure
 * @param jobId - Job ID to poll
 * @param onProgress - Callback for progress updates
 * @param interval - Polling interval in milliseconds (default: 2000)
 * @param timeout - Maximum polling time in milliseconds (default: 300000 = 5 minutes)
 */
export const pollJobStatus = async (
  jobId: string,
  onProgress?: (job: JobDetails) => void,
  interval: number = 2000,
  timeout: number = 300000
): Promise<JobDetails> => {
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        // Check timeout
        if (Date.now() - startTime > timeout) {
          reject(new Error('Job polling timeout'));
          return;
        }

        // Get job status
        const job = await getJobDetails(jobId);

        // Call progress callback
        if (onProgress) {
          onProgress(job);
        }

        // Check if job is complete
        if (job.status === 'completed') {
          resolve(job);
          return;
        }

        // Check if job failed
        if (job.status === 'failed' || job.status === 'cancelled') {
          reject(new Error(job.error_message || `Job ${job.status}`));
          return;
        }

        // Continue polling
        setTimeout(poll, interval);
      } catch (error) {
        reject(error);
      }
    };

    // Start polling
    poll();
  });
};

/**
 * Upload file and start analysis in one call
 */
export const uploadAndAnalyze = async (
  file: File,
  language?: string,
  analysisConfig?: AnalysisRequest['config']
): Promise<{ jobId: string; uploadResponse: UploadResponse; analysisResponse: AnalysisResponse }> => {
  // Upload file
  const uploadResponse = await uploadFile({ file, language });

  // Start analysis
  const analysisResponse = await startAnalysis({
    job_id: uploadResponse.job_id,
    config: analysisConfig,
  });

  return {
    jobId: uploadResponse.job_id,
    uploadResponse,
    analysisResponse,
  };
};

// Made with Bob
