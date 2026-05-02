# for IBM hackathon
"""
Job management API endpoints.

This module provides endpoints for:
- Job status tracking
- Job results retrieval
- Job cancellation
"""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Path, status, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.schemas import ErrorResponse, JobResultResponse, JobStatusResponse
from app.storage.database import get_db_session
from app.storage.repositories import (
    get_job_repository,
    get_risk_repository,
    get_suggestion_repository,
    get_analysis_result_repository,
)
from app.storage.models import JobStatusEnum
from app.middleware.error_handler import NotFoundError, ConflictError
from app.services.analysis_service import analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _priority_label(priority: int | None) -> str:
    if priority is None:
        return "medium"
    if priority >= 9:
        return "critical"
    if priority >= 7:
        return "high"
    if priority >= 5:
        return "medium"
    return "low"


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0, "unknown": 0}


def _max_severity(current: str, candidate: str) -> str:
    return candidate if SEVERITY_RANK.get(candidate, 0) > SEVERITY_RANK.get(current, 0) else current


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Get current status and progress of an analysis job",
    responses={
        200: {"description": "Job status retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_job_status(
    job_id: str = Path(..., description="Job identifier"),
    db: Session = Depends(get_db_session)
):
    """
    Get the current status and progress of an analysis job.
    
    Returns:
    - Overall job status (queued, processing, completed, failed, cancelled, partial_success)
    - Progress percentage
    - Current stage being executed
    - Progress of each stage
    - Estimated completion time
    - Error message if failed
    """
    logger.info(f"Received job status request for: {job_id}")
    
    try:
        # Query job from database
        job_repo = get_job_repository(db)
        job = job_repo.get_job(job_id)
        
        if not job:
            raise NotFoundError(f"Job {job_id} not found")
        
        # Calculate stage progress
        stages = []
        stage_names = ["upload", "parsing", "analysis", "risk_detection", "suggestions"]
        
        # Update stage progress based on job status (from persisted data)
        job_status_value = job.status.value if hasattr(job.status, 'value') else str(job.status)
        current_stage_value = str(job.current_stage) if job.current_stage is not None else None
        
        # Use the aligned enum values from storage model
        if job_status_value == "completed":
            for stage_name in stage_names:
                stages.append({
                    "stage_name": stage_name,
                    "status": "completed",
                    "progress_percent": 100.0,
                    "message": f"{stage_name.replace('_', ' ').title()} completed",
                    "started_at": job.created_at,  # type: ignore
                    "completed_at": job.updated_at  # type: ignore
                })
        elif job_status_value == JobStatusEnum.PROCESSING.value:
            # Estimate progress based on current stage
            for i, stage_name in enumerate(stage_names):
                if current_stage_value and stage_name == current_stage_value:
                    stages.append({
                        "stage_name": stage_name,
                        "status": "running",
                        "progress_percent": float(job.progress) if job.progress is not None else 50.0,  # type: ignore
                        "message": f"Processing {stage_name.replace('_', ' ')}",
                        "started_at": job.updated_at,  # type: ignore
                        "completed_at": None
                    })
                elif current_stage_value and stage_names.index(current_stage_value) > i:
                    stages.append({
                        "stage_name": stage_name,
                        "status": "completed",
                        "progress_percent": 100.0,
                        "message": f"{stage_name.replace('_', ' ').title()} completed",
                        "started_at": job.created_at,  # type: ignore
                        "completed_at": job.updated_at  # type: ignore
                    })
                else:
                    stages.append({
                        "stage_name": stage_name,
                        "status": "pending",
                        "progress_percent": 0.0,
                        "message": f"Waiting to start {stage_name.replace('_', ' ')}",
                        "started_at": None,
                        "completed_at": None
                    })
        else:
            for stage_name in stage_names:
                stages.append({
                    "stage_name": stage_name,
                    "status": "pending",
                    "progress_percent": 0.0,
                    "message": "Not started",
                    "started_at": None,
                    "completed_at": None
                })
        
        # Calculate overall progress (from persisted data)
        if job_status_value == "completed":
            overall_progress = 100.0
        elif job_status_value == "failed":
            overall_progress = float(job.progress) if job.progress is not None else 0.0  # type: ignore
        else:
            overall_progress = float(job.progress) if job.progress is not None else 0.0  # type: ignore
        
        # Determine status message (based on persisted status)
        if job_status_value == "completed":
            message = "Analysis completed successfully"
        elif job_status_value == "failed":
            error_msg = str(job.error_message) if job.error_message is not None else 'Unknown error'
            message = f"Analysis failed: {error_msg}"
        elif job_status_value == "processing":
            message = f"Processing {current_stage_value or 'analysis'}..."
        else:
            message = f"Job is {job_status_value}"
        
        logger.info(f"Job {job_id} status: {job_status_value}, progress: {overall_progress}%")
        
        # Convert status string to enum
        from app.schemas.common import JobStatusEnum as SchemaJobStatusEnum
        status_enum = SchemaJobStatusEnum(job_status_value)
        
        return JobStatusResponse(
            job_id=job_id,
            status=status_enum,
            progress_percent=overall_progress,
            message=message,
            stages=stages,
            current_stage=current_stage_value,
            estimated_completion=None,
            error_message=str(job.error_message) if job.error_message is not None else None,
            created_at=job.created_at,  # type: ignore
            updated_at=job.updated_at  # type: ignore
        )
        
    except NotFoundError as e:
        logger.warning(f"Job status retrieval failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Job status retrieval failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to retrieve job status",
                    "details": {"error": str(e)},
                }
            },
        )


