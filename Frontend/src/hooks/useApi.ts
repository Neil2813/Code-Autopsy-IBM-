/**
 * React Query Hooks for IBM BOB API
 * Provides easy-to-use hooks for data fetching and mutations
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
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
import * as api from '@/services/api.service';

// ============================================================================
// Query Keys
// ============================================================================

export const queryKeys = {
  health: ['health'] as const,
  jobs: {
    all: ['jobs'] as const,
    detail: (jobId: string) => ['jobs', jobId] as const,
    results: (jobId: string) => ['jobs', jobId, 'results'] as const,
  },
  queries: {
    history: (jobId: string) => ['queries', 'history', jobId] as const,
  },
  reports: {
    detail: (reportId: string) => ['reports', reportId] as const,
  },
};

// ============================================================================
// Health Check Hooks
// ============================================================================

export const useHealthCheck = (options?: UseQueryOptions<HealthCheckResponse>) => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.checkHealth,
    refetchInterval: 30000, // Refetch every 30 seconds
    ...options,
  });
};

// ============================================================================
// Upload Hooks
// ============================================================================

export const useUploadFile = (
  options?: UseMutationOptions<UploadResponse, Error, FileUploadRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.uploadFile,
    onSuccess: (data) => {
      // Invalidate jobs list
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
    ...options,
  });
};

export const useUploadRepository = (
  options?: UseMutationOptions<UploadResponse, Error, RepositoryUploadRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.uploadRepository,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
    ...options,
  });
};

export const useUploadSnippet = (
  options?: UseMutationOptions<UploadResponse, Error, SnippetUploadRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.uploadSnippet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
    ...options,
  });
};

// ============================================================================
// Analysis Hooks
// ============================================================================

export const useStartAnalysis = (
  options?: UseMutationOptions<AnalysisResponse, Error, AnalysisRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.startAnalysis,
    onSuccess: (data, variables) => {
      // Invalidate job details to trigger refetch
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.jobs.detail(variables.job_id) 
      });
    },
    ...options,
  });
};

// ============================================================================
// Job Hooks
// ============================================================================

export const useJobDetails = (
  jobId: string,
  options?: UseQueryOptions<JobDetails>
) => {
  return useQuery({
    queryKey: queryKeys.jobs.detail(jobId),
    queryFn: () => api.getJobDetails(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Auto-refetch every 2 seconds if job is still processing
      const data = query.state.data;
      if (data?.status === 'pending' || data?.status === 'processing') {
        return 2000;
      }
      return false;
    },
    ...options,
  });
};

export const useJobResults = (
  jobId: string,
  options?: UseQueryOptions<JobResults>
) => {
  return useQuery({
    queryKey: queryKeys.jobs.results(jobId),
    queryFn: () => api.getJobResults(jobId),
    enabled: !!jobId,
    ...options,
  });
};

export const useCancelJob = (
  options?: UseMutationOptions<{ message: string }, Error, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.cancelJob,
    onSuccess: (data, jobId) => {
      // Invalidate job details
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.jobs.detail(jobId) 
      });
    },
    ...options,
  });
};

// ============================================================================
// Query Hooks
// ============================================================================

export const useQueryCode = (
  options?: UseMutationOptions<QueryResponse, Error, QueryRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.queryCode,
    onSuccess: (data, variables) => {
      // Invalidate query history
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.queries.history(variables.job_id) 
      });
    },
    ...options,
  });
};

export const useQueryHistory = (
  jobId: string,
  options?: UseQueryOptions<QueryHistory>
) => {
  return useQuery({
    queryKey: queryKeys.queries.history(jobId),
    queryFn: () => api.getQueryHistory(jobId),
    enabled: !!jobId,
    ...options,
  });
};

// ============================================================================
// Report Hooks
// ============================================================================

export const useGenerateReport = (
  options?: UseMutationOptions<ReportResponse, Error, ReportGenerationRequest>
) => {
  return useMutation({
    mutationFn: api.generateReport,
    ...options,
  });
};

export const useReportMetadata = (
  reportId: string,
  options?: UseQueryOptions<ReportMetadata>
) => {
  return useQuery({
    queryKey: queryKeys.reports.detail(reportId),
    queryFn: () => api.getReportMetadata(reportId),
    enabled: !!reportId,
    ...options,
  });
};

export const useDownloadReport = (
  options?: UseMutationOptions<Blob, Error, string>
) => {
  return useMutation({
    mutationFn: api.downloadReport,
    ...options,
  });
};

// ============================================================================
// Combined Hooks
// ============================================================================

/**
 * Upload file and start analysis with automatic polling
 */
export const useUploadAndAnalyze = () => {
  const uploadFile = useUploadFile();
  const startAnalysis = useStartAnalysis();

  const uploadAndAnalyze = async (
    file: File,
    language?: string,
    analysisConfig?: AnalysisRequest['config']
  ) => {
    // Upload file
    const uploadResult = await uploadFile.mutateAsync({ file, language });

    // Start analysis
    const analysisResult = await startAnalysis.mutateAsync({
      job_id: uploadResult.job_id,
      config: analysisConfig,
    });

    return {
      jobId: uploadResult.job_id,
      uploadResult,
      analysisResult,
    };
  };

  return {
    uploadAndAnalyze,
    isLoading: uploadFile.isPending || startAnalysis.isPending,
    error: uploadFile.error || startAnalysis.error,
  };
};

/**
 * Poll job status with automatic refetching
 */
export const useJobPolling = (jobId: string, enabled: boolean = true) => {
  const { data: job, isLoading, error } = useJobDetails(jobId, {
    enabled: enabled && !!jobId,
  } as any);

  const isProcessing = job?.status === 'pending' || job?.status === 'processing';
  const isCompleted = job?.status === 'completed';
  const isFailed = job?.status === 'failed';
  const isCancelled = job?.status === 'cancelled';

  return {
    job,
    isLoading,
    error,
    isProcessing,
    isCompleted,
    isFailed,
    isCancelled,
    progress: job?.progress_percent || 0,
    currentStage: job?.current_stage,
  };
};

// Made with Bob
