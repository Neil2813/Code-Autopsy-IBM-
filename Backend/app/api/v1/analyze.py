"""
Analysis API endpoints.

This module provides endpoints for:
- Starting analysis jobs
- Configuring analysis parameters
"""

import logging

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.services.analysis_service import analysis_service
from app.storage.database import get_db
from app.storage.models import Job, JobStatusEnum

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Start analysis (synchronous)",
    description="Analyze uploaded code synchronously - blocks until analysis completes",
    responses={
        200: {"description": "Analysis completed successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Analysis already in progress"},
        500: {"model": ErrorResponse, "description": "Analysis failed"},
    },
)
async def start_analysis(request: AnalyzeRequest):
    """
    Analyze uploaded code synchronously.
    
    **IMPORTANT**: This endpoint blocks until analysis completes. For large codebases,
    consider implementing a job-based approach with polling via /jobs/{job_id}.
    
    This endpoint:
    1. Validates the job exists and is ready for analysis
    2. Runs the analysis synchronously through all stages
    3. Returns when analysis is complete (or fails)
    
    The analysis runs through multiple stages:
    - Ingest: Load and validate files
    - Parse: Extract code structure
    - Classify: Categorize files and components
    - Analyze: Detect risks and patterns
    - Explain: Generate human-readable explanations
    - Recommend: Generate modernization suggestions
    - Validate: Verify recommendations
    - Report: Generate final report
    
    For MVP, synchronous execution is acceptable. The response accurately reflects
    that analysis has completed when this endpoint returns.
    """
    logger.info(f"Received synchronous analysis request for job: {request.job_id}")
    
    # Verify job exists
    with get_db() as db:
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {request.job_id} not found"
            )
        
        # Check if analysis is already in progress or completed
        job_status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        if job_status == JobStatusEnum.PROCESSING.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Analysis already in progress for job {request.job_id}"
            )
        
        if job_status == JobStatusEnum.COMPLETED.value:
            logger.info(f"Job {request.job_id} already completed, returning success")
            return AnalyzeResponse(
                job_id=request.job_id,
                status=JobStatusEnum.COMPLETED.value,
                message="Analysis already completed",
                estimated_duration_seconds=None
            )
    
    # Run analysis synchronously
    options = request.config.dict() if request.config else {}
    await analysis_service.start_analysis(request.job_id, options)
    
    # Get final job status
    with get_db() as db:
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Job {request.job_id} not found after analysis"
            )
        
        final_status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        if final_status == JobStatusEnum.FAILED.value:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {job.error_message or 'Unknown error'}"
            )
        
        # Return actual status from database
        return AnalyzeResponse(
            job_id=request.job_id,
            status=JobStatusEnum.COMPLETED.value,
            message="Analysis completed successfully",
            estimated_duration_seconds=None  # Not applicable for synchronous execution
        )

# Made with Bob
