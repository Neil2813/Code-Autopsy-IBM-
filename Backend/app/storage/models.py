# for IBM hackathon
"""
SQLAlchemy Database Models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class JobStatusEnum(enum.Enum):
    """Job processing status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class Job(Base):
    """Main job tracking table"""
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True)
    status = Column(Enum(JobStatusEnum, native_enum=False, length=50), nullable=False, default=JobStatusEnum.QUEUED)
    progress = Column(Float, default=0.0)
    current_stage = Column(String(50))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    # Relationships
    files = relationship("File", back_populates="job", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="job", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="job", cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="job", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="job", cascade="all, delete-orphan")


class File(Base):
    """Uploaded files table"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    language = Column(String(50))
    file_type = Column(String(50))
    content = Column(Text)
    parsed_content = Column(JSON)  # Parsed/analyzed content from parsers
    size_bytes = Column(Integer)
    lines_of_code = Column(Integer)
    complexity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="files")


class AnalysisResult(Base):
    """Analysis results table"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    result_type = Column(String(50), nullable=False)  # summary, dependency_graph, etc.
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="analysis_results")


class Risk(Base):
    """Detected risks table"""
    __tablename__ = "risks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    risk_id = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(50))
    level = Column(String(20))
    affected_files = Column(JSON)
    line_numbers = Column(JSON)
    recommendation = Column(Text)
    confidence = Column(Float)
    mcp_solution_available = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="risks")


class Suggestion(Base):
    """Modernization suggestions table"""
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    suggestion_id = Column(String(50), unique=True, nullable=False)
    type = Column(String(50))
    title = Column(Text, nullable=False)
    description = Column(Text)
    rationale = Column(Text)
    priority = Column(Integer)
    effort_estimate = Column(String(50))
    affected_files = Column(JSON)
    before_snippet = Column(Text)
    after_snippet = Column(Text)
    confidence = Column(Float)
    mcp_based = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="suggestions")


class Query(Base):
    """Query history table"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    confidence = Column(Float)
    references = Column(JSON)
    mcp_solutions_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="queries")

# Made with Bob
