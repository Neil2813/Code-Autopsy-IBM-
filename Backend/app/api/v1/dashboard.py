"""
Dashboard statistics API endpoints.

This module provides endpoints for:
- Dashboard statistics (analyses count, risk scores, lines analyzed, hours saved)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.schemas.common import JobStatusEnum
from app.storage.database import get_db_session
from app.storage.models import Job, File, Risk, JobStatusEnum as ModelJobStatusEnum

logger = logging.getLogger(__name__)

router = APIRouter()


def _calculate_risk_score(severity: str) -> float:
    """Convert risk severity to numeric score."""
    severity_scores = {
        "critical": 10.0,
        "high": 7.0,
        "medium": 5.0,
        "low": 3.0,
        "info": 1.0,
    }
    return severity_scores.get(severity.lower(), 0.0)


@router.get(
    "/dashboard/stats",
    summary="Get dashboard statistics",
    description="Get aggregated statistics for the dashboard (estimates based on persisted data)",
    responses={
        200: {"description": "Dashboard statistics retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
async def get_dashboard_stats(
    db: Session = Depends(get_db_session),
    days: int = 30
):
    """
    Get dashboard statistics including:
    - Number of analyses this month (from persisted jobs)
    - Average risk score across all completed jobs (estimated from persisted risks)
    - Total lines of code analyzed (from persisted file data)
    - Estimated hours saved (rough estimate: 4 hours per completed analysis)
    
    **Note**: All metrics are computed from fully persisted analysis data.
    The hours_saved metric is a rough estimate based on manual analysis time.
    
    Args:
        days: Number of days to look back for "this month" stats (default: 30)
    """
    logger.info("Received dashboard stats request")
    
    try:
        # Calculate date threshold for "this month"
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Count analyses this month (from persisted jobs)
        analyses_this_month = db.query(func.count(Job.id)).filter(
            Job.created_at >= date_threshold
        ).scalar() or 0
        
        # Get all completed jobs (only from persisted data)
        completed_jobs = db.query(Job).filter(
            Job.status == ModelJobStatusEnum.COMPLETED
        ).all()
        
        # Calculate average risk score (estimate from persisted risks)
        avg_risk_score = None
        if completed_jobs:
            total_risk_score = 0.0
            total_risks = 0
            
            for job in completed_jobs:
                # Get risks for this job from persisted data
                risks = db.query(Risk).filter(Risk.job_id == job.id).all()
                for risk in risks:
                    risk_level = str(risk.level) if risk.level is not None else "low"
                    total_risk_score += _calculate_risk_score(risk_level)
                    total_risks += 1
            
            if total_risks > 0:
                avg_risk_score = round(total_risk_score / total_risks, 2)
        
        # Calculate total lines analyzed (from persisted file data)
        lines_analyzed = None
        if completed_jobs:
            job_ids = [job.id for job in completed_jobs]
            total_lines = db.query(func.sum(File.lines_of_code)).filter(
                File.job_id.in_(job_ids),
                File.lines_of_code.isnot(None)
            ).scalar()
            
            if total_lines:
                lines_analyzed = int(total_lines)
        
        # Calculate hours saved (rough estimate: 4 hours per completed analysis)
        # This is an estimate assuming manual analysis would take ~4 hours per job
        hours_saved = len(completed_jobs) * 4 if completed_jobs else 0
        
        logger.info(
            f"Dashboard stats (from persisted data): {analyses_this_month} analyses, "
            f"avg risk: {avg_risk_score}, lines: {lines_analyzed}, "
            f"hours saved (estimate): {hours_saved}"
        )
        
        return {
            "analyses_this_month": analyses_this_month,
            "avg_risk_score": avg_risk_score,  # Estimate from persisted risks
            "lines_analyzed": lines_analyzed,  # From persisted file data
            "hours_saved": hours_saved,  # Rough estimate (4 hrs/job)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard stats: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to retrieve dashboard statistics",
                    "details": {"error": str(e)},
                }
            },
        )

# Made with Bob