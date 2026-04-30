"""
Upload-related Pydantic schemas.

This module contains schemas for:
- File upload requests
- Repository upload requests
- Upload responses
"""

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import FileTypeEnum, LanguageEnum


class FileUploadRequest(BaseModel):
    """Request schema for individual file upload."""

    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="File content (base64 encoded for binary files)")
    content_type: Optional[str] = Field(None, description="MIME type")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "Main.java",
                "content": "public class Main { ... }",
                "content_type": "text/plain",
            }
        }


class RepositoryUploadRequest(BaseModel):
    """Request schema for repository URL upload."""

    repository_url: HttpUrl = Field(..., description="Git repository URL")
    branch: Optional[str] = Field("main", description="Branch name")
    subdirectory: Optional[str] = Field(None, description="Subdirectory to analyze")
    include_patterns: Optional[List[str]] = Field(
        None, description="File patterns to include (e.g., ['*.java', '*.xml'])"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None, description="File patterns to exclude (e.g., ['**/test/**', '**/*.class'])"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "repository_url": "https://github.com/example/legacy-app.git",
                "branch": "main",
                "subdirectory": "src",
                "include_patterns": ["*.java", "*.xml"],
                "exclude_patterns": ["**/test/**", "**/*.class"],
            }
        }


class CodeSnippetUploadRequest(BaseModel):
    """Request schema for code snippet upload."""

    code: str = Field(..., description="Code snippet")
    language: Optional[LanguageEnum] = Field(None, description="Programming language")
    filename: Optional[str] = Field(None, description="Optional filename for context")
    description: Optional[str] = Field(None, description="Optional description")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "public class Main { public static void main(String[] args) { ... } }",
                "language": "java",
                "filename": "Main.java",
                "description": "Legacy main class",
            }
        }


class UploadedFile(BaseModel):
    """Schema for uploaded file information."""

    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Relative file path in uploaded structure")
    size_bytes: int = Field(..., description="File size in bytes")
    detected_language: Optional[LanguageEnum] = Field(None, description="Detected programming language")
    file_type: Optional[FileTypeEnum] = Field(None, description="Detected file type")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "f123e456-e89b-12d3-a456-426614174000",
                "filename": "Main.java",
                "file_path": "src/main/java/com/example/Main.java",
                "size_bytes": 1024,
                "detected_language": "java",
                "file_type": "source",
            }
        }


class UploadResponse(BaseModel):
    """Response schema for upload operations."""

    job_id: str = Field(..., description="Unique job identifier for tracking")
    upload_id: str = Field(..., description="Unique upload identifier")
    status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Status message")
    files: List[UploadedFile] = Field(..., description="List of uploaded files")
    total_files: int = Field(..., description="Total number of files uploaded")
    total_size_bytes: int = Field(..., description="Total size of all files in bytes")
    detected_languages: List[LanguageEnum] = Field(..., description="List of detected languages")
    primary_language: Optional[LanguageEnum] = Field(None, description="Primary/dominant language")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "j123e456-e89b-12d3-a456-426614174000",
                "upload_id": "u123e456-e89b-12d3-a456-426614174000",
                "status": "success",
                "message": "Successfully uploaded 5 files",
                "files": [
                    {
                        "file_id": "f123e456-e89b-12d3-a456-426614174000",
                        "filename": "Main.java",
                        "file_path": "src/main/java/com/example/Main.java",
                        "size_bytes": 1024,
                        "detected_language": "java",
                        "file_type": "source",
                    }
                ],
                "total_files": 5,
                "total_size_bytes": 5120,
                "detected_languages": ["java"],
                "primary_language": "java",
            }
        }


class UploadValidationError(BaseModel):
    """Schema for upload validation errors."""

    filename: str = Field(..., description="Filename that failed validation")
    error: str = Field(..., description="Validation error message")
    error_code: str = Field(..., description="Error code")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "malicious.exe",
                "error": "Unsupported file type",
                "error_code": "UNSUPPORTED_FILE_TYPE",
            }
        }

# Made with Bob
