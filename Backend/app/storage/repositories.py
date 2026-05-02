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
from app.schemas.common import JobStatusEnum, SeverityEnum, LanguageEnum, PriorityEnum
from app.middleware.error_handler import NotFoundError, ConflictError

logger = logging.getLogger(__name__)

# Severity ranking for proper ordering (higher = more severe)
SEVERITY_RANK = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1
}

# Priority ranking for proper ordering (higher = more priority)
PRIORITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1
}


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
        from app.storage.models import JobStatusEnum as ModelJobStatusEnum
        
        job = self.get_job_or_raise(job_id)
        # Convert schema enum to model enum
        model_status = ModelJobStatusEnum[status.name]
        setattr(job, 'status', model_status)
        if error_message:
            setattr(job, 'error_message', error_message)
        setattr(job, 'updated_at', datetime.utcnow())
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
        setattr(job, 'progress', progress_percent)
        if current_stage:
            setattr(job, 'current_stage', current_stage)
        setattr(job, 'updated_at', datetime.utcnow())
        self.db.flush()
        return job
    
    def update_job_metadata(
        self,
        job_id: str,
        metadata: Dict[str, Any]
    ) -> Job:
        """Update job metadata."""
        job = self.get_job_or_raise(job_id)
        current_metadata = getattr(job, 'job_metadata', None)
        if current_metadata:
            current_metadata.update(metadata)
            setattr(job, 'job_metadata', current_metadata)
        else:
            setattr(job, 'job_metadata', metadata)
        setattr(job, 'updated_at', datetime.utcnow())
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
        """Get files by language for a job. Tolerant of enum-vs-string mismatches."""
        # Handle both enum and string values
        language_value = language.value if isinstance(language, LanguageEnum) else language
        return self.db.query(File).filter(
            and_(File.job_id == job_id, File.language == language_value)
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
            setattr(file, 'parsed_content', parsed_content)
        if complexity_score is not None:
            setattr(file, 'complexity_score', complexity_score)
        if lines_of_code is not None:
            setattr(file, 'lines_of_code', lines_of_code)
        
        # Update the timestamp
        setattr(file, 'updated_at', datetime.utcnow())
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
            query = query.filter(Risk.level == severity.value)
        
        # Fetch all risks and sort by severity rank (handle string values)
        risks = query.all()
        risks.sort(key=lambda r: SEVERITY_RANK.get(str(r.level).lower() if r.level is not None else "", 0), reverse=True)
        return risks
    
    def get_critical_risks(self, job_id: str) -> List[Risk]:
        """Get critical and high severity risks."""
        return self.db.query(Risk).filter(
            and_(
                Risk.job_id == job_id,
                or_(
                    Risk.level == SeverityEnum.CRITICAL.value,
                    Risk.level == SeverityEnum.HIGH.value
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
        """Get all suggestions for a job, ordered by priority rank."""
        suggestions = self.db.query(Suggestion).filter(
            Suggestion.job_id == job_id
        ).all()
        
        # Sort by priority rank (handle both integer and string priorities)
        def get_priority_rank(s):
            if isinstance(s.priority, int):
                return s.priority
            return PRIORITY_RANK.get(str(s.priority).lower() if s.priority else "", 0)
        
        suggestions.sort(key=get_priority_rank, reverse=True)
        return suggestions
    
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
