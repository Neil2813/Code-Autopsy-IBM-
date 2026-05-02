"""
Base Parser Interface

Abstract base class for all language parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import re


class NodeType(str, Enum):
    """Types of code nodes that can be parsed."""
    
    # Common
    FILE = "file"
    MODULE = "module"
    PACKAGE = "package"
    
    # Object-oriented
    CLASS = "class"
    INTERFACE = "interface"
    METHOD = "method"
    FUNCTION = "function"
    CONSTRUCTOR = "constructor"
    
    # Procedural
    PROCEDURE = "procedure"
    SUBROUTINE = "subroutine"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    
    # Data structures
    VARIABLE = "variable"
    CONSTANT = "constant"
    FIELD = "field"
    PROPERTY = "property"
    
    # COBOL specific
    DIVISION = "division"
    COPYBOOK = "copybook"
    FILE_DESCRIPTOR = "file_descriptor"
    
    # RPG specific
    FILE_SPEC = "file_spec"
    DATA_SPEC = "data_spec"
    CALC_SPEC = "calc_spec"
    OUTPUT_SPEC = "output_spec"
    
    # Mainframe specific
    JOB = "job"
    STEP = "step"
    DD_STATEMENT = "dd_statement"
    
    # Other
    IMPORT = "import"
    ANNOTATION = "annotation"
    COMMENT = "comment"
    UNKNOWN = "unknown"


@dataclass
class CodeNode:
    """Represents a parsed code element."""
    
    node_type: NodeType
    name: str
    line_start: int
    line_end: int
    
    # Optional attributes
    modifiers: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    parent: Optional[str] = None
    children: List['CodeNode'] = field(default_factory=list)
    
    # Metadata
    complexity: Optional[int] = None
    annotations: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "node_type": self.node_type.value,
            "name": self.name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "modifiers": self.modifiers,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "parent": self.parent,
            "children": [child.to_dict() for child in self.children],
            "complexity": self.complexity,
            "annotations": self.annotations,
            "comments": self.comments,
            "metadata": self.metadata
        }


@dataclass
class ParseResult:
    """Result of parsing a source file."""
    
    file_path: str
    language: str
    success: bool
    
    # Parsed structure
    nodes: List[CodeNode] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Metrics
    lines_of_code: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    complexity_score: float = 0.0
    
    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "success": self.success,
            "nodes": [node.to_dict() for node in self.nodes],
            "imports": self.imports,
            "dependencies": self.dependencies,
            "lines_of_code": self.lines_of_code,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "complexity_score": self.complexity_score,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata
        }
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[CodeNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes if node.node_type == node_type]
    
    def get_node_by_name(self, name: str) -> Optional[CodeNode]:
        """Get a node by name."""
        for node in self.nodes:
            if node.name == name:
                return node
        return None


class BaseParser(ABC):
    """
    Abstract base class for language parsers.
    
    All language-specific parsers must inherit from this class
    and implement the parse method.
    """
    
    def __init__(self):
        self.language = "unknown"
    
    @abstractmethod
    def parse(self, file_path: str, content: str) -> ParseResult:
        """
        Parse source code and extract structure.
        
        Args:
            file_path: Path to the source file
            content: Source code content
            
        Returns:
            ParseResult with extracted information
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if parser can handle this file
        """
        pass
    
    def _count_lines(self, content: str) -> tuple[int, int, int]:
        """
        Count lines of code, comments, and blank lines.
        
        Args:
            content: Source code content
            
        Returns:
            Tuple of (code_lines, comment_lines, blank_lines)
        """
        lines = content.split('\n')
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif self._is_comment_line(stripped):
                comment_lines += 1
            else:
                code_lines += 1
        
        return code_lines, comment_lines, blank_lines
    
    @abstractmethod
    def _is_comment_line(self, line: str) -> bool:
        """
        Check if a line is a comment.
        
        Args:
            line: Stripped line content
            
        Returns:
            True if line is a comment
        """
        pass
    
    def _calculate_complexity(self, nodes: List[CodeNode]) -> float:
        """
        Calculate overall complexity score.
        
        Args:
            nodes: List of parsed nodes
            
        Returns:
            Complexity score (0.0 to 1.0)
        """
        if not nodes:
            return 0.0
        
        total_complexity = sum(
            node.complexity or 0
            for node in nodes
            if node.complexity is not None
        )
        
        # Normalize to 0-1 range (assuming max complexity of 100 per node)
        max_possible = len(nodes) * 100
        return min(total_complexity / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def _calculate_cyclomatic_complexity(self, content: str, line_start: int, line_end: int) -> int:
        """
        Calculate cyclomatic complexity for a code block.
        
        Args:
            content: Full source code content
            line_start: Starting line number (1-based)
            line_end: Ending line number (1-based)
            
        Returns:
            Cyclomatic complexity score
        """
        lines = content.split('\n')
        block_lines = lines[line_start-1:line_end]
        block_content = '\n'.join(block_lines)
        
        # Base complexity is 1
        complexity = 1
        
        # Count decision points (language-agnostic patterns)
        decision_keywords = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\belse\s+if\b',
            r'\bfor\b', r'\bwhile\b', r'\bdo\b',
            r'\bcase\b', r'\bwhen\b', r'\bswitch\b',
            r'\bcatch\b', r'\bexcept\b',
            r'\band\b', r'\bor\b', r'\b&&\b', r'\b\|\|\b',
            r'\?', r'\bEVALUATE\b', r'\bPERFORM\b.*\bUNTIL\b'
        ]
        
        for pattern in decision_keywords:
            complexity += len(re.findall(pattern, block_content, re.IGNORECASE))
        
        return complexity
    
    def _find_block_end(self, lines: List[str], start_line: int, open_char: str = '{', close_char: str = '}') -> int:
        """
        Find the ending line of a code block by matching braces/keywords.
        
        Args:
            lines: List of all lines in the file
            start_line: Starting line number (0-based index)
            open_char: Opening character/keyword
            close_char: Closing character/keyword
            
        Returns:
            Ending line number (0-based index)
        """
        depth = 0
        found_open = False
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            
            # Count opening and closing characters
            depth += line.count(open_char)
            depth += line.count(close_char) * -1
            
            if depth > 0:
                found_open = True
            
            if found_open and depth == 0:
                return i
        
        # If no matching close found, return last line
        return len(lines) - 1
    
    def _extract_body_content(self, content: str, line_start: int, line_end: int) -> str:
        """
        Extract the body content between line numbers.
        
        Args:
            content: Full source code content
            line_start: Starting line number (1-based)
            line_end: Ending line number (1-based)
            
        Returns:
            Body content as string
        """
        lines = content.split('\n')
        if line_start < 1 or line_end > len(lines):
            return ""
        
        return '\n'.join(lines[line_start-1:line_end])
    
    def _enrich_node_metadata(self, node: CodeNode, content: str) -> None:
        """
        Enrich a node with additional metadata.
        
        Args:
            node: CodeNode to enrich
            content: Full source code content
        """
        # Calculate complexity if not already set
        if node.complexity is None and node.line_end > node.line_start:
            node.complexity = self._calculate_cyclomatic_complexity(
                content, node.line_start, node.line_end
            )
        
        # Add line count
        node.metadata['line_count'] = node.line_end - node.line_start + 1
        
        # Extract and store body content hash for change detection
        body = self._extract_body_content(content, node.line_start, node.line_end)
        node.metadata['body_hash'] = hash(body)
        node.metadata['body_length'] = len(body)

# Made with Bob
