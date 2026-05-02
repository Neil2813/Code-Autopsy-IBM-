# Frontend-Backend Integration Guide

## IBM BOB Legacy Code Modernization Copilot

This guide explains how the Frontend (React/TypeScript/Vite) integrates with the Backend (FastAPI/Python).

---

## 🔗 Integration Overview

### Architecture
```
┌─────────────────┐         HTTP/REST API          ┌─────────────────┐
│                 │    ←─────────────────────→     │                 │
│  React Frontend │                                │  FastAPI Backend│
│  (Port 8080)    │    JSON Request/Response       │  (Port 8000)    │
│                 │                                │                 │
└─────────────────┘                                └─────────────────┘
```

### Key Components

1. **API Client** (`src/lib/api-client.ts`)
   - Axios-based HTTP client
   - Request/response interceptors
   - Authentication token handling
   - Error handling

2. **Type Definitions** (`src/types/api.ts`)
   - TypeScript interfaces matching Backend Pydantic schemas
   - Type-safe API calls

3. **API Services** (`src/services/api.service.ts`)
   - Typed API functions for all endpoints
   - File upload handling
   - Polling utilities

4. **React Query Hooks** (`src/hooks/useApi.ts`)
   - Easy-to-use hooks for components
   - Automatic caching and refetching
   - Optimistic updates

---

## 🚀 Getting Started

### 1. Install Dependencies

Frontend dependencies are already installed. If needed:

```bash
cd Frontend
npm install
```

### 2. Configure Environment

The environment files are already created:

**Development** (`.env.development`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_ENABLE_AUTH=false
```

**Production** (`.env.production`):
```env
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_API_TIMEOUT=60000
VITE_ENABLE_AUTH=true
```

### 3. Start Backend

```bash
cd Backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 4. Start Frontend

```bash
cd Frontend
npm run dev
```

Frontend will be available at: `http://localhost:8080`

---

## 🔧 Configuration Details

### CORS Configuration

**Backend** (`Backend/.env`):
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8080
```

The Backend is configured to accept requests from the Frontend origin.

### Vite Proxy Configuration

**Frontend** (`vite.config.ts`):
```typescript
server: {
  port: 8080,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

This proxies API requests through Vite dev server to avoid CORS issues in development.

---

## 📡 API Endpoints

### Upload Endpoints
- `POST /api/v1/upload/files` - Upload single file
- `POST /api/v1/upload/repository` - Upload repository
- `POST /api/v1/upload/snippet` - Upload code snippet

### Analysis Endpoints
- `POST /api/v1/analyze` - Start analysis

### Job Endpoints
- `GET /api/v1/jobs/{job_id}` - Get job details
- `GET /api/v1/jobs/{job_id}/results` - Get analysis results
- `DELETE /api/v1/jobs/{job_id}` - Cancel job

### Query Endpoints
- `POST /api/v1/query` - Ask question about code
- `GET /api/v1/query/history/{job_id}` - Get query history

### Report Endpoints
- `POST /api/v1/report` - Generate report
- `GET /api/v1/report/{report_id}` - Get report metadata
- `GET /api/v1/report/{report_id}/download` - Download report

### Health Check
- `GET /api/v1/health` - Check API health

---

## 💻 Usage Examples

### Example 1: Upload and Analyze File

```typescript
import { useUploadAndAnalyze, useJobPolling } from '@/hooks/useApi';

function UploadPage() {
  const { uploadAndAnalyze, isLoading } = useUploadAndAnalyze();
  const [jobId, setJobId] = useState<string | null>(null);
  
  const { job, isProcessing, isCompleted, progress } = useJobPolling(
    jobId || '',
    !!jobId
  );

  const handleUpload = async (file: File) => {
    const result = await uploadAndAnalyze(file, 'java');
    setJobId(result.jobId);
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
      {isProcessing && <p>Progress: {progress}%</p>}
      {isCompleted && <p>Analysis complete!</p>}
    </div>
  );
}
```

### Example 2: Query Code

```typescript
import { useQueryCode } from '@/hooks/useApi';

function QueryPage({ jobId }: { jobId: string }) {
  const queryMutation = useQueryCode();

  const handleQuery = async (question: string) => {
    const response = await queryMutation.mutateAsync({
      job_id: jobId,
      question,
    });
    console.log('Answer:', response.answer);
  };

  return (
    <div>
      <input 
        type="text" 
        onKeyPress={(e) => {
          if (e.key === 'Enter') handleQuery(e.currentTarget.value);
        }}
      />
    </div>
  );
}
```

### Example 3: Generate and Download Report

```typescript
import { useGenerateReport, useDownloadReport } from '@/hooks/useApi';

function ReportPage({ jobId }: { jobId: string }) {
  const generateReport = useGenerateReport();
  const downloadReport = useDownloadReport();

  const handleGenerateReport = async () => {
    const report = await generateReport.mutateAsync({
      job_id: jobId,
      format: 'markdown',
      options: {
        include_summary: true,
        include_risks: true,
        include_suggestions: true,
      },
    });

    // Download the report
    const blob = await downloadReport.mutateAsync(report.report_id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${report.report_id}.md`;
    a.click();
  };

  return (
    <button onClick={handleGenerateReport}>
      Generate Report
    </button>
  );
}
```

### Example 4: Health Check

```typescript
import { useHealthCheck } from '@/hooks/useApi';

