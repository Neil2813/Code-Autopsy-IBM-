"""
File handling utilities for upload and storage management.
"""

import hashlib
import logging
import shutil
import re
from pathlib import Path
from typing import List, Optional
import zipfile
import tarfile

from fastapi import UploadFile, HTTPException

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class FileHandler:
    """Handle file operations for uploads and storage."""
    
    # Characters not allowed in filenames
    INVALID_FILENAME_CHARS = r'[<>:"|?*\x00-\x1f]'
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.temp_dir = Path(settings.temp_dir)
        self.max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def sanitize_filename(self, filename: str, preserve_path: bool = False) -> str:
        """
        Sanitize filename to prevent path traversal and invalid characters.
        
        Args:
            filename: Original filename
            preserve_path: If True, preserve directory structure (for repository uploads)
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Remove or replace invalid characters
        sanitized = re.sub(self.INVALID_FILENAME_CHARS, '_', filename)
        
        if preserve_path:
            # For paths, normalize and validate each component
            parts = Path(sanitized).parts
            safe_parts = []
            for part in parts:
                # Skip dangerous path components
                if part in ('..', '.', ''):
                    continue
                # Remove leading/trailing dots and spaces
                part = part.strip('. ')
                if part:
                    safe_parts.append(part)
            
            if not safe_parts:
                return "unnamed_file"
            
            return str(Path(*safe_parts))
        else:
            # For single filenames, just take the basename
            sanitized = Path(sanitized).name
            # Remove leading/trailing dots and spaces
            sanitized = sanitized.strip('. ')
            
            return sanitized if sanitized else "unnamed_file"
    
    def validate_extraction_path(self, extract_to: Path, member_path: str) -> Path:
        """
        Validate that extraction path is safe (prevents zip-slip attacks).
        
        Args:
            extract_to: Base extraction directory
            member_path: Path of the archive member
            
        Returns:
            Validated absolute path
            
        Raises:
            HTTPException: If path traversal is detected
        """
        # Sanitize the member path
        safe_member = self.sanitize_filename(member_path, preserve_path=True)
        
        # Resolve to absolute path
        target_path = (extract_to / safe_member).resolve()
        extract_to_resolved = extract_to.resolve()
        
        # Ensure the target is within the extraction directory
        try:
            target_path.relative_to(extract_to_resolved)
        except ValueError:
            logger.error(f"Path traversal attempt detected: {member_path}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid archive: path traversal detected in {member_path}"
            )
        
        return target_path
    
    async def save_upload(self, file: UploadFile, job_id: str, preserve_path: Optional[str] = None) -> Path:
        """
        Save uploaded file to job directory.
        
        Args:
            file: Uploaded file
            job_id: Job identifier
            preserve_path: Optional relative path to preserve (for repository structure)
            
        Returns:
            Path to saved file
        """
        job_dir = self.upload_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        filename = self.sanitize_filename(file.filename or "unnamed_file")
        
        # Handle path preservation for repository uploads
        if preserve_path:
            safe_path = self.sanitize_filename(preserve_path, preserve_path=True)
            file_path = job_dir / safe_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            file_path = job_dir / filename
        
        # Validate the final path is within job directory
        try:
            file_path.resolve().relative_to(job_dir.resolve())
        except ValueError:
            logger.error(f"Path traversal attempt in save_upload: {file.filename}")
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Saved file: {file_path}")
        return file_path
    
    async def extract_archive(self, archive_path: Path, extract_to: Path) -> List[Path]:
        """
        Extract ZIP or TAR archive with path traversal protection.
        
        Args:
            archive_path: Path to archive file
            extract_to: Directory to extract to
            
        Returns:
            List of extracted file paths
        """
        extract_to.mkdir(parents=True, exist_ok=True)
        extracted_files = []
        
        try:
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # Validate and extract each member safely
                    for member in zip_ref.namelist():
                        # Skip directories
                        if member.endswith('/'):
                            continue
                        
                        # Validate extraction path
                        target_path = self.validate_extraction_path(extract_to, member)
                        
                        # Create parent directories
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Extract the file
                        with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        
                        extracted_files.append(target_path)
            
            elif archive_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz']:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    # Validate and extract each member safely
                    for member in tar_ref.getmembers():
                        # Skip directories and special files
                        if not member.isfile():
                            continue
                        
                        # Validate extraction path
                        target_path = self.validate_extraction_path(extract_to, member.name)
                        
                        # Create parent directories
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Extract the file
                        source = tar_ref.extractfile(member)
                        if source:
                            with source, open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                        
                        extracted_files.append(target_path)
            
            logger.info(f"Extracted {len(extracted_files)} files from {archive_path}")
            return extracted_files
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to extract archive {archive_path}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to extract archive: {str(e)}")
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate file type based on extension."""
        allowed_extensions = {
            '.java', '.class', '.jar',
            '.cbl', '.cob', '.cobol',
            '.rpg', '.rpgle', '.sqlrpgle',
            '.jcl', '.proc',
            '.xml', '.properties', '.yaml', '.yml', '.json',
            '.sql', '.ddl',
            '.txt', '.md',
            '.zip', '.tar', '.gz', '.tgz'
        }
        
        ext = Path(filename).suffix.lower()
        return ext in allowed_extensions
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size is within limits."""
        return file_size <= self.max_size_bytes
    
    async def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def get_file_extension(self, filename: str) -> str:
        """Get file extension without dot."""
        return Path(filename).suffix.lstrip('.')
    
    async def cleanup_job_files(self, job_id: str) -> None:
        """Clean up all files for a job."""
        job_dir = self.upload_dir / job_id
        
        if job_dir.exists():
            shutil.rmtree(job_dir)
            logger.info(f"Cleaned up files for job: {job_id}")
    
    def list_files_recursive(self, directory: Path) -> List[Path]:
        """List all files recursively in directory."""
        files = []
        for item in directory.rglob('*'):
            if item.is_file():
                files.append(item)
        return files
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get file information."""
        stat = file_path.stat()
        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "extension": self.get_file_extension(file_path.name),
            "modified": stat.st_mtime
        }


# Singleton instance
file_handler = FileHandler()

# Made with Bob
