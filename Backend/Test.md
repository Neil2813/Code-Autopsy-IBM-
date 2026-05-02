# API Testing Guide

## Prerequisites

1. **Start the server:**
```bash
cd Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Access API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 1. Health Check

### GET /api/v1/health

**Description:** Check if the API is running

**cURL:**
```bash
curl http://localhost:8000/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-01T15:00:00Z"
}
```

---

## 2. Upload Endpoints

### 2.1 Upload Files

**POST /api/v1/upload/files**

**Description:** Upload one or more source code files

**cURL (Single File):**
```bash
curl -X POST http://localhost:8000/api/v1/upload/files \
  -F "files=@path/to/your/file.java"
```

**cURL (Multiple Files):**
```bash
curl -X POST http://localhost:8000/api/v1/upload/files \
  -F "files=@file1.java" \
  -F "files=@file2.java" \
  -F "files=@file3.java"
```

**PowerShell (Windows):**
```powershell
$files = @{
    files = Get-Item "C:\path\to\file.java"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/upload/files" -Method Post -Form $files
```

**Expected Response:**
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "files": [
    {
      "filename": "file.java",
      "size_bytes": 1024,
      "language": "java"
    }
  ],
  "total_files": 1,
  "total_size_bytes": 1024,
  "primary_language": "java",
  "detected_languages": ["java"],
  "message": "Files uploaded successfully"
}
```

---

### 2.2 Upload Repository

**POST /api/v1/upload/repository**

**Description:** Clone a Git repository for analysis

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/upload/repository \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repo.git",
    "branch": "main"
  }'
```

**Request Body:**
```json
{
  "repository_url": "https://github.com/username/repo.git",
  "branch": "main"
}
```

**Expected Response:**
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440001",
  "files": [],
  "total_files": 0,
  "total_size_bytes": 0,
  "primary_language": "unknown",
  "detected_languages": [],
  "message": "Repository cloning queued"
}
```

---

### 2.3 Upload Code Snippet

**POST /api/v1/upload/snippet**

**Description:** Upload a code snippet for quick analysis

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/upload/snippet \
  -H "Content-Type: application/json" \
  -d '{
    "code": "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}",
    "language": "java",
    "filename": "HelloWorld.java"
  }'
```

**Request Body:**
```json
{
  "code": "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}",
  "language": "java",
  "filename": "HelloWorld.java"
}
```

**Expected Response:**
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440002",
  "files": [
    {
      "filename": "HelloWorld.java",
      "size_bytes": 150,
      "language": "java"
    }
  ],
  "total_files": 1,
  "total_size_bytes": 150,
  "primary_language": "java",
  "detected_languages": ["java"],
  "message": "Code snippet uploaded successfully"
}
```

---

## 3. Analysis Endpoints

### 3.1 Start Analysis

**POST /api/v1/analyze**

**Description:** Start analyzing uploaded code

**cURL (Basic):**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**cURL (With Configuration):**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "config": {
      "enable_mcp": true,
      "enable_dependency_analysis": true,
      "enable_risk_detection": true,
      "enable_suggestion_generation": true,
      "max_file_size_mb": 10,
      "focus_areas": ["security", "maintainability"]
    },
    "priority": "high"
  }'
```

**Request Body (Full Options):**
```json
{
  "job_id": "ce1e6107-204e-4348-84ed-1128e0d3b3fe",
  "config": {
    "enable_mcp": true,
    "enable_dependency_analysis": true,
    "enable_risk_detection": true,
    "enable_suggestion_generation": true,
    "max_file_size_mb": 10,
    "languages_to_analyze": ["java"],
    "focus_areas": ["security", "performance", "maintainability"]
  },
  "priority": "normal"
}
```

**Expected Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Analysis queued successfully",
  "estimated_duration_seconds": 300
}
```

---

## 4. Job Management Endpoints

### 4.1 Get Job Status

**GET /api/v1/jobs/{job_id}**

**Description:** Check the status of an analysis job

**cURL:**
```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Expected Response (Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress_percent": 45.5,
  "current_stage": "analyze",
  "stages_completed": ["ingest", "parse", "classify"],
  "created_at": "2026-05-01T15:00:00Z",
  "updated_at": "2026-05-01T15:02:30Z"
}
```

**Expected Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress_percent": 100.0,
  "current_stage": "report",
  "stages_completed": ["ingest", "parse", "classify", "analyze", "explain", "recommend", "validate", "report"],
  "created_at": "2026-05-01T15:00:00Z",
  "updated_at": "2026-05-01T15:05:00Z"
}
```

---

### 4.2 Get Job Results

**GET /api/v1/jobs/{job_id}/results**

**Description:** Get the complete analysis results

**cURL:**
```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/results
```

**Expected Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "summary": {
    "total_files": 10,
    "total_lines": 5000,
    "languages": ["java"],
    "risk_score": 6.5,
    "maintainability_index": 72.3
  },
  "risks": [
    {
      "id": "risk-001",
      "title": "Hardcoded credentials detected",
      "category": "security",
      "level": "high",
      "affected_files": ["src/config/Database.java"],
      "recommendation": "Use environment variables or secure vault"
    }
  ],
  "suggestions": [
    {
      "id": "sugg-001",
      "type": "refactoring",
      "title": "Extract method to reduce complexity",
      "priority": 2,
      "effort_estimate": "medium"
    }
  ]
}
```

