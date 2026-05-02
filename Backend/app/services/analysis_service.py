"""
Analysis service to orchestrate LangGraph agent execution.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.agents.modernization_agent import get_agent
from app.agents.agent_state import FileInfo, RiskItem, SuggestionItem
from app.storage.database import get_db
from app.storage.models import Job, File, JobStatusEnum, AnalysisResult, Risk, Suggestion
from app.storage.repositories import (
    get_risk_repository,
    get_suggestion_repository,
    get_job_repository
)

logger = logging.getLogger(__name__)


def _read_file_content(file_path: str) -> str:
    """Best-effort file reader for analysis."""
    try:
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        logger.warning("Could not read file content for analysis: %s", file_path)
        return ""


def _json_safe_dependency_graph(graph: Any) -> Dict[str, Any]:
    """Convert dependency graph objects or dicts into plain JSON-safe structures."""
    if graph is None:
        return {"nodes": [], "edges": []}

    if isinstance(graph, dict):
        return {
            "nodes": list(graph.get("nodes", [])),
            "edges": list(graph.get("edges", [])),
        }

    def to_plain(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        return vars(value)

    nodes = getattr(graph, "nodes", []) or []
    edges = getattr(graph, "edges", []) or []
    return {
        "nodes": [to_plain(node) for node in nodes],
        "edges": [to_plain(edge) for edge in edges],
    }


def _persist_risks(db, job_id: str, risks: List[RiskItem]) -> int:
    """
    Persist risk items to database.
    
    Args:
        db: Database session
        job_id: Job identifier
        risks: List of risk items from agent
        
    Returns:
        Number of risks persisted
    """
    if not risks:
        return 0
    
    risk_repo = get_risk_repository(db)
    persisted_count = 0
    
    for index, risk_item in enumerate(risks):
        try:
            affected_files = risk_item.get("affected_files", [])
            line_numbers = risk_item.get("line_numbers")
            if not line_numbers and isinstance(affected_files, list) and affected_files:
                first_ref = affected_files[0]
                if isinstance(first_ref, dict) and first_ref.get("line_start") is not None:
                    line_numbers = [first_ref.get("line_start")]

            severity = risk_item.get("severity") or risk_item.get("level") or "medium"
            risk_data = {
                "job_id": job_id,
                "risk_id": f"risk_{job_id[:8]}_{index}_{uuid.uuid4().hex[:10]}",
                "title": risk_item.get("title", "Untitled Risk"),
                "description": risk_item.get("description", ""),
                "category": risk_item.get("category", "general"),
                "level": str(severity).lower(),
                "affected_files": affected_files,
                "line_numbers": line_numbers,
                "recommendation": risk_item.get("recommendation", ""),
                "confidence": risk_item.get("confidence", 0.5),
                "mcp_solution_available": risk_item.get("mcp_solution_available", False)
            }
            risk_repo.create_risk(risk_data)
            persisted_count += 1
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist risk {risk_item.get('risk_id')}: {e}")
    
    logger.info(f"Persisted {persisted_count} risks for job {job_id}")
    return persisted_count


def _persist_suggestions(db, job_id: str, suggestions: List[SuggestionItem]) -> int:
    """
    Persist suggestion items to database.
    
    Args:
        db: Database session
        job_id: Job identifier
        suggestions: List of suggestion items from agent
        
    Returns:
        Number of suggestions persisted
    """
    if not suggestions:
        return 0
    
    suggestion_repo = get_suggestion_repository(db)
    persisted_count = 0
    
    for index, suggestion_item in enumerate(suggestions):
        try:
            # Map priority string to integer
            priority_map = {"critical": 10, "high": 8, "medium": 5, "low": 3}
            priority_value = suggestion_item.get("priority", "medium")
            # Handle both string and integer priority values
            if isinstance(priority_value, int):
                priority_int = priority_value
            else:
                priority_int = priority_map.get(str(priority_value).lower(), 5)
            
            suggestion_data = {
                "job_id": job_id,
                "suggestion_id": f"sugg_{job_id[:8]}_{index}_{uuid.uuid4().hex[:10]}",
                "type": suggestion_item.get("category", "modernization"),
                "title": suggestion_item.get("title", "Untitled Suggestion"),
                "description": suggestion_item.get("description", ""),
                "rationale": suggestion_item.get("implementation_guide", ""),
                "priority": priority_int,
                "effort_estimate": suggestion_item.get("estimated_effort", "medium"),
                "affected_files": suggestion_item.get("affected_files", []),
                "before_snippet": None,  # Can be enhanced if agent provides code snippets
                "after_snippet": None,
                "confidence": suggestion_item.get("confidence", 0.5),
                "mcp_based": suggestion_item.get("mcp_solution_available", False)
            }
            suggestion_repo.create_suggestion(suggestion_data)
            persisted_count += 1
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist suggestion {suggestion_item.get('suggestion_id')}: {e}")
    
    logger.info(f"Persisted {persisted_count} suggestions for job {job_id}")
    return persisted_count


class AnalysisService:
    """Service for code analysis orchestration with enhanced persistence."""
    
    async def start_analysis(
        self,
        job_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Start analysis for a job with full persistence of risks and suggestions.
        
        Args:
            job_id: Job identifier
            options: Analysis options dictionary
        """
        logger.info(f"Starting analysis for job {job_id}")
        
        try:
            # Get job from database
            with get_db() as db:
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job:
                    raise ValueError(f"Job {job_id} not found")
                
                # Update status
                job.status = JobStatusEnum.PROCESSING  # type: ignore
                db.commit()
                
                # Load files
                files = db.query(File).filter(File.job_id == job_id).all()
                if not files:
                    raise ValueError(f"No files found for job {job_id}")
                
                # Convert to FileInfo objects
                file_infos = []
                for f in files:
                    file_path = str(f.file_path)  # type: ignore
                    content = _read_file_content(file_path)
                    file_infos.append(
                        FileInfo(
                            file_id=str(f.id),
                            file_path=file_path,
                            language=str(f.language or "unknown"),  # type: ignore
                            file_type=str(f.file_type or "source"),
                            content=content,
                            size_bytes=int(f.size_bytes or 0),  # type: ignore
                            lines_of_code=int(f.lines_of_code or (content.count("\n") + 1 if content else 0)),  # type: ignore
                            complexity_score=float(f.complexity_score) if f.complexity_score is not None else None,  # type: ignore
                        )
                    )
            
            # Get agent
            agent = get_agent()
            
            # Execute agent with proper method signature
            logger.info(f"Executing LangGraph agent for job {job_id}")
            result = await agent.analyze(
                job_id=job_id,
                uploaded_files=file_infos,
                analysis_config=options or {}
            )
            
            # Store results with enhanced persistence
            with get_db() as db:
                job_repo = get_job_repository(db)
                job = job_repo.get_job(job_id)
                if not job:
                    logger.error(f"Job {job_id} not found after analysis")
                    return
                
                if result.get("errors") or result.get("status") == "failed" or result.get("error_message"):
                    job.status = JobStatusEnum.FAILED  # type: ignore
                    errors = result.get("errors") or [result.get("error_message") or "Analysis failed"]
                    job.error_message = "; ".join(str(error) for error in errors)  # type: ignore
                    logger.error(f"Analysis failed for job {job_id}: {job.error_message}")
                else:
                    # Update job progress and stage from agent result
                    job.status = JobStatusEnum.COMPLETED  # type: ignore
                    job.progress = float(result.get("progress_percent", 100.0))  # type: ignore
                    job.current_stage = str(result.get("current_stage", "completed"))  # type: ignore
                    
                    risk_items = result.get("risks", []) or result.get("code_smells", [])
                    suggestion_items = result.get("suggestions", [])
                    risks_count = _persist_risks(db, job_id, risk_items)
                    suggestions_count = _persist_suggestions(db, job_id, suggestion_items)
                    
                    # Store main analysis results
                    analysis_result = AnalysisResult(
                        job_id=job_id,
                        result_type="complete_analysis",
                        content={
                            "summary": result.get("summary", ""),
                            "architecture": {
                                "project_type": result.get("project_type", "legacy"),
                                "primary_language": result.get("primary_language", "unknown"),
                                "detected_frameworks": result.get("detected_frameworks", []),
                                "architecture_patterns": result.get("architecture_patterns", []),
                                "layers": result.get("layers", {}),
                                "entry_points": [
                                    {"file_path": path}
                                    for path in result.get("entry_points", [])
                                ],
                                "dependency_graph": _json_safe_dependency_graph(result.get("dependency_graph")),
                            },
                            "file_inventory": [
                                {
                                    "file_path": file_info["file_path"],
                                    "language": file_info["language"],
                                    "lines_of_code": file_info["lines_of_code"],
                                    "file_type": file_info["file_type"],
                                }
                                for file_info in file_infos
                            ],
                            "migration_blockers": result.get("migration_blockers", []),
                            "recommended_next_steps": result.get("recommended_next_steps", []),
                            "code_smells": result.get("code_smells", []),
                            "complexity_metrics": result.get("complexity_metrics", {}),
                            "risks_count": risks_count,
                            "suggestions_count": suggestions_count,
                            "mcp_solutions_used": result.get("mcp_solutions_used", 0)
                        },
                    )
                    db.add(analysis_result)
                    
                    logger.info(
                        f"Analysis completed for job {job_id}: "
                        f"{risks_count} risks, {suggestions_count} suggestions persisted"
                    )
                
                db.commit()
        
        except Exception as e:
            logger.error(f"Analysis failed for job {job_id}: {e}", exc_info=True)
            
            # Update job status
            try:
                with get_db() as db:
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if job:
                        job.status = JobStatusEnum.FAILED  # type: ignore
                        job.error_message = str(e)  # type: ignore
                        db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update job status: {db_error}")
    
    async def get_analysis_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis results for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Analysis results dictionary or None if not found
        """
        with get_db() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return None
            
            # Check status using value comparison
            if job.status.value != JobStatusEnum.COMPLETED.value:  # type: ignore
                return None
            
            # Get analysis results
            result = db.query(AnalysisResult).filter(
                AnalysisResult.job_id == job_id,
                AnalysisResult.result_type == "complete_analysis"
            ).first()
            
            if not result:
                return None
            
            # Access content attribute properly
            return dict(result.content) if result.content else None  # type: ignore
    
    async def cancel_analysis(self, job_id: str) -> bool:
        """
        Cancel a running analysis.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled, False otherwise
        """
        with get_db() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return False
            
            # Check if job is in cancellable state
            if job.status in [JobStatusEnum.QUEUED, JobStatusEnum.PROCESSING]:  # type: ignore
                job.status = JobStatusEnum.CANCELLED  # type: ignore
                db.commit()
                logger.info(f"Cancelled analysis for job {job_id}")
                return True
            
            return False


# Singleton instance
analysis_service = AnalysisService()

# Made with Bob
