# for IBM hackathon
"""
Upload API endpoints.

This module provides endpoints for:
- File uploads
- Repository uploads
- Code snippet uploads
"""

import logging
from typing import List

from fastapi import APIRouter, File, UploadFile, status, HTTPException

from app.schemas import (
    CodeSnippetUploadRequest,
    ErrorResponse,
    RepositoryUploadRequest,
    UploadResponse,
)
from app.services.upload_service import upload_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload/files",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload files",
    description="Upload one or more source files for analysis",
    responses={
        201: {"description": "Files uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file upload"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
)
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload source files for analysis.
    
    Accepts multiple files in various formats:
    - Source code files (.java, .cbl, .rpg, etc.)
    - Configuration files
    - Build files
    
    Returns a job ID for tracking the analysis.
    """
    logger.info(f"Received {len(files)} files for upload")
    
    try:
        response = await upload_service.upload_files(files)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload files: {str(e)}"
        )


@router.post(
    "/upload/repository",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload from repository",
    description="Clone and upload files from a Git repository",
    responses={
        201: {"description": "Repository cloned and uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid repository URL"},
        404: {"model": ErrorResponse, "description": "Repository not found"},
    },
)
async def upload_repository(request: RepositoryUploadRequest):
    """
    Clone a Git repository and upload its contents for analysis.
    
    Supports:
    - Public and private repositories (with authentication)
    - Branch selection
    - Subdirectory filtering
    - File pattern inclusion/exclusion
    
    Returns a job ID for tracking the analysis.
    """
    logger.info(f"Received repository upload request: {request.repository_url}")
    
    try:
        response = await upload_service.clone_repository(
            repository_url=str(request.repository_url),
            branch=request.branch,
            subdirectory=request.subdirectory,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone repository: {str(e)}"
        )


@router.post(
    "/upload/snippet",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload code snippet",
    description="Upload a code snippet for quick analysis",
    responses={
        201: {"description": "Snippet uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid code snippet"},
    },
)
async def upload_snippet(request: CodeSnippetUploadRequest):
    """
    Upload a code snippet for quick analysis.
    
    Useful for:
    - Quick code reviews
    - Testing specific code patterns
    - Analyzing small code sections
    
    Returns a job ID for tracking the analysis.
    """
    logger.info(f"Received code snippet upload: {len(request.code)} characters")
    
    try:
        response = await upload_service.process_snippet(
            code=request.code,
            language=request.language.value if request.language else None,
            filename=request.filename
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing snippet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process code snippet: {str(e)}"
        )

# Made with Bob