---

### 4.3 Cancel Job

**DELETE /api/v1/jobs/{job_id}**

**Description:** Cancel a running analysis job

**cURL:**
```bash
curl -X DELETE http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Expected Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

---

## 5. Query Endpoints (Currently 501 - Not Implemented)

### 5.1 Ask Question

**POST /api/v1/query**

**Description:** Ask natural language questions about the codebase

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "Where is authentication handled in this codebase?"
  }'
```

**Request Body:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Where is authentication handled in this codebase?",
  "context_limit": 5
}
```

**Expected Response (When Implemented):**
```json
{
  "answer": "Authentication is handled in the SecurityConfig.java file...",
  "confidence": 0.85,
  "references": [
    {
      "file": "src/security/SecurityConfig.java",
      "line_number": 45
    }
  ],
  "related_files": ["SecurityConfig.java", "AuthController.java"]
}
```

---

### 5.2 Get Query History

**GET /api/v1/query/history/{job_id}**

**Description:** Get all queries asked about a job

**cURL:**
```bash
curl http://localhost:8000/api/v1/query/history/550e8400-e29b-41d4-a716-446655440000
```

---

## 6. Report Endpoints (Currently 501 - Not Implemented)

### 6.1 Generate Report

**POST /api/v1/report**

**Description:** Generate a comprehensive analysis report

**cURL (Markdown):**
```bash
curl -X POST http://localhost:8000/api/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "format": "markdown"
  }'
```

**cURL (JSON):**
```bash
curl -X POST http://localhost:8000/api/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "format": "json",
    "include_code_snippets": true,
    "include_dependency_graph": true
  }'
```

**Request Body:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "format": "markdown",
  "include_code_snippets": true,
  "include_dependency_graph": true,
  "sections": ["summary", "risks", "suggestions", "dependencies"]
}
```

---

### 6.2 Download Report

**GET /api/v1/report/{report_id}/download**

**Description:** Download a generated report

**cURL:**
```bash
curl -O http://localhost:8000/api/v1/report/550e8400-e29b-41d4-a716-446655440000/download
```

---

### 6.3 Get Report Metadata

**GET /api/v1/report/{report_id}**

**Description:** Get report metadata

**cURL:**
```bash
curl http://localhost:8000/api/v1/report/550e8400-e29b-41d4-a716-446655440000
```

---

## Complete Testing Workflow

### Step 1: Upload Files
```bash
# Upload a Java file
curl -X POST http://localhost:8000/api/v1/upload/files \
  -F "files=@MyClass.java"

# Save the job_id from response
JOB_ID="<job_id_from_response>"
```

### Step 2: Start Analysis
```bash
# Start analysis with the job_id
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d "{\"job_id\": \"$JOB_ID\"}"
```

### Step 3: Check Status
```bash
# Check status (repeat until completed)
curl http://localhost:8000/api/v1/jobs/$JOB_ID
```

### Step 4: Get Results
```bash
# Get complete results
curl http://localhost:8000/api/v1/jobs/$JOB_ID/results
```

---

## Testing with Postman

### Import Collection

Create a Postman collection with these requests:

1. **Health Check** - GET http://localhost:8000/api/v1/health
2. **Upload Files** - POST http://localhost:8000/api/v1/upload/files (form-data)
3. **Start Analysis** - POST http://localhost:8000/api/v1/analyze (JSON body)
4. **Get Job Status** - GET http://localhost:8000/api/v1/jobs/{{job_id}}
5. **Get Results** - GET http://localhost:8000/api/v1/jobs/{{job_id}}/results

### Environment Variables
- `base_url`: http://localhost:8000
- `job_id`: (set from upload response)

---

## Common Issues & Solutions

### Issue: "Job not found"
**Solution:** Make sure you're using the correct `job_id` from the upload response

### Issue: "Analysis not complete"
**Solution:** Wait for the job status to be "completed" before requesting results

### Issue: "File too large"
**Solution:** Check `max_file_size_mb` in analysis config (default: 10MB)

### Issue: "Invalid file type"
**Solution:** Ensure file has a supported extension (.java, .cobol, .rpg, .jcl, etc.)

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created
- `202 Accepted` - Request accepted for processing
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `501 Not Implemented` - Feature not yet implemented

---

## Next Steps

1. Test upload endpoints with your files
2. Start an analysis job
3. Monitor job progress
4. Retrieve results
5. Report any issues or unexpected behavior

For more details, visit the interactive API documentation at http://localhost:8000/docs