function HealthStatus() {
  const { data: health, isLoading } = useHealthCheck();

  if (isLoading) return <div>Checking...</div>;

  return (
    <div>
      <p>Status: {health?.status}</p>
      <p>Database: {health?.services.database}</p>
      <p>LLM Provider: {health?.services.llm_provider}</p>
    </div>
  );
}
```

---

## 🔍 Testing the Integration

### 1. Test Health Check

```bash
# Backend should be running
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-01T...",
  "services": {
    "database": "up",
    "llm_provider": "up"
  }
}
```

### 2. Test File Upload

```bash
curl -X POST http://localhost:8000/api/v1/upload/files \
  -F "file=@test.java" \
  -F "language=java"
```

### 3. Test from Frontend

1. Open browser to `http://localhost:8080`
2. Open DevTools Network tab
3. Upload a file
4. Verify API calls to `http://localhost:8000/api/v1/...`
5. Check for CORS headers in response

---

## 🐛 Troubleshooting

### CORS Errors

**Problem**: `Access-Control-Allow-Origin` error in browser console

**Solution**:
1. Verify Backend `.env` has `ALLOWED_ORIGINS=http://localhost:8080`
2. Restart Backend server
3. Clear browser cache

### Connection Refused

**Problem**: `ERR_CONNECTION_REFUSED` when calling API

**Solution**:
1. Verify Backend is running: `curl http://localhost:8000/api/v1/health`
2. Check Backend logs for errors
3. Verify port 8000 is not blocked by firewall

### 404 Not Found

**Problem**: API endpoints return 404

**Solution**:
1. Check API prefix in Backend: `/api/v1`
2. Verify endpoint path in Frontend matches Backend
3. Check Backend logs for routing errors

### Type Errors

**Problem**: TypeScript errors in Frontend

**Solution**:
1. Run `npm install` to ensure all dependencies are installed
2. Check `tsconfig.json` configuration
3. Verify type definitions in `src/types/api.ts` match Backend schemas

---

## 📊 Monitoring

### Backend Logs

Backend logs include:
- Request/response details
- Error messages
- Performance metrics

View logs in terminal where Backend is running.

### Frontend Logs

Frontend logs include:
- API request/response (in browser console)
- React Query cache status
- Component lifecycle events

Open browser DevTools Console to view.

### Network Monitoring

Use browser DevTools Network tab to:
- Inspect API requests/responses
- Check request headers (Authorization, Content-Type)
- Verify response status codes
- Monitor request timing

---

## 🚢 Production Deployment

### Backend Deployment

1. Update `.env` with production values
2. Set `ALLOWED_ORIGINS` to production Frontend URL
3. Use production database (PostgreSQL)
4. Enable HTTPS
5. Deploy using Docker or cloud platform

### Frontend Deployment

1. Update `.env.production` with production API URL
2. Build production bundle: `npm run build`
3. Deploy `dist/` folder to static hosting (Vercel, Netlify, etc.)
4. Configure CDN and caching
5. Enable HTTPS

### Environment Variables

**Backend Production**:
```env
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
```

**Frontend Production**:
```env
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_ENABLE_AUTH=true
VITE_ENABLE_ANALYTICS=true
```

---

## 📚 Additional Resources

- [Backend API Documentation](http://localhost:8000/docs)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Axios Documentation](https://axios-http.com/)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [Vite Proxy Documentation](https://vitejs.dev/config/server-options.html#server-proxy)

---

## ✅ Integration Checklist

- [x] API client configured (`src/lib/api-client.ts`)
- [x] Type definitions created (`src/types/api.ts`)
- [x] API services implemented (`src/services/api.service.ts`)
- [x] React Query hooks created (`src/hooks/useApi.ts`)
- [x] Environment variables configured (`.env.development`, `.env.production`)
- [x] Vite proxy configured (`vite.config.ts`)
- [x] Backend CORS updated (`Backend/.env`)
- [ ] Test health check endpoint
- [ ] Test file upload flow
- [ ] Test analysis workflow
- [ ] Test query functionality
- [ ] Test report generation
- [ ] Verify error handling
- [ ] Test in production environment

---

**Integration Status**: ✅ Complete

The Frontend is now fully integrated with the Backend. All API endpoints are accessible through typed service functions and React Query hooks.