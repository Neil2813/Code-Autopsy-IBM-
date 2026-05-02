"""
COBOL Parser

Parser for COBOL source code.
"""

import logging
import re
from typing import List, Optional

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
        """Parse COBOL divisions with accurate boundaries."""
        division_pattern = re.compile(
            r'^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION',
            re.IGNORECASE | re.MULTILINE
        )
        
        lines = content.split('\n')
        divisions = []
        
        # First pass: find all divisions
        for i, line in enumerate(lines, 1):
            match = division_pattern.search(line)
            if match:
                division_name = match.group(1).upper()
                divisions.append((i, division_name))
        
        # Second pass: create nodes with accurate line_end
        for idx, (line_start, division_name) in enumerate(divisions):
            # End is either the start of next division or end of file
            if idx + 1 < len(divisions):
                line_end = divisions[idx + 1][0] - 1
            else:
                line_end = len(lines)
            
            node = CodeNode(
                node_type=NodeType.DIVISION,
                name=f"{division_name} DIVISION",
                line_start=line_start,
                line_end=line_end
            )
            
            # Calculate complexity for PROCEDURE DIVISION
            if division_name == 'PROCEDURE':
                node.complexity = self._calculate_cyclomatic_complexity(content, line_start, line_end)
            
            result.nodes.append(node)
            result.metadata.setdefault('divisions', []).append(division_name)
            logger.debug(f"Found division: {division_name} (lines {line_start}-{line_end})")
    
    def _parse_sections(self, content: str, result: ParseResult) -> None:
        """Parse COBOL sections with accurate boundaries."""
        section_pattern = re.compile(
            r'^\s*([A-Z0-9\-]+)\s+SECTION',
            re.IGNORECASE | re.MULTILINE
        )
        
        lines = content.split('\n')
        sections = []
        
        # Find all sections
        for i, line in enumerate(lines, 1):
            match = section_pattern.search(line)
            if match:
                section_name = match.group(1).upper()
                sections.append((i, section_name))
        
        # Create nodes with boundaries
        for idx, (line_start, section_name) in enumerate(sections):
            # Find end: next section, next division, or end of file
            line_end = self._find_section_end(lines, line_start, sections, idx)
            
            node = CodeNode(
                node_type=NodeType.SECTION,
                name=section_name,
                line_start=line_start,
                line_end=line_end
            )
            
            # Add parent division context
            parent_division = self._find_parent_division(lines, line_start)
            if parent_division:
                node.parent = parent_division
                node.metadata['division'] = parent_division
            
            # Calculate complexity
            node.complexity = self._calculate_cyclomatic_complexity(content, line_start, line_end)
            
            result.nodes.append(node)
            result.metadata.setdefault('sections', []).append(section_name)
            logger.debug(f"Found section: {section_name} (lines {line_start}-{line_end})")
    
    def _parse_paragraphs(self, content: str, result: ParseResult) -> None:
        """Parse COBOL paragraphs with accurate boundaries."""
        # COBOL paragraphs are typically alphanumeric names followed by a period
        paragraph_pattern = re.compile(
            r'^\s{0,6}([A-Z0-9\-]+)\s*\.\s*$',
            re.MULTILINE
        )
        
        lines = content.split('\n')
        paragraphs = []
        
        # Common COBOL keywords to exclude
        excluded_keywords = {
            'STOP', 'EXIT', 'GOBACK', 'END', 'CONTINUE', 'NEXT',
            'PERFORM', 'IF', 'ELSE', 'EVALUATE', 'WHEN', 'MOVE',
            'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'COMPUTE',
            'DISPLAY', 'ACCEPT', 'OPEN', 'CLOSE', 'READ', 'WRITE'
        }
        
        for i, line in enumerate(lines, 1):
            # Skip if it's a division or section
            upper_line = line.upper()
            if 'DIVISION' in upper_line or 'SECTION' in upper_line:
                continue
            
            # Skip comments
            if self._is_comment_line(line.strip()):
                continue
            
            match = paragraph_pattern.search(line)
            if match:
                para_name = match.group(1).upper()
                # Filter out common COBOL keywords
                if para_name not in excluded_keywords and len(para_name) > 1:
                    paragraphs.append((i, para_name))
        
        # Create nodes with boundaries
        for idx, (line_start, para_name) in enumerate(paragraphs):
            # Find end: next paragraph or end of section
            if idx + 1 < len(paragraphs):
                line_end = paragraphs[idx + 1][0] - 1
            else:
                line_end = self._find_paragraph_end(lines, line_start)
            
            node = CodeNode(
                node_type=NodeType.PARAGRAPH,
                name=para_name,
                line_start=line_start,
                line_end=line_end
            )
            
            # Find parent section
            parent_section = self._find_parent_section(lines, line_start)
            if parent_section:
                node.parent = parent_section
                node.metadata['section'] = parent_section
            
            # Calculate complexity
            node.complexity = self._calculate_cyclomatic_complexity(content, line_start, line_end)
            
            # Check for PERFORM statements (calls to other paragraphs)
            self._extract_paragraph_calls(lines[line_start-1:line_end], node)
            
            result.nodes.append(node)
            logger.debug(f"Found paragraph: {para_name} (lines {line_start}-{line_end})")
    
    def _parse_copybooks(self, content: str, result: ParseResult) -> None:
        """Parse COBOL COPY statements (copybook includes) with enhanced details."""
        # Match COPY statements with optional REPLACING clause
        copy_pattern = re.compile(
            r'COPY\s+([A-Z0-9\-]+)(?:\s+(?:IN|OF)\s+([A-Z0-9\-]+))?(?:\s+REPLACING\s+(.+?)(?=\.|$))?',
            re.IGNORECASE | re.DOTALL
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for match in copy_pattern.finditer(line):
                copybook_name = match.group(1).upper()
                library = match.group(2).upper() if match.group(2) else None
                replacing = match.group(3)
                
                # Create copybook node
                node = CodeNode(
                    node_type=NodeType.COPYBOOK,
                    name=copybook_name,
                    line_start=i,
                    line_end=i
                )
                
                if library:
                    node.metadata['library'] = library
                if replacing:
                    node.metadata['replacing'] = replacing.strip()
                
                result.nodes.append(node)
                result.dependencies.append(copybook_name)
                
                copybook_info = {'name': copybook_name, 'line': i}
                if library:
                    copybook_info['library'] = library
                result.metadata.setdefault('copybooks', []).append(copybook_info)
                
                logger.debug(f"Found copybook: {copybook_name}" +
                           (f" in {library}" if library else ""))
    
    def _parse_file_descriptors(self, content: str, result: ParseResult) -> None:
        """Parse COBOL file descriptors (FD) with record details."""
        fd_pattern = re.compile(
            r'^\s*FD\s+([A-Z0-9\-]+)',
            re.IGNORECASE | re.MULTILINE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = fd_pattern.search(line)
            if match:
                fd_name = match.group(1).upper()
                
                # Find the end of FD declaration (usually followed by 01 level)
                line_end = self._find_fd_end(lines, i - 1) + 1
                
                node = CodeNode(
                    node_type=NodeType.FILE_DESCRIPTOR,
                    name=fd_name,
                    line_start=i,
                    line_end=line_end
                )
                
                # Extract FD details (LABEL, BLOCK, RECORD clauses)
                fd_block = '\n'.join(lines[i-1:line_end])
                self._extract_fd_details(fd_block, node)
                
                result.nodes.append(node)
                
                fd_info = {'name': fd_name, 'line': i}
                if 'record_name' in node.metadata:
                    fd_info['record'] = node.metadata['record_name']
                result.metadata.setdefault('file_descriptors', []).append(fd_info)
                
                logger.debug(f"Found FD: {fd_name} (lines {i}-{line_end})")
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a COBOL comment (enhanced detection)."""
        if not line:
            return False
        
        stripped = line.strip()
        
        # Empty lines are not comments
        if not stripped:
            return False
        
        # Fixed format: * in column 7 (position 6 in 0-indexed)
        if len(line) >= 7 and line[6] in ('*', '/'):
            return True
        
        # Free format or stripped: starts with * or *>
        if stripped.startswith('*') or stripped.startswith('*>'):
            return True
        
        # Inline comments (COBOL 2002+)
        if '*>' in stripped:
            return True
        
        return False
    
    def _find_section_end(self, lines: list, start_line: int, sections: list, current_idx: int) -> int:
        """Find the end of a section."""
        # Check for next section
        if current_idx + 1 < len(sections):
            return sections[current_idx + 1][0] - 1
        
        # Check for next division
        for i in range(start_line, len(lines)):
            if 'DIVISION' in lines[i].upper():
                return i
        
        return len(lines)
    
    def _find_paragraph_end(self, lines: list, start_line: int) -> int:
        """Find the end of a paragraph."""
        # Look for next paragraph, section, or division
        for i in range(start_line, len(lines)):
            line = lines[i].upper()
            if 'DIVISION' in line or 'SECTION' in line:
                return i
            # Check for paragraph pattern
            if re.match(r'^\s{0,6}[A-Z0-9\-]+\s*\.\s*$', lines[i]):
                return i
        
        return len(lines)
    
    def _find_fd_end(self, lines: list, start_idx: int) -> int:
        """Find the end of an FD declaration (usually at 01 level)."""
        for i in range(start_idx + 1, min(start_idx + 20, len(lines))):
            if re.match(r'^\s*01\s+', lines[i], re.IGNORECASE):
                return i
            if re.match(r'^\s*FD\s+', lines[i], re.IGNORECASE):
                return i - 1
        
        return start_idx + 1
    
    def _find_parent_division(self, lines: list, line_num: int) -> Optional[str]:
        """Find the parent division for a given line."""
        division_pattern = re.compile(
            r'^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION',
            re.IGNORECASE
        )
        
        for i in range(line_num - 1, -1, -1):
            match = division_pattern.search(lines[i])
            if match:
                return f"{match.group(1).upper()} DIVISION"
        
        return None
    
    def _find_parent_section(self, lines: list, line_num: int) -> Optional[str]:
        """Find the parent section for a given line."""
        section_pattern = re.compile(r'^\s*([A-Z0-9\-]+)\s+SECTION', re.IGNORECASE)
        
        for i in range(line_num - 1, -1, -1):
            # Stop at division boundary
            if 'DIVISION' in lines[i].upper():
                break
            
            match = section_pattern.search(lines[i])
            if match:
                return match.group(1).upper()
        
        return None
    
    def _extract_paragraph_calls(self, lines: list, node: CodeNode) -> None:
        """Extract PERFORM statements (calls to other paragraphs)."""
        perform_pattern = re.compile(
            r'PERFORM\s+([A-Z0-9\-]+)(?:\s+THRU\s+([A-Z0-9\-]+))?',
            re.IGNORECASE
        )
        
        calls = []
        for line in lines:
            for match in perform_pattern.finditer(line):
                para_name = match.group(1).upper()
                thru_para = match.group(2).upper() if match.group(2) else None
                
                if thru_para:
                    calls.append(f"{para_name} THRU {thru_para}")
                else:
                    calls.append(para_name)
        
        if calls:
            node.metadata['calls'] = calls
    
    def _extract_fd_details(self, fd_block: str, node: CodeNode) -> None:
        """Extract details from FD declaration."""
        # Extract LABEL clause
        label_match = re.search(r'LABEL\s+RECORDS?\s+(?:ARE\s+)?(\w+)', fd_block, re.IGNORECASE)
        if label_match:
            node.metadata['label_records'] = label_match.group(1).upper()
        
        # Extract BLOCK clause
        block_match = re.search(r'BLOCK\s+CONTAINS\s+(\d+)', fd_block, re.IGNORECASE)
        if block_match:
            node.metadata['block_size'] = int(block_match.group(1))
        
        # Extract RECORD clause
        record_match = re.search(r'RECORD\s+CONTAINS\s+(\d+)', fd_block, re.IGNORECASE)
        if record_match:
            node.metadata['record_size'] = int(record_match.group(1))
        
        # Extract 01 level record name
        record_name_match = re.search(r'01\s+([A-Z0-9\-]+)', fd_block, re.IGNORECASE)
        if record_name_match:
            node.metadata['record_name'] = record_name_match.group(1).upper()

# Made with Bob
