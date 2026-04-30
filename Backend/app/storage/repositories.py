"""
Repository Pattern for Database Access

This module provides repository classes for database operations,
abstracting SQLAlchemy queries and providing a clean interface
for data access.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc

from app.storage.models import (
    Job, File, AnalysisResult, Risk, Suggestion, Query
)
from app.schemas.common import JobStatusEnum, SeverityEnum, LanguageEnum
from app.middleware.error_handler import NotFoundError, ConflictError

logger = logging.getLogger(__name__)


class JobRepository:
    """Repository for Job operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_job(self, job_data: Dict[str, Any]) -> Job:
        """Create a new job."""
        job = Job(**job_data)
        self.db.add(job)
        self.db.flush()
        logger.info(f"Created job {job.id}")
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def get_job_or_raise(self, job_id: str) -> Job:
        """Get job by ID or raise NotFoundError."""
        job = self.get_job(job_id)
        if not job:
            raise NotFoundError(f"Job {job_id} not found")
        return job
    
    def get_job_with_files(self, job_id: str) -> Optional[Job]:
        """Get job with files loaded."""
        return self.db.query(Job).options(
            joinedload(Job.files)
        ).filter(Job.id == job_id).first()
    
    def get_job_with_results(self, job_id: str) -> Optional[Job]:
        """Get job with all related data loaded."""
        return self.db.query(Job).options(
            joinedload(Job.files),
            joinedload(Job.analysis_results),
            joinedload(Job.risks),
            joinedload(Job.suggestions),
            joinedload(Job.queries)
        ).filter(Job.id == job_id).first()
    
    def update_job_status(
        self, 
        job_id: str, 
        status: JobStatusEnum,
        error_message: Optional[str] = None
    ) -> Job:
        """Update job status."""
        job = self.get_job_or_raise(job_id)
        job.status = status
        if error_message:
            job.error_message = error_message
        job.updated_at = datetime.utcnow()
        self.db.flush()
        logger.info(f"Updated job {job_id} status to {status}")
        return job
    
    def update_job_progress(
        self,
        job_id: str,
        progress_percent: float,
        current_stage: Optional[str] = None
    ) -> Job:
        """Update job progress."""
        job = self.get_job_or_raise(job_id)
        job.progress_percent = progress_percent
        if current_stage:
            job.current_stage = current_stage
        job.updated_at = datetime.utcnow()
        self.db.flush()
        return job
    
    def update_job_metadata(
        self,
        job_id: str,
        metadata: Dict[str, Any]
    ) -> Job:
        """Update job metadata."""
        job = self.get_job_or_raise(job_id)
        if job.metadata:
            job.metadata.update(metadata)
        else:
            job.metadata = metadata
        job.updated_at = datetime.utcnow()
        self.db.flush()
        return job
    
    def list_jobs(
        self,
        status: Optional[JobStatusEnum] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Job]:
        """List jobs with optional filtering."""
        query = self.db.query(Job)
        if status:
            query = query.filter(Job.status == status)
        return query.order_by(desc(Job.created_at)).limit(limit).offset(offset).all()
    
    def delete_job(self, job_id: str) -> None:
        """Delete a job and all related data."""
        job = self.get_job_or_raise(job_id)
        self.db.delete(job)
        self.db.flush()
        logger.info(f"Deleted job {job_id}")


class FileRepository:
    """Repository for File operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_file(self, file_data: Dict[str, Any]) -> File:
        """Create a new file record."""
        file = File(**file_data)
        self.db.add(file)
        self.db.flush()
        return file
    
    def create_files(self, files_data: List[Dict[str, Any]]) -> List[File]:
        """Create multiple file records."""
        files = [File(**data) for data in files_data]
        self.db.add_all(files)
        self.db.flush()
        logger.info(f"Created {len(files)} file records")
        return files
    
    def get_file(self, file_id: str) -> Optional[File]:
        """Get file by ID."""
        return self.db.query(File).filter(File.id == file_id).first()
    
    def get_files_by_job(self, job_id: str) -> List[File]:
        """Get all files for a job."""
        return self.db.query(File).filter(File.job_id == job_id).all()
    
    def get_files_by_language(
        self,
        job_id: str,
        language: LanguageEnum
    ) -> List[File]:
        """Get files by language for a job."""
        return self.db.query(File).filter(
            and_(File.job_id == job_id, File.language == language)
        ).all()
    
    def update_file_analysis(
        self,
        file_id: str,
        parsed_content: Optional[Dict[str, Any]] = None,
        complexity_score: Optional[float] = None,
        lines_of_code: Optional[int] = None
    ) -> File:
        """Update file analysis data."""
        file = self.db.query(File).filter(File.id == file_id).first()
        if not file:
            raise NotFoundError(f"File {file_id} not found")
        
        if parsed_content is not None:
            file.parsed_content = parsed_content
        if complexity_score is not None:
            file.complexity_score = complexity_score
        if lines_of_code is not None:
            file.lines_of_code = lines_of_code
        
        file.updated_at = datetime.utcnow()
        self.db.flush()
        return file


class AnalysisResultRepository:
    """Repository for AnalysisResult operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_result(self, result_data: Dict[str, Any]) -> AnalysisResult:
        """Create a new analysis result."""
        result = AnalysisResult(**result_data)
        self.db.add(result)
        self.db.flush()
        logger.info(f"Created analysis result for job {result.job_id}")
        return result
    
    def get_result_by_job(self, job_id: str) -> Optional[AnalysisResult]:
        """Get analysis result for a job."""
        return self.db.query(AnalysisResult).filter(
            AnalysisResult.job_id == job_id
        ).first()
    
    def update_result(
        self,
        job_id: str,
        updates: Dict[str, Any]
    ) -> AnalysisResult:
        """Update analysis result."""
        result = self.get_result_by_job(job_id)
        if not result:
            raise NotFoundError(f"Analysis result for job {job_id} not found")
        
        for key, value in updates.items():
            if hasattr(result, key):
                setattr(result, key, value)
        
        result.updated_at = datetime.utcnow()
        self.db.flush()
        return result


