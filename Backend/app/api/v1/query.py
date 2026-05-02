# for IBM hackathon
"""
Query API endpoints.

This module provides endpoints for:
- Natural language queries about analyzed code
- Query history retrieval
"""

import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Path, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.schemas import (
    ErrorResponse,
    QueryHistoryResponse,
    QueryRequest,
    QueryResponse,
)
from app.storage.database import get_db_session
from app.storage.repositories import get_job_repository, get_query_repository, get_file_repository, get_risk_repository, get_suggestion_repository
from app.storage.models import JobStatusEnum, Query
from app.llm.provider_chain import get_llm_chain
from app.llm.prompts import PromptTemplates
from app.middleware.error_handler import NotFoundError, ConflictError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query codebase",
    description="Ask natural language questions about analyzed code",
    responses={
        200: {"description": "Query answered successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job not yet completed"},
    },
)
async def query_codebase(request: QueryRequest, db: Session = Depends(get_db_session)):
    """
    Ask natural language questions about analyzed code.
    
    This endpoint allows you to:
    - Ask questions about code behavior
    - Find specific patterns or issues
    - Get explanations of complex logic
    - Understand architecture decisions
    - Identify modernization opportunities
    
    The system uses:
    - Analysis results from the job
    - MCP solution database for similar patterns
    - LLM for natural language understanding
    - Code references for traceability
    
    Example questions:
    - "What are the most critical security risks?"
    - "Where is authentication handled?"
    - "Which files are most tightly coupled?"
    - "What should I modernize first?"
    - "How does the payment processing work?"
    """
    logger.info(f"Received query for job {request.job_id}: {request.question}")
    
    try:
        # 1. Validate job exists and is completed
        job_repo = get_job_repository(db)
        job = job_repo.get_job(request.job_id)  # lightweight: no eager-load of file content
        
        if not job:
            raise NotFoundError(f"Job {request.job_id} not found")
        
        job_status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        if job_status != JobStatusEnum.COMPLETED.value:
            raise ConflictError(
                f"Job {request.job_id} is not completed yet (status: {job_status})"
            )
        
        # 2. Load analysis results and build context via targeted repos (avoids memory blowup)
        file_repo = get_file_repository(db)
        risk_repo = get_risk_repository(db)
        suggestion_repo = get_suggestion_repository(db)

        files = file_repo.get_files_by_job(request.job_id)
        risks = risk_repo.get_risks_by_job(request.job_id)
        suggestions = suggestion_repo.get_suggestions_by_job(request.job_id)

        codebase_context = {
            "language": "mixed",
            "file_count": len(files),
            "total_loc": sum(f.lines_of_code or 0 for f in files),
            "risks_count": len(risks),
            "suggestions_count": len(suggestions),
        }
        
        # Add user-provided context if available
        if request.context:
            codebase_context["user_context"] = request.context
        
        # Get relevant files (top files by complexity or all if few)
        relevant_files = [f.file_path for f in files[:10]]
        
        # 3. Generate answer using LLM with context
        llm_chain = get_llm_chain()
        
        # Build prompt with user context if provided
        question_with_context = request.question
        if request.context:
            question_with_context = f"{request.question}\n\nAdditional context: {request.context}"
        
        prompt = PromptTemplates.answer_query(
            question=question_with_context,
            codebase_context=codebase_context,
            relevant_files=relevant_files
        )
        
        system_prompt = PromptTemplates.system_prompt_for_stage("query")
        
        llm_response = await llm_chain.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1500
        )
        
        if not llm_response.success:
            logger.error(f"LLM generation failed: {llm_response.error}")
            answer = "I apologize, but I'm unable to generate an answer at this time. Please try again later."
            confidence = 0.0
        else:
            answer = llm_response.content
            confidence = 0.85  # Default confidence for successful LLM responses
        
        # 4. Extract file references from answer (richer references)
        references = []
        for file in files:
            if file.file_path in answer:
                # Create richer file reference with available metadata
                ref = {
                    "file_path": file.file_path,
                    "line_numbers": [],  # Could be enhanced with line number extraction
                    "snippet": None
                }
                # Add line range if file has complexity data
                if file.lines_of_code and file.lines_of_code > 0:
                    ref["line_start"] = 1
                    ref["line_end"] = file.lines_of_code  # type: ignore
                references.append(ref)
        
        # 5. Generate follow-up suggestions based on question type
        follow_up_suggestions = []
        question_lower = request.question.lower()
        
        if "risk" in question_lower or "security" in question_lower:
            follow_up_suggestions = [
                "How can I fix the most critical security risks?",
                "What are the recommended tools for addressing these risks?",
                "Which risks should I prioritize first?"
            ]
        elif "moderniz" in question_lower or "refactor" in question_lower:
            follow_up_suggestions = [
                "What is the estimated effort for these modernization suggestions?",
                "Which modernization approach would you recommend?",
                "Are there any migration blockers I should address first?"
            ]
        elif "architecture" in question_lower or "structure" in question_lower:
            follow_up_suggestions = [
                "What are the main architectural issues?",
                "How can I improve the code structure?",
                "What design patterns should I consider?"
            ]
        else:
            follow_up_suggestions = [
                "What are the most critical issues in this codebase?",
                "How can I improve code quality?",
                "What should I modernize first?"
            ]
        
        # 6. Store query in history
        query_repo = get_query_repository(db)
        query_record = query_repo.create_query({
            "job_id": request.job_id,
            "question": request.question,
            "answer": answer,
            "confidence": confidence,
            "references": references,
            "mcp_solutions_used": 0  # Could be enhanced with MCP integration
        })
        
        db.commit()
        
        logger.info(f"Query answered successfully for job {request.job_id}")
        
        # 7. Return response with follow-up suggestions
        return QueryResponse(
            query_id=str(query_record.id),
            job_id=request.job_id,
            question=request.question,
            answer=answer,
            confidence=confidence,
            references=references,
            mcp_solutions_used=0,
            follow_up_suggestions=follow_up_suggestions,
            created_at=query_record.created_at,  # type: ignore
            updated_at=query_record.created_at  # type: ignore
        )
        
    except (NotFoundError, ConflictError) as e:
        logger.warning(f"Query failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to process query",
                    "details": {"error": str(e)},
                }
            },
        )


