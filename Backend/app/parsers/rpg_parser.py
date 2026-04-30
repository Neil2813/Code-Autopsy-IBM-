"""
RPG Parser

Parser for RPG (Report Program Generator) source code.
"""

import logging
import re

from app.parsers.base_parser import (
    BaseParser, ParseResult, CodeNode, NodeType
)

logger = logging.getLogger(__name__)


class RpgParser(BaseParser):
    """Parser for RPG source code."""
    
    def __init__(self):
        super().__init__()
        self.language = "rpg"
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is an RPG file."""
        lower_path = file_path.lower()
        return (
            lower_path.endswith('.rpg') or
            lower_path.endswith('.rpgle') or
            lower_path.endswith('.sqlrpgle') or
            lower_path.endswith('.rpg4')
        )
    
    def parse(self, file_path: str, content: str) -> ParseResult:
        """
        Parse RPG source code.
        
        Args:
            file_path: Path to RPG file
            content: RPG source code
            
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
            
            # Detect RPG format (fixed or free)
            is_free_format = self._detect_free_format(content)
            result.metadata['format'] = 'free' if is_free_format else 'fixed'
            
            # Parse RPG structure
            if is_free_format:
                self._parse_free_format(content, result)
            else:
                self._parse_fixed_format(content, result)
            
            # Calculate complexity
            result.complexity_score = self._calculate_complexity(result.nodes)
            
            result.success = True
            logger.info(f"Successfully parsed RPG file {file_path}: {len(result.nodes)} nodes")
            
        except Exception as e:
            logger.error(f"Failed to parse RPG file {file_path}: {e}")
            result.errors.append(str(e))
            result.success = False
        
        return result
    
    def _detect_free_format(self, content: str) -> bool:
        """Detect if RPG code is in free format."""
        # Free format RPG typically has **FREE directive
        return '**FREE' in content.upper() or '**free' in content
    
    def _parse_free_format(self, content: str, result: ParseResult) -> None:
        """Parse free-format RPG code."""
        lines = content.split('\n')
        
        # Parse procedures
        proc_pattern = re.compile(
            r'^\s*dcl-proc\s+(\w+)',
            re.IGNORECASE
        )
        
        for i, line in enumerate(lines, 1):
            # Procedures
            match = proc_pattern.search(line)
            if match:
                proc_name = match.group(1)
                node = CodeNode(
                    node_type=NodeType.PROCEDURE,
                    name=proc_name,
                    line_start=i,
                    line_end=i
                )
                result.nodes.append(node)
            
            # Subroutines
            if re.search(r'^\s*begsr\s+(\w+)', line, re.IGNORECASE):
                match = re.search(r'begsr\s+(\w+)', line, re.IGNORECASE)
                if match:
                    subr_name = match.group(1)
                    node = CodeNode(
                        node_type=NodeType.SUBROUTINE,
                        name=subr_name,
                        line_start=i,
                        line_end=i
                    )
                    result.nodes.append(node)
    
    def _parse_fixed_format(self, content: str, result: ParseResult) -> None:
        """Parse fixed-format RPG code."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) < 6:
                continue
            
            # Get specification type from position 6 (0-indexed position 5)
            spec_type = line[5].upper() if len(line) > 5 else ''
            
            if spec_type == 'F':
                # File specification
                self._parse_file_spec(line, i, result)
            elif spec_type == 'D':
                # Data specification
                self._parse_data_spec(line, i, result)
            elif spec_type == 'C':
                # Calculation specification
                self._parse_calc_spec(line, i, result)
            elif spec_type == 'O':
                # Output specification
                self._parse_output_spec(line, i, result)
    
    def _parse_file_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG file specification."""
        # File name is typically in positions 7-16
        if len(line) >= 16:
            file_name = line[6:16].strip()
            if file_name:
                node = CodeNode(
                    node_type=NodeType.FILE_SPEC,
                    name=file_name,
                    line_start=line_num,
                    line_end=line_num
                )
                result.nodes.append(node)
                result.metadata.setdefault('files', []).append(file_name)
    
    def _parse_data_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG data specification."""
        # Data name is typically in positions 7-21
        if len(line) >= 21:
            data_name = line[6:21].strip()
            if data_name:
                node = CodeNode(
                    node_type=NodeType.DATA_SPEC,
                    name=data_name,
                    line_start=line_num,
                    line_end=line_num
                )
                result.nodes.append(node)
    
    def _parse_calc_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG calculation specification."""
        # Look for subroutine definitions (BEGSR)
        if 'BEGSR' in line.upper():
            # Subroutine name is in Factor 1 (positions 12-25)
            if len(line) >= 25:
                subr_name = line[11:25].strip()
                if subr_name:
                    node = CodeNode(
                        node_type=NodeType.SUBROUTINE,
                        name=subr_name,
                        line_start=line_num,
                        line_end=line_num
                    )
                    result.nodes.append(node)
    
    def _parse_output_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG output specification."""
        # Output specs define report formatting
        if len(line) >= 16:
            output_name = line[6:16].strip()
            if output_name:
                node = CodeNode(
                    node_type=NodeType.OUTPUT_SPEC,
                    name=output_name,
                    line_start=line_num,
                    line_end=line_num
                )
                result.nodes.append(node)
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is an RPG comment."""
        # Fixed format: * in position 7 (index 6)
        if len(line) >= 7 and line[6] == '*':
            return True
        # Free format: // comments
        stripped = line.strip()
        return stripped.startswith('//') or stripped.startswith('*')

# Made with Bob
