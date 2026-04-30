"""
COBOL Parser

Parser for COBOL source code.
"""

import logging
import re
from typing import List

from app.parsers.base_parser import (
    BaseParser, ParseResult, CodeNode, NodeType
)

logger = logging.getLogger(__name__)


class CobolParser(BaseParser):
    """Parser for COBOL source code."""
    
    def __init__(self):
        super().__init__()
        self.language = "cobol"
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a COBOL file."""
        lower_path = file_path.lower()
        return (
            lower_path.endswith('.cbl') or
            lower_path.endswith('.cob') or
            lower_path.endswith('.cobol') or
            lower_path.endswith('.cpy')  # Copybook
        )
    
    def parse(self, file_path: str, content: str) -> ParseResult:
        """
        Parse COBOL source code.
        
        Args:
            file_path: Path to COBOL file
            content: COBOL source code
            
        Returns:
            ParseResult with extracted structure
        """
        result = ParseResult(
            file_path=file_path,
            language=self.language,
            success=False
        )
        
        try:
            # Count lines
            code_lines, comment_lines, blank_lines = self._count_lines(content)
            result.lines_of_code = code_lines
            result.comment_lines = comment_lines
            result.blank_lines = blank_lines
            
            # Parse COBOL structure
            self._parse_divisions(content, result)
            self._parse_sections(content, result)
            self._parse_paragraphs(content, result)
            self._parse_copybooks(content, result)
            self._parse_file_descriptors(content, result)
            
            # Calculate complexity
            result.complexity_score = self._calculate_complexity(result.nodes)
            
            result.success = True
            logger.info(f"Successfully parsed COBOL file {file_path}: {len(result.nodes)} nodes")
            
        except Exception as e:
            logger.error(f"Failed to parse COBOL file {file_path}: {e}")
            result.errors.append(str(e))
            result.success = False
        
        return result
    
    def _parse_divisions(self, content: str, result: ParseResult) -> None:
        """Parse COBOL divisions."""
        division_pattern = re.compile(
            r'^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION',
            re.IGNORECASE | re.MULTILINE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = division_pattern.search(line)
            if match:
                division_name = match.group(1).upper()
                node = CodeNode(
                    node_type=NodeType.DIVISION,
                    name=f"{division_name} DIVISION",
                    line_start=i,
                    line_end=i
                )
                result.nodes.append(node)
                logger.debug(f"Found division: {division_name}")
    
    def _parse_sections(self, content: str, result: ParseResult) -> None:
        """Parse COBOL sections."""
        section_pattern = re.compile(
            r'^\s*([A-Z0-9\-]+)\s+SECTION',
            re.IGNORECASE | re.MULTILINE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = section_pattern.search(line)
            if match:
                section_name = match.group(1).upper()
                node = CodeNode(
                    node_type=NodeType.SECTION,
                    name=section_name,
                    line_start=i,
                    line_end=i
                )
                result.nodes.append(node)
    
    def _parse_paragraphs(self, content: str, result: ParseResult) -> None:
        """Parse COBOL paragraphs."""
        # COBOL paragraphs are typically alphanumeric names followed by a period
        paragraph_pattern = re.compile(
            r'^\s*([A-Z0-9\-]+)\s*\.',
            re.MULTILINE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Skip if it's a division or section
            if 'DIVISION' in line.upper() or 'SECTION' in line.upper():
                continue
            
            match = paragraph_pattern.search(line)
            if match:
                para_name = match.group(1)
                # Filter out common COBOL keywords
                if para_name not in ['STOP', 'EXIT', 'GOBACK', 'END']:
                    node = CodeNode(
                        node_type=NodeType.PARAGRAPH,
                        name=para_name,
                        line_start=i,
                        line_end=i
                    )
                    result.nodes.append(node)
    
    def _parse_copybooks(self, content: str, result: ParseResult) -> None:
        """Parse COBOL COPY statements (copybook includes)."""
        copy_pattern = re.compile(
            r'COPY\s+([A-Z0-9\-]+)',
            re.IGNORECASE
        )
        
        for match in copy_pattern.finditer(content):
            copybook_name = match.group(1)
            result.dependencies.append(copybook_name)
            result.metadata.setdefault('copybooks', []).append(copybook_name)
            logger.debug(f"Found copybook: {copybook_name}")
    
    def _parse_file_descriptors(self, content: str, result: ParseResult) -> None:
        """Parse COBOL file descriptors (FD)."""
        fd_pattern = re.compile(
            r'^\s*FD\s+([A-Z0-9\-]+)',
            re.IGNORECASE | re.MULTILINE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = fd_pattern.search(line)
            if match:
                fd_name = match.group(1)
                node = CodeNode(
                    node_type=NodeType.FILE_DESCRIPTOR,
                    name=fd_name,
                    line_start=i,
                    line_end=i
                )
                result.nodes.append(node)
                result.metadata.setdefault('file_descriptors', []).append(fd_name)
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a COBOL comment."""
        # COBOL comments start with * in column 7 (position 6 in 0-indexed)
        if len(line) >= 7:
            return line[6] == '*'
        return line.strip().startswith('*')

# Made with Bob
