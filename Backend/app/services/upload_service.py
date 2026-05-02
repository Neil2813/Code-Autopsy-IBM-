# for IBM hackathon
"""
Upload service for handling file uploads, repository cloning, and code snippets.
"""

import logging
import uuid
import shutil
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import git

from app.config.settings import get_settings
from app.schemas.upload import UploadResponse, UploadedFile
from app.schemas.common import LanguageEnum, FileTypeEnum
from app.storage.database import get_db
from app.storage.models import Job, File, JobStatusEnum
from app.utils.file_handler import file_handler
from app.utils.language_detector import language_detector

settings = get_settings()
logger = logging.getLogger(__name__)


class UploadService:
    """Service for handling code uploads."""
    
    async def upload_files(self, files: List[UploadFile]) -> UploadResponse:
        """
        Handle file uploads with enhanced metadata storage.
        
        Args:
            files: List of uploaded files
            
        Returns:
            UploadResponse with job ID and metadata
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        upload_timestamp = datetime.utcnow()
        
        # Validate and save files
        saved_files = []
        total_size = 0
        file_hashes = []
        
        for upload_file in files:
            # Validate file type
            if not file_handler.validate_file_type(upload_file.filename or ""):
                logger.warning(f"Invalid file type: {upload_file.filename}")
                continue
            
            # Get file size
            content = await upload_file.read()
            file_size = len(content)
            
            # Validate file size
            if not file_handler.validate_file_size(file_size):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {upload_file.filename} exceeds maximum size"
                )
            
            # Reset file pointer
            await upload_file.seek(0)
            
            # Save file
            file_path = await file_handler.save_upload(upload_file, job_id)
            
            # Calculate file hash for deduplication
            file_hash = await file_handler.calculate_file_hash(file_path)
            file_hashes.append(file_hash)
            
            # Detect language with confidence
            language, confidence = language_detector.detect_language_with_confidence(
                content.decode('utf-8', errors='ignore'),
                upload_file.filename or ""
            )
            
            # Count lines of code
            lines_of_code = content.decode('utf-8', errors='ignore').count('\n') + 1
            
            # Determine file type
            file_type = "source" if language else "config"
            if upload_file.filename:
                ext = Path(upload_file.filename).suffix.lower()
                if ext in ['.xml', '.properties', '.yaml', '.yml', '.json']:
                    file_type = "config"
                elif ext in ['.md', '.txt', '.doc']:
                    file_type = "documentation"
            
            saved_files.append({
                "path": str(file_path),
                "name": upload_file.filename,
                "size": file_size,
                "language": language,
                "language_confidence": confidence,
                "lines_of_code": lines_of_code,
                "file_type": file_type,
                "file_hash": file_hash,
                "original_name": upload_file.filename
            })
            
            total_size += file_size
        
        if not saved_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid files to process"
            )
        
        # Detect languages
        detected_languages = list(set(
            f["language"] for f in saved_files if f["language"]
        ))
        
        # Create job in database with enhanced metadata
        with get_db() as db:
            job = Job(
                id=job_id,
                status=JobStatusEnum.QUEUED,
                progress=0.0,
                job_metadata={
                    "upload_type": "files",
                    "file_count": len(saved_files),
                    "total_size": total_size,
                    "languages": detected_languages,
                    "upload_timestamp": upload_timestamp.isoformat(),
                    "file_hashes": file_hashes,
                    "file_types": list(set(f["file_type"] for f in saved_files))
                }
            )
            db.add(job)
            
            # Create file records with enhanced metadata
            uploaded_files = []
            for file_info in saved_files:
                file_record = File(
                    job_id=job_id,
                    file_path=file_info["path"],
                    language=file_info["language"],
                    file_type=file_info["file_type"],
                    size_bytes=file_info["size"],
                    lines_of_code=file_info.get("lines_of_code", 0)
                )
                db.add(file_record)
                db.flush()  # Get the ID
                
                # Convert string language to enum
                lang_enum = None
                if file_info["language"]:
                    try:
                        lang_enum = LanguageEnum(file_info["language"])
                    except ValueError:
                        lang_enum = LanguageEnum.UNKNOWN
                
                # Convert file type to enum
                file_type_enum = FileTypeEnum.SOURCE
                try:
                    file_type_enum = FileTypeEnum(file_info["file_type"].upper())
                except (ValueError, AttributeError):
                    pass
                
                uploaded_files.append({
                    "file_id": str(file_record.id),
                    "filename": file_info["name"],
                    "file_path": file_info["path"],
                    "size_bytes": file_info["size"],
                    "detected_language": lang_enum,
                    "file_type": file_type_enum
                })
        
        logger.info(f"Created job {job_id} with {len(saved_files)} files (total: {total_size} bytes)")
        
        # Determine primary language
        primary_lang_str = language_detector.get_primary_language(
            [Path(f["path"]) for f in saved_files]
        )
        primary_lang_enum = None
        if primary_lang_str:
            try:
                primary_lang_enum = LanguageEnum(primary_lang_str)
            except ValueError:
                primary_lang_enum = LanguageEnum.UNKNOWN
        
        # Convert detected languages to enums
        lang_enums = []
        for lang in detected_languages:
            try:
                lang_enums.append(LanguageEnum(lang))
            except ValueError:
                lang_enums.append(LanguageEnum.UNKNOWN)
        
        return UploadResponse(
            job_id=job_id,
            upload_id=job_id,  # Use job_id as upload_id
            status="uploaded",
            message=f"Successfully uploaded {len(saved_files)} files",
            files=[UploadedFile(**f) for f in uploaded_files],
            total_files=len(saved_files),
            total_size_bytes=total_size,
            detected_languages=lang_enums,
            primary_language=primary_lang_enum
        )
    
    async def clone_repository(
        self,
        repository_url: str,
        branch: Optional[str] = None,
        subdirectory: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> UploadResponse:
        """
        Clone a Git repository and process its files.
        
        Args:
            repository_url: Git repository URL
            branch: Branch to clone (default: main/master)
            subdirectory: Subdirectory to process (optional)
            include_patterns: File patterns to include (e.g., ["*.java", "*.xml"])
            exclude_patterns: File patterns to exclude (e.g., ["**/test/**"])
            
        Returns:
            UploadResponse with job ID and metadata
        """
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        logger.info(f"Repository clone requested: {repository_url}, branch: {branch}")
        
        # Create temporary clone directory
        clone_dir = Path(settings.upload_dir) / "repos" / job_id
        clone_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone repository
            logger.info(f"Cloning repository to {clone_dir}")
            clone_attempts = [branch] if branch else [None, "main", "master"]
            last_git_error = None
            repo = None
            for clone_branch in clone_attempts:
                try:
                    clone_kwargs: Dict[str, Any] = {"depth": 1}
                    if clone_branch:
                        clone_kwargs["branch"] = clone_branch
                    repo = git.Repo.clone_from(repository_url, clone_dir, **clone_kwargs)  # type: ignore[arg-type]
                    branch = clone_branch or branch
                    break
                except git.GitCommandError as e:
                    last_git_error = e
                    logger.warning("Clone attempt failed for branch %s: %s", clone_branch or "<default>", e)
                    if clone_dir.exists():
                        shutil.rmtree(clone_dir, ignore_errors=True)
                    clone_dir.mkdir(parents=True, exist_ok=True)

            if repo is None:
                raise last_git_error or git.GitCommandError("clone", 128)
            logger.info(f"Repository cloned successfully: {repo.head.commit.hexsha[:8]}")
            
            # Determine target directory
            target_dir = clone_dir
            if subdirectory:
                target_dir = clone_dir / subdirectory
                if not target_dir.exists():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Subdirectory '{subdirectory}' not found in repository"
                    )
            
            # Set default patterns if not provided
            if not include_patterns:
                include_patterns = ["*.java", "*.cbl", "*.rpg", "*.py", "*.js", "*.ts", "*.xml", "*.properties"]
            if not exclude_patterns:
                exclude_patterns = ["**/test/**", "**/*.class", "**/target/**", "**/build/**", "**/.git/**", "**/node_modules/**"]
            
            # Find and process files with preserved directory structure
            saved_files = []
            total_size = 0
            file_hashes = []
            upload_timestamp = datetime.utcnow()
            
            for file_path in target_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Get relative path for pattern matching
                rel_path = str(file_path.relative_to(target_dir))
                
                # Check exclude patterns first
                excluded = False
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                        excluded = True
                        break
                
                if excluded:
                    continue
                
                # Check include patterns
                included = False
                for pattern in include_patterns:
                    if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                        included = True
                        break
                
                if not included:
                    continue
                
                # Validate file type
                if not file_handler.validate_file_type(file_path.name):
                    continue
                
                # Read file content
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    file_size = len(content)
                    
                    # Validate file size
                    if not file_handler.validate_file_size(file_size):
                        logger.warning(f"File {file_path.name} exceeds maximum size, skipping")
                        continue
                    
                    # Copy to job directory preserving relative path structure
                    job_dir = Path(settings.upload_dir) / job_id
                    job_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Preserve directory structure from repository
                    dest_path = job_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)
                    
                    # Calculate file hash
                    file_hash = await file_handler.calculate_file_hash(dest_path)
                    file_hashes.append(file_hash)
                    
                    # Detect language with confidence
                    language, confidence = language_detector.detect_language_with_confidence(
                        content.decode('utf-8', errors='ignore'),
                        file_path.name
                    )
                    
                    # Count lines of code
                    lines_of_code = content.decode('utf-8', errors='ignore').count('\n') + 1
                    
                    # Determine file type
                    file_type = "source" if language else "config"
                    ext = file_path.suffix.lower()
                    if ext in ['.xml', '.properties', '.yaml', '.yml', '.json']:
                        file_type = "config"
                    elif ext in ['.md', '.txt', '.doc']:
                        file_type = "documentation"
                    
                    saved_files.append({
                        "path": str(dest_path),
                        "relative_path": rel_path,
                        "name": file_path.name,
                        "size": file_size,
                        "language": language,
                        "language_confidence": confidence,
                        "lines_of_code": lines_of_code,
                        "file_type": file_type,
                        "file_hash": file_hash
                    })
                    
                    total_size += file_size
                    
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue
            
            if not saved_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid files found in repository matching the specified patterns"
                )
            
            # Detect languages
            detected_languages = list(set(
                f["language"] for f in saved_files if f["language"]
            ))
            
            # Create job in database with enhanced metadata
            with get_db() as db:
                job = Job(
                    id=job_id,
                    status=JobStatusEnum.QUEUED,
                    progress=0.0,
                    job_metadata={
                        "upload_type": "repository",
                        "repository_url": str(repository_url),
                        "branch": branch or "main",
                        "subdirectory": subdirectory,
                        "file_count": len(saved_files),
                        "total_size": total_size,
                        "languages": detected_languages,
                        "upload_timestamp": upload_timestamp.isoformat(),
                        "file_hashes": file_hashes,
                        "file_types": list(set(f["file_type"] for f in saved_files)),
                        "include_patterns": include_patterns,
                        "exclude_patterns": exclude_patterns,
                        "directory_structure_preserved": True
                    }
                )
                db.add(job)
                
                # Create file records with enhanced metadata
                uploaded_files = []
                for file_info in saved_files:
                    file_record = File(
                        job_id=job_id,
                        file_path=file_info["path"],
                        language=file_info["language"],
                        file_type=file_info["file_type"],
                        size_bytes=file_info["size"],
                        lines_of_code=file_info.get("lines_of_code", 0)
                    )
                    db.add(file_record)
                    db.flush()
                    
                    # Convert string language to enum
                    lang_enum = None
                    if file_info["language"]:
                        try:
                            lang_enum = LanguageEnum(file_info["language"])
                        except ValueError:
                            lang_enum = LanguageEnum.UNKNOWN
                    
                    # Convert file type to enum
                    file_type_enum = FileTypeEnum.SOURCE
                    try:
                        file_type_enum = FileTypeEnum(file_info["file_type"].upper())
                    except (ValueError, AttributeError):
                        pass
                    
                    uploaded_files.append({
                        "file_id": str(file_record.id),
                        "filename": file_info["name"],
                        "file_path": file_info["path"],
                        "size_bytes": file_info["size"],
                        "detected_language": lang_enum,
                        "file_type": file_type_enum
                    })
            
            logger.info(f"Created job {job_id} with {len(saved_files)} files from repository")
            
            # Determine primary language
            primary_lang_str = language_detector.get_primary_language(
                [Path(f["path"]) for f in saved_files]
            )
            primary_lang_enum = None
            if primary_lang_str:
                try:
                    primary_lang_enum = LanguageEnum(primary_lang_str)
                except ValueError:
                    primary_lang_enum = LanguageEnum.UNKNOWN
            
            # Convert detected languages to enums
            lang_enums = []
            for lang in detected_languages:
                try:
                    lang_enums.append(LanguageEnum(lang))
                except ValueError:
                    lang_enums.append(LanguageEnum.UNKNOWN)
            
            return UploadResponse(
                job_id=job_id,
                upload_id=job_id,
                status="uploaded",
                message=f"Successfully cloned repository and processed {len(saved_files)} files",
                files=[UploadedFile(**f) for f in uploaded_files],
                total_files=len(saved_files),
                total_size_bytes=total_size,
                detected_languages=lang_enums,
                primary_language=primary_lang_enum
            )
            
        except git.GitCommandError as e:
            logger.error(f"Git clone failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to clone repository: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Repository processing failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process repository: {str(e)}"
            )
        finally:
            # Clean up cloned repository
            if clone_dir.exists():
                try:
                    shutil.rmtree(clone_dir)
                    logger.info(f"Cleaned up clone directory: {clone_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up clone directory: {e}")
    
    async def process_snippet(
        self,
        code: str,
        language: Optional[str] = None,
        filename: Optional[str] = None
    ) -> UploadResponse:
        """
        Process a code snippet with rigorous language detection and metadata.
        
        Args:
            code: Code snippet content
            language: Programming language (optional, will be detected if not provided)
            filename: Filename for the snippet (optional)
            
        Returns:
            UploadResponse with job ID and metadata
        """
        if not code or len(code.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code snippet cannot be empty"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        upload_timestamp = datetime.utcnow()
        
        # Detect language with confidence if not provided
        language_confidence = 1.0
        if not language:
            language, language_confidence = language_detector.detect_language_with_confidence(
                code, filename or ""
            )
            if not language:
                language = "unknown"
                language_confidence = 0.0
        
        # Create temporary file for snippet
        job_dir = Path(settings.upload_dir) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename with proper extension
        if not filename:
            ext_map = {
                'java': '.java',
                'cobol': '.cbl',
                'rpg': '.rpg',
                'jcl': '.jcl',
                'python': '.py',
                'javascript': '.js',
                'typescript': '.ts',
                'sql': '.sql',
                'xml': '.xml',
                'json': '.json',
                'yaml': '.yaml'
            }
            ext = ext_map.get(language, '.txt')
            filename = f"snippet{ext}"
        
        # Sanitize filename
        filename = file_handler.sanitize_filename(filename)
        snippet_path = job_dir / filename
        
        # Save snippet
        with open(snippet_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        file_size = len(code.encode('utf-8'))
        lines_of_code = code.count('\n') + 1
        
        # Calculate file hash
        file_hash = await file_handler.calculate_file_hash(snippet_path)
        
        # Determine file type explicitly
        file_type = "source"
        if language in ['xml', 'json', 'yaml', 'properties']:
            file_type = "config"
        elif language == "sql":
            file_type = "source"
        
        # Create job in database with enhanced metadata
        with get_db() as db:
            job = Job(
                id=job_id,
                status=JobStatusEnum.QUEUED,
                progress=0.0,
                job_metadata={
                    "upload_type": "snippet",
                    "language": language,
                    "language_confidence": language_confidence,
                    "size": file_size,
                    "lines_of_code": lines_of_code,
                    "upload_timestamp": upload_timestamp.isoformat(),
                    "file_hash": file_hash,
                    "file_type": file_type,
                    "original_filename": filename
                }
            )
            db.add(job)
            
            # Create file record with explicit metadata
            file_record = File(
                job_id=job_id,
                file_path=str(snippet_path),
                language=language,
                file_type=file_type,
                size_bytes=file_size,
                lines_of_code=lines_of_code
            )
            db.add(file_record)
            db.flush()
            
            # Convert language to enum
            lang_enum = None
            if language:
                try:
                    lang_enum = LanguageEnum(language)
                except ValueError:
                    lang_enum = LanguageEnum.UNKNOWN
            
            # Convert file type to enum
            file_type_enum = FileTypeEnum.SOURCE
            try:
                file_type_enum = FileTypeEnum(file_type.upper())
            except (ValueError, AttributeError):
                pass
            
            uploaded_file = UploadedFile(
                file_id=str(file_record.id),
                filename=filename,
                file_path=str(snippet_path),
                size_bytes=file_size,
                detected_language=lang_enum,
                file_type=file_type_enum
            )
        
        logger.info(f"Created job {job_id} for code snippet ({file_size} bytes)")
        
        return UploadResponse(
            job_id=job_id,
            upload_id=job_id,
            status="uploaded",
            message="Code snippet uploaded successfully",
            files=[uploaded_file],
            total_files=1,
            total_size_bytes=file_size,
            detected_languages=[lang_enum] if lang_enum else [],
            primary_language=lang_enum
        )


# Singleton instance
upload_service = UploadService()

# Made with Bob