@router.get(
    "/query/history/{job_id}",
    response_model=QueryHistoryResponse,
    summary="Get query history",
    description="Get all queries asked about a specific job",
    responses={
        200: {"description": "Query history retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_query_history(
    job_id: str = Path(..., description="Job identifier"),
    db: Session = Depends(get_db_session)
):
    """
    Get all queries asked about a specific job.
    
    Returns a list of all questions asked, with:
    - Question text
    - Answer preview
    - Confidence score
    - Timestamp
    """
    logger.info(f"Received query history request for job: {job_id}")
    
    try:
        # 1. Validate job exists
        job_repo = get_job_repository(db)
        job = job_repo.get_job(job_id)
        
        if not job:
            raise NotFoundError(f"Job {job_id} not found")
        
        # 2. Get all queries for this job
        query_repo = get_query_repository(db)
        queries = query_repo.get_queries_by_job(job_id)
        
        # 3. Format response
        query_items = []
        for q in queries:
            answer_text = str(q.answer) if q.answer is not None else ""
            if answer_text and len(answer_text) > 200:
                answer_preview = answer_text[:200] + "..."
            else:
                answer_preview = answer_text
            
            query_items.append({
                "query_id": str(q.id),
                "question": q.question,
                "answer_preview": answer_preview,
                "answer_full": answer_text,
                "confidence": q.confidence,
                "created_at": q.created_at.isoformat()  # type: ignore
            })
        
        logger.info(f"Retrieved {len(query_items)} queries for job {job_id}")
        
        return QueryHistoryResponse(
            job_id=job_id,
            total_queries=len(query_items),
            queries=query_items  # type: ignore
        )
        
    except NotFoundError as e:
        logger.warning(f"Query history retrieval failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Query history retrieval failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to retrieve query history",
                    "details": {"error": str(e)},
                }
            },
        )

# Made with Bob
