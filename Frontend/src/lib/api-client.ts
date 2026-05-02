/**
 * API Client Configuration for IBM BOB Legacy Modernization Copilot
 * Connects React Frontend to FastAPI Backend
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 0,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

// Request interceptor - Add auth token if available
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage if available
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add correlation ID for request tracking
    const correlationId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    if (config.headers) {
      config.headers['X-Correlation-ID'] = correlationId;
    }
    
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
      correlationId,
      params: config.params,
    });
    
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
      status: response.status,
      data: response.data,
    });
    return response;
  },
  (error: AxiosError) => {
    // Handle different error scenarios
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;
      
      console.error(`[API Error ${status}]`, {
        url: error.config?.url,
        method: error.config?.method,
        status,
        message: data?.message || data?.detail || 'Unknown error',
        data,
      });
      
      // Handle specific status codes
      switch (status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          break;
        case 403:
          // Forbidden
          console.error('Access forbidden');
          break;
        case 404:
          // Not found
          console.error('Resource not found');
          break;
        case 422:
          // Validation error
          console.error('Validation error:', data);
          break;
        case 500:
          // Server error
          console.error('Server error');
          break;
        case 501:
          // Not implemented
          console.warn('Feature not yet implemented');
          break;
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('[API Network Error]', {
        message: 'No response from server',
        url: error.config?.url,
      });
    } else {
      // Error in request setup
      console.error('[API Setup Error]', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Export configured client
export default apiClient;

// Export base URL for file uploads and downloads
export const API_BASE = `${API_BASE_URL}${API_PREFIX}`;
export const UPLOAD_URL = `${API_BASE}/upload`;
export const DOWNLOAD_URL = `${API_BASE}/report`;

// Made with Bob