@router.get(
    "/jobs/{job_id}/results",
    response_model=JobResultResponse,
    summary="Get job results",
    description="Get complete analysis results for a completed job",
    responses={
        200: {"description": "Job results retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job not yet completed"},
    },
)
async def get_job_results(
    job_id: str = Path(..., description="Job identifier"),
    db: Session = Depends(get_db_session)
):
    """
    Get complete analysis results for a completed job.
    
    Returns:
    - Summary of analysis
    - Architecture overview
    - Detected risks with severity levels
    - Modernization suggestions with priorities
    - Migration blockers
    - Recommended next steps
    - Dependency graph
    - File inventory
    """
    logger.info(f"Received job results request for: {job_id}")
    
    try:
        # Query job from database
        job_repo = get_job_repository(db)
        job = job_repo.get_job(job_id)
        
        if not job:
            raise NotFoundError(f"Job {job_id} not found")
        
        # Verify job is completed (from persisted data)
        job_status_value = job.status.value if hasattr(job.status, 'value') else str(job.status)
        if job_status_value != "completed":
            raise ConflictError(
                f"Job {job_id} is not completed yet (status: {job_status_value})"
            )
        
        # Load risks (from persisted data only)
        risk_repo = get_risk_repository(db)
        risks = risk_repo.get_risks_by_job(job_id)
        
        # Load suggestions (from persisted data only)
        suggestion_repo = get_suggestion_repository(db)
        suggestions = suggestion_repo.get_suggestions_by_job(job_id)
        
        # Load analysis results (from persisted data only)
        result_repo = get_analysis_result_repository(db)
        analysis_result = result_repo.get_result_by_job(job_id)
        
        file_inventory = []
        if analysis_result is not None and analysis_result.content is not None:
            file_inventory = analysis_result.content.get("file_inventory", []) or []

        total_files = len(file_inventory)
        total_lines_of_code = sum(
            int(file_item.get("lines_of_code") or 0)
            for file_item in file_inventory
            if isinstance(file_item, dict)
        )
        languages = sorted({
            str(file_item.get("language") or "unknown")
            for file_item in file_inventory
            if isinstance(file_item, dict)
        })

        summary_text = (
            f"Analyzed {total_files} files with {total_lines_of_code} "
            f"lines of code. Found {len(risks)} risks and {len(suggestions)} modernization suggestions."
        )
        
        # Count critical risks safely
        critical_count = 0
        for r in risks:
            risk_level = str(r.level) if r.level is not None else ""
            if risk_level == "critical":
                critical_count += 1
        
        # Count high priority suggestions safely (from persisted data)
        high_priority_count = 0
        for s in suggestions:
            # Access the actual value, not the Column object
            priority_val = s.priority if s.priority is not None else 0  # type: ignore
            if priority_val >= 8:  # type: ignore
                high_priority_count += 1
        
        # Format risks (from persisted data)
        risks_data = []
        for r in risks:
            # Extract line info from the line_numbers JSON column
            line_nums = r.line_numbers or {}
            line_start = None
            line_end = None
            code_snippet = None
            if isinstance(line_nums, dict):
                line_start = line_nums.get("line_start") or line_nums.get("start")
                line_end = line_nums.get("line_end") or line_nums.get("end")
                code_snippet = line_nums.get("code_snippet") or line_nums.get("snippet")
            elif isinstance(line_nums, list) and line_nums:
                line_start = line_nums[0] if isinstance(line_nums[0], int) else None

            affected_files = r.affected_files or []
            if isinstance(affected_files, list) and affected_files:
                first_ref = affected_files[0]
                if isinstance(first_ref, dict):
                    line_start = line_start or first_ref.get("line_start") or first_ref.get("line")
                    line_end = line_end or first_ref.get("line_end") or line_start
                    code_snippet = code_snippet or first_ref.get("snippet") or first_ref.get("code_snippet")

            risks_data.append({
                "risk_id": r.risk_id,
                "title": r.title,
                "description": r.description or "",
                "severity": str(r.level) if r.level is not None else "unknown",
                "category": r.category or "general",
                "affected_files": affected_files,
                "recommendation": r.recommendation or "",
                "line_start": line_start,
                "line_end": line_end,
                "code_snippet": code_snippet,
                "mcp_solution_available": bool(r.mcp_solution_available),
                "confidence": float(r.confidence) if r.confidence is not None else 0.0,  # type: ignore
            })

        # Some earlier runs stored the analyzer output only inside analysis_results
        # after a risk table insert failed. Keep the UI truthful for those jobs.
        if not risks_data and analysis_result is not None and analysis_result.content is not None:
            fallback_risks = analysis_result.content.get("code_smells", []) or []
            for index, risk in enumerate(fallback_risks):
                if not isinstance(risk, dict):
                    continue

                affected_files = risk.get("affected_files") or []
                line_start = None
                line_end = None
                code_snippet = None
                if isinstance(affected_files, list) and affected_files:
                    first_ref = affected_files[0]
                    if isinstance(first_ref, dict):
                        line_start = first_ref.get("line_start") or first_ref.get("line")
                        line_end = first_ref.get("line_end") or line_start
                        code_snippet = first_ref.get("snippet") or first_ref.get("code_snippet")

                risks_data.append({
                    "risk_id": str(risk.get("risk_id") or f"analysis_{job_id}_{index}"),
                    "title": risk.get("title") or "Untitled Risk",
                    "description": risk.get("description") or "",
                    "severity": str(risk.get("severity") or risk.get("level") or "unknown").lower(),
                    "category": risk.get("category") or "general",
                    "affected_files": affected_files,
                    "recommendation": risk.get("recommendation") or "",
                    "line_start": line_start,
                    "line_end": line_end,
                    "code_snippet": code_snippet,
                    "mcp_solution_available": bool(risk.get("mcp_solution_available", False)),
                    "confidence": float(risk.get("confidence") or 0.0),
                })
        
        # Format suggestions (from persisted data)
        suggestions_data = []
        for s in suggestions:
            # Extract values from persisted data - use type: ignore for SQLAlchemy column access
            priority_val: int | None = s.priority if s.priority is not None else None  # type: ignore
            desc_val: str = s.description if s.description is not None else ""  # type: ignore
            
            suggestions_data.append({
                "suggestion_id": s.suggestion_id,
                "title": s.title,
                "description": desc_val,
                "priority": _priority_label(priority_val),
                "category": str(s.type) if s.type is not None else "general",
                "affected_files": s.affected_files or [],
                "implementation_guide": s.rationale or "",
                "estimated_effort": s.effort_estimate or "medium",
                "code_snippet": s.before_snippet or None,
                "fix_snippet": s.after_snippet or None,
                "benefits": [desc_val] if desc_val else [],
                "risks": [],
                "mcp_solution_available": bool(s.mcp_based),
                "confidence": float(s.confidence) if s.confidence is not None else 0.0,  # type: ignore
            })

        file_risk: Dict[str, str] = {}
        for risk in risks_data:
            severity = str(risk.get("severity") or "unknown").lower()
            for ref in risk.get("affected_files") or []:
                if isinstance(ref, dict) and ref.get("file_path"):
                    path = str(ref["file_path"])
                    file_risk[path] = _max_severity(file_risk.get(path, "unknown"), severity)

        priority_order = [
            str(risk.get("title"))
            for risk in sorted(
                risks_data,
                key=lambda item: (
                    -SEVERITY_RANK.get(str(item.get("severity") or "unknown").lower(), 0),
                    (item.get("line_start") or 0),
                ),
            )
            if risk.get("title")
        ][:10]
        
        # Build architecture summary
        architecture = {
            "project_type": "legacy",
            "primary_language": languages[0] if languages else "unknown",
            "detected_frameworks": [],
            "architecture_patterns": [],
            "layers": {},
            "entry_points": [],
            "dependency_graph": {"nodes": [], "edges": []}
        }
        
        if analysis_result is not None and analysis_result.content is not None:
            summary_text = str(analysis_result.content.get("summary") or summary_text)
            arch_data = analysis_result.content.get("architecture", {})
            if isinstance(arch_data, dict):
                architecture.update(arch_data)
        
        # Migration blockers
        migration_blockers = [
            str(r.title) for r in risks if r.level is not None and str(r.level) in {"critical", "high"}
        ][:5]

        if analysis_result is not None and analysis_result.content is not None:
            migration_blockers = analysis_result.content.get("migration_blockers", migration_blockers) or migration_blockers

        # Recommended next steps
        recommended_next_steps = [
            f"Address {critical_count} critical security risks",
            f"Review {high_priority_count} high-priority modernization suggestions",
                "Update dependencies to latest stable versions",
                "Implement automated testing",
                "Set up CI/CD pipeline"
        ]
        if analysis_result is not None and analysis_result.content is not None:
            recommended_next_steps = analysis_result.content.get("recommended_next_steps", recommended_next_steps) or recommended_next_steps
        
        logger.info(f"Retrieved results for job {job_id}: {len(risks)} risks, {len(suggestions)} suggestions")
        
        # Convert status string to enum
        from app.schemas.common import JobStatusEnum as SchemaJobStatusEnum
        status_enum = SchemaJobStatusEnum(job_status_value)
        
        # Convert architecture dict to ArchitectureSummary
        from app.schemas.job import ArchitectureSummary
        arch_summary = ArchitectureSummary(**architecture)
        
        return JobResultResponse(
            job_id=job_id,
            status=status_enum,
            summary=summary_text,
            architecture=arch_summary,
            risks=risks_data,
            suggestions=suggestions_data,
            migration_blockers=migration_blockers,
            recommended_next_steps=recommended_next_steps,
            metadata={
                "total_files": total_files,
                "total_lines_of_code": total_lines_of_code,
                "languages": languages,
                "file_inventory": file_inventory,
                "priority_order": priority_order,
                "file_risk": file_risk,
            },
            created_at=job.created_at,  # type: ignore
            updated_at=job.updated_at  # type: ignore
        )
        
    except (NotFoundError, ConflictError) as e:
        logger.warning(f"Job results retrieval failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Job results retrieval failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to retrieve job results",
                    "details": {"error": str(e)},
                }
            },
        )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel job",
    description="Cancel a running analysis job",
    responses={
        204: {"description": "Job cancelled successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job cannot be cancelled"},
    },
)
async def cancel_job(
    job_id: str = Path(..., description="Job identifier"),
    db: Session = Depends(get_db_session)
):
    """
    Cancel a running analysis job.
    
    Only jobs in 'queued' or 'processing' status can be cancelled.
    Completed or failed jobs cannot be cancelled.
    """
    logger.info(f"Received job cancellation request for: {job_id}")
    
    try:
        # Query job from database
        job_repo = get_job_repository(db)
        job = job_repo.get_job(job_id)
        
        if not job:
            raise NotFoundError(f"Job {job_id} not found")
        
        # Verify job can be cancelled
        cancellable_statuses = [JobStatusEnum.QUEUED, JobStatusEnum.PROCESSING]
        if job.status not in cancellable_statuses:
            raise ConflictError(
                f"Job {job_id} cannot be cancelled (status: {job.status.value})"
            )
        
        # Cancel the job
        success = await analysis_service.cancel_analysis(job_id)
        
        if not success:
            raise ConflictError(f"Failed to cancel job {job_id}")
        
        logger.info(f"Job {job_id} cancelled successfully")
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except (NotFoundError, ConflictError) as e:
        logger.warning(f"Job cancellation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Job cancellation failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to cancel job",
                    "details": {"error": str(e)},
                }
            },
        )

# Made with Bob
