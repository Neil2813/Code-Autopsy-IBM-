# for IBM hackathon
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
        """Parse fixed-format RPG code with improved accuracy."""
        lines = content.split('\n')
        
        # Track subroutines for accurate line_end
        subroutines = []
        
        for i, line in enumerate(lines, 1):
            # Skip blank lines and comments
            if len(line) < 6 or self._is_comment_line(line):
                continue
            
            # Get specification type from position 6 (0-indexed position 5)
            spec_type = line[5].upper() if len(line) > 5 else ''
            
            if spec_type == 'H':
                # Header specification (control options)
                self._parse_header_spec(line, i, result)
            elif spec_type == 'F':
                # File specification
                self._parse_file_spec(line, i, result)
            elif spec_type == 'E':
                # Extension specification (arrays/tables)
                self._parse_extension_spec(line, i, result)
            elif spec_type == 'L':
                # Line specification (compile-time arrays)
                self._parse_line_spec(line, i, result)
            elif spec_type == 'I':
                # Input specification
                self._parse_input_spec(line, i, result)
            elif spec_type == 'D':
                # Data specification
                self._parse_data_spec(line, i, result)
            elif spec_type == 'C':
                # Calculation specification
                self._parse_calc_spec(line, i, result, subroutines)
            elif spec_type == 'O':
                # Output specification
                self._parse_output_spec(line, i, result)
        
        # Update subroutine line_end values
        self._finalize_subroutine_boundaries(subroutines, len(lines))
    
    def _parse_file_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG file specification with enhanced details."""
        # File name is in positions 7-16 (columns 7-16)
        if len(line) >= 16:
            file_name = line[6:16].strip()
            if file_name:
                node = CodeNode(
                    node_type=NodeType.FILE_SPEC,
                    name=file_name,
                    line_start=line_num,
                    line_end=line_num
                )
                
                # Extract file type (position 17: I=Input, O=Output, U=Update, C=Combined)
                if len(line) > 16:
                    file_type = line[16].upper()
                    if file_type in ['I', 'O', 'U', 'C']:
                        node.metadata['file_type'] = {
                            'I': 'Input', 'O': 'Output', 'U': 'Update', 'C': 'Combined'
                        }[file_type]
                
                # Extract file designation (position 18: P=Primary, S=Secondary, etc.)
                if len(line) > 17:
                    designation = line[17].upper()
                    if designation in ['P', 'S', 'R', 'T', 'F']:
                        node.metadata['designation'] = designation
                
                # Extract device (positions 40-46)
                if len(line) >= 46:
                    device = line[39:46].strip()
                    if device:
                        node.metadata['device'] = device
                
                result.nodes.append(node)
                result.metadata.setdefault('files', []).append({
                    'name': file_name,
                    'line': line_num,
                    'type': node.metadata.get('file_type', 'Unknown')
                })
    
    def _parse_data_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG data specification with type information."""
        # Data name is in positions 7-21 (columns 7-21)
        if len(line) >= 21:
            data_name = line[6:21].strip()
            if data_name:
                node = CodeNode(
                    node_type=NodeType.DATA_SPEC,
                    name=data_name,
                    line_start=line_num,
                    line_end=line_num
                )
                
                # Extract data type (positions 40-42)
                if len(line) >= 42:
                    data_type = line[39:42].strip()
                    if data_type:
                        node.metadata['data_type'] = data_type
                
                # Extract length (positions 33-39)
                if len(line) >= 39:
                    length_str = line[32:39].strip()
                    if length_str and length_str.isdigit():
                        node.metadata['length'] = int(length_str)
                
                # Check if it's a constant (position 24: C)
                if len(line) > 23 and line[23].upper() == 'C':
                    node.node_type = NodeType.CONSTANT
                    node.metadata['is_constant'] = True
                
                # Check if it's a standalone field (position 24: S)
                if len(line) > 23 and line[23].upper() == 'S':
                    node.metadata['standalone'] = True
                
                result.nodes.append(node)
    
    def _parse_calc_spec(self, line: str, line_num: int, result: ParseResult, subroutines: list) -> None:
        """Parse RPG calculation specification with operation detection."""
        # Look for subroutine definitions (BEGSR)
        if 'BEGSR' in line.upper():
            # Subroutine name is in Factor 1 (positions 12-25)
            if len(line) >= 25:
                subr_name = line[11:25].strip()
                if not subr_name:
                    # Sometimes name is in Factor 2 (positions 36-49)
                    if len(line) >= 49:
                        subr_name = line[35:49].strip()
                
                if subr_name:
                    node = CodeNode(
                        node_type=NodeType.SUBROUTINE,
                        name=subr_name,
                        line_start=line_num,
                        line_end=line_num  # Will be updated later
                    )
                    result.nodes.append(node)
                    subroutines.append((line_num, subr_name, node))
        
        # Look for ENDSR (end of subroutine)
        elif 'ENDSR' in line.upper():
            if subroutines:
                # Update the last subroutine's line_end
                last_subr = subroutines[-1]
                last_subr[2].line_end = line_num
        
        # Extract operation code (positions 28-37)
        if len(line) >= 37:
            operation = line[27:37].strip().upper()
            if operation:
                # Track EXSR (execute subroutine) calls
                if operation == 'EXSR':
                    if len(line) >= 49:
                        called_subr = line[35:49].strip()
                        if called_subr:
                            result.metadata.setdefault('subroutine_calls', []).append({
                                'from_line': line_num,
                                'subroutine': called_subr
                            })
    
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
        """Check if line is an RPG comment (enhanced detection)."""
        if not line:
            return False
        
        stripped = line.strip()
        
        # Empty lines
        if not stripped:
            return False
        
        # Fixed format: * in position 7 (index 6)
        if len(line) >= 7:
            char_at_6 = line[6]
            if char_at_6 == '*':
                return True
            # Also check for comment indicator in position 7
            if char_at_6 in ('/', '*'):
                return True
        
        # Free format: // or * at start
        if stripped.startswith('//') or stripped.startswith('*'):
            return True
        
        # Compiler directives (not really comments but treated similarly)
        if stripped.startswith('/'):
            return True
        
        return False
    
    def _parse_header_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG header specification (control options)."""
        # Extract control options from positions 7-80
        if len(line) > 6:
            options = line[6:].strip()
            if options:
                result.metadata.setdefault('control_options', []).append({
                    'line': line_num,
                    'options': options
                })
    
    def _parse_extension_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG extension specification (arrays/tables)."""
        # Array/table name in positions 27-32
        if len(line) >= 32:
            name = line[26:32].strip()
            if name:
                node = CodeNode(
                    node_type=NodeType.DATA_SPEC,
                    name=name,
                    line_start=line_num,
                    line_end=line_num
                )
                node.metadata['spec_type'] = 'extension'
                result.nodes.append(node)
    
    def _parse_line_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG line specification (compile-time arrays)."""
        # This marks compile-time array data
        result.metadata.setdefault('compile_time_arrays', []).append(line_num)
    
    def _parse_input_spec(self, line: str, line_num: int, result: ParseResult) -> None:
        """Parse RPG input specification."""
        # File name in positions 7-16
        if len(line) >= 16:
            file_name = line[6:16].strip()
            if file_name:
                # Field name in positions 53-58
                if len(line) >= 58:
                    field_name = line[52:58].strip()
                    if field_name:
                        result.metadata.setdefault('input_fields', []).append({
                            'file': file_name,
                            'field': field_name,
                            'line': line_num
                        })
    
    def _finalize_subroutine_boundaries(self, subroutines: list, total_lines: int) -> None:
        """Update subroutine line_end values based on ENDSR or next BEGSR."""
        for idx, (start_line, name, node) in enumerate(subroutines):
            if node.line_end == start_line:  # Not yet updated by ENDSR
                # Find next subroutine or end of file
                if idx + 1 < len(subroutines):
                    node.line_end = subroutines[idx + 1][0] - 1
                else:
                    node.line_end = total_lines

# Made with Bob