class RiskRepository:
    """Repository for Risk operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_risk(self, risk_data: Dict[str, Any]) -> Risk:
        """Create a new risk."""
        risk = Risk(**risk_data)
        self.db.add(risk)
        self.db.flush()
        return risk
    
    def create_risks(self, risks_data: List[Dict[str, Any]]) -> List[Risk]:
        """Create multiple risks."""
        risks = [Risk(**data) for data in risks_data]
        self.db.add_all(risks)
        self.db.flush()
        logger.info(f"Created {len(risks)} risk records")
        return risks
    
    def get_risks_by_job(
        self,
        job_id: str,
        severity: Optional[SeverityEnum] = None
    ) -> List[Risk]:
        """Get risks for a job, optionally filtered by severity."""
        query = self.db.query(Risk).filter(Risk.job_id == job_id)
        if severity:
            query = query.filter(Risk.severity == severity)
        return query.order_by(desc(Risk.severity)).all()
    
    def get_critical_risks(self, job_id: str) -> List[Risk]:
        """Get critical and high severity risks."""
        return self.db.query(Risk).filter(
            and_(
                Risk.job_id == job_id,
                or_(
                    Risk.severity == SeverityEnum.CRITICAL,
                    Risk.severity == SeverityEnum.HIGH
                )
            )
        ).all()


class SuggestionRepository:
    """Repository for Suggestion operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_suggestion(self, suggestion_data: Dict[str, Any]) -> Suggestion:
        """Create a new suggestion."""
        suggestion = Suggestion(**suggestion_data)
        self.db.add(suggestion)
        self.db.flush()
        return suggestion
    
    def create_suggestions(
        self,
        suggestions_data: List[Dict[str, Any]]
    ) -> List[Suggestion]:
        """Create multiple suggestions."""
        suggestions = [Suggestion(**data) for data in suggestions_data]
        self.db.add_all(suggestions)
        self.db.flush()
        logger.info(f"Created {len(suggestions)} suggestion records")
        return suggestions
    
    def get_suggestions_by_job(self, job_id: str) -> List[Suggestion]:
        """Get all suggestions for a job."""
        return self.db.query(Suggestion).filter(
            Suggestion.job_id == job_id
        ).order_by(desc(Suggestion.priority)).all()
    
    def get_high_priority_suggestions(self, job_id: str) -> List[Suggestion]:
        """Get high priority suggestions."""
        return self.db.query(Suggestion).filter(
            and_(
                Suggestion.job_id == job_id,
                Suggestion.priority >= 8
            )
        ).all()


class QueryRepository:
    """Repository for Query operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_query(self, query_data: Dict[str, Any]) -> Query:
        """Create a new query record."""
        query = Query(**query_data)
        self.db.add(query)
        self.db.flush()
        logger.info(f"Created query for job {query.job_id}")
        return query
    
    def get_queries_by_job(self, job_id: str) -> List[Query]:
        """Get all queries for a job."""
        return self.db.query(Query).filter(
            Query.job_id == job_id
        ).order_by(desc(Query.created_at)).all()
    
    def get_query(self, query_id: str) -> Optional[Query]:
        """Get query by ID."""
        return self.db.query(Query).filter(Query.id == query_id).first()


# Factory functions for dependency injection
def get_job_repository(db: Session) -> JobRepository:
    """Get JobRepository instance."""
    return JobRepository(db)


def get_file_repository(db: Session) -> FileRepository:
    """Get FileRepository instance."""
    return FileRepository(db)


def get_analysis_result_repository(db: Session) -> AnalysisResultRepository:
    """Get AnalysisResultRepository instance."""
    return AnalysisResultRepository(db)


def get_risk_repository(db: Session) -> RiskRepository:
    """Get RiskRepository instance."""
    return RiskRepository(db)


def get_suggestion_repository(db: Session) -> SuggestionRepository:
    """Get SuggestionRepository instance."""
    return SuggestionRepository(db)


def get_query_repository(db: Session) -> QueryRepository:
    """Get QueryRepository instance."""
    return QueryRepository(db)

# Made with Bob
