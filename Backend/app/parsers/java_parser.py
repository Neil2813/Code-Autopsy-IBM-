"""
Java Parser

Parser for Java source code using tree-sitter and javalang.
"""

import logging
from typing import List, Dict, Any, Optional
import re

from app.parsers.base_parser import (
    BaseParser, ParseResult, CodeNode, NodeType
)

logger = logging.getLogger(__name__)


class JavaParser(BaseParser):
    """Parser for Java source code."""
    
    def __init__(self):
        super().__init__()
        self.language = "java"
        self._tree_sitter_available = False
        self._javalang_available = False
        
        # Try to import tree-sitter
        try:
            import tree_sitter
            import tree_sitter_java
            self._tree_sitter_available = True
            logger.info("Tree-sitter Java parser available")
        except ImportError:
            logger.warning("Tree-sitter not available, using fallback parser")
        
        # Try to import javalang
        try:
            import javalang
            self._javalang_available = True
            logger.info("Javalang parser available")
        except ImportError:
            logger.warning("Javalang not available")
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a Java file."""
        return file_path.lower().endswith('.java')
    
    def parse(self, file_path: str, content: str) -> ParseResult:
        """
        Parse Java source code.
        
        Args:
            file_path: Path to Java file
            content: Java source code
            
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
            
            # Try tree-sitter first, then javalang, then regex fallback
            if self._tree_sitter_available:
                self._parse_with_tree_sitter(content, result)
            elif self._javalang_available:
                self._parse_with_javalang(content, result)
            else:
                self._parse_with_regex(content, result)
            
            # Calculate complexity
            result.complexity_score = self._calculate_complexity(result.nodes)
            
            result.success = True
            logger.info(f"Successfully parsed {file_path}: {len(result.nodes)} nodes")
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            result.errors.append(str(e))
            result.success = False
        
        return result
    
    def _parse_with_tree_sitter(self, content: str, result: ParseResult) -> None:
        """Parse using tree-sitter (most accurate)."""
        try:
            import tree_sitter
            import tree_sitter_java
            
            # TODO: Implement tree-sitter parsing
            # This requires setting up tree-sitter parser
            logger.debug("Tree-sitter parsing not yet implemented, using fallback")
            self._parse_with_regex(content, result)
            
        except Exception as e:
            logger.error(f"Tree-sitter parsing failed: {e}")
            result.warnings.append(f"Tree-sitter parsing failed: {e}")
            self._parse_with_regex(content, result)
    
    def _parse_with_javalang(self, content: str, result: ParseResult) -> None:
        """Parse using javalang library."""
        try:
            import javalang
            
            tree = javalang.parse.parse(content)
            
            # Extract package
            if tree.package:
                result.metadata['package'] = tree.package.name
            
            # Extract imports
            for imp in tree.imports:
                import_path = imp.path
                result.imports.append(import_path)
                result.dependencies.append(import_path.split('.')[0])
            
            # Extract classes and interfaces
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                class_node = self._create_class_node(node, content)
                result.nodes.append(class_node)
            
            for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
                interface_node = self._create_interface_node(node, content)
                result.nodes.append(interface_node)
            
            logger.debug(f"Javalang parsed {len(result.nodes)} top-level nodes")
            
        except Exception as e:
            logger.error(f"Javalang parsing failed: {e}")
            result.warnings.append(f"Javalang parsing failed: {e}")
            self._parse_with_regex(content, result)
    
    def _parse_with_regex(self, content: str, result: ParseResult) -> None:
        """Parse using regex patterns (fallback)."""
        lines = content.split('\n')
        
        # Extract package
        package_match = re.search(r'package\s+([\w.]+);', content)
        if package_match:
            result.metadata['package'] = package_match.group(1)
        
        # Extract imports
        import_pattern = re.compile(r'import\s+(static\s+)?([\w.]+)(\.\*)?;')
        for match in import_pattern.finditer(content):
            import_path = match.group(2)
            result.imports.append(import_path)
            result.dependencies.append(import_path.split('.')[0])
        
        # Extract classes
        class_pattern = re.compile(
            r'(public|private|protected)?\s*(static|final|abstract)?\s*class\s+(\w+)'
        )
        for i, line in enumerate(lines, 1):
            match = class_pattern.search(line)
            if match:
                class_name = match.group(3)
                modifiers = [m for m in [match.group(1), match.group(2)] if m]
                
                node = CodeNode(
                    node_type=NodeType.CLASS,
                    name=class_name,
                    line_start=i,
                    line_end=i,  # Approximate
                    modifiers=modifiers
                )
                result.nodes.append(node)
        
        # Extract methods
        method_pattern = re.compile(
            r'(public|private|protected)?\s*(static|final|abstract|synchronized)?\s*'
            r'([\w<>\[\]]+)\s+(\w+)\s*\('
        )
        for i, line in enumerate(lines, 1):
            match = method_pattern.search(line)
            if match and 'class' not in line and 'interface' not in line:
                method_name = match.group(4)
                return_type = match.group(3)
                modifiers = [m for m in [match.group(1), match.group(2)] if m]
                
                node = CodeNode(
                    node_type=NodeType.METHOD,
                    name=method_name,
                    line_start=i,
                    line_end=i,  # Approximate
                    modifiers=modifiers,
                    return_type=return_type
                )
                result.nodes.append(node)
        
        logger.debug(f"Regex parsed {len(result.nodes)} nodes")
    
    def _create_class_node(self, java_class, content: str) -> CodeNode:
        """Create CodeNode from javalang ClassDeclaration."""
        modifiers = []
        if hasattr(java_class, 'modifiers'):
            modifiers = [str(m) for m in java_class.modifiers]
        
        node = CodeNode(
            node_type=NodeType.CLASS,
            name=java_class.name,
            line_start=java_class.position.line if hasattr(java_class, 'position') else 0,
            line_end=0,  # Would need to calculate
            modifiers=modifiers
        )
        
        # Extract methods
        if hasattr(java_class, 'methods'):
            for method in java_class.methods:
                method_node = self._create_method_node(method, content)
                method_node.parent = java_class.name
                node.children.append(method_node)
        
        return node
    
    def _create_interface_node(self, java_interface, content: str) -> CodeNode:
        """Create CodeNode from javalang InterfaceDeclaration."""
        modifiers = []
        if hasattr(java_interface, 'modifiers'):
            modifiers = [str(m) for m in java_interface.modifiers]
        
        node = CodeNode(
            node_type=NodeType.INTERFACE,
            name=java_interface.name,
            line_start=java_interface.position.line if hasattr(java_interface, 'position') else 0,
            line_end=0,
            modifiers=modifiers
        )
        
        return node
    
    def _create_method_node(self, java_method, content: str) -> CodeNode:
        """Create CodeNode from javalang MethodDeclaration."""
        modifiers = []
        if hasattr(java_method, 'modifiers'):
            modifiers = [str(m) for m in java_method.modifiers]
        
        return_type = None
        if hasattr(java_method, 'return_type') and java_method.return_type:
            return_type = str(java_method.return_type.name)
        
        parameters = []
        if hasattr(java_method, 'parameters'):
            for param in java_method.parameters:
                parameters.append({
                    'name': param.name,
                    'type': str(param.type.name) if hasattr(param.type, 'name') else 'unknown'
                })
        
        node = CodeNode(
            node_type=NodeType.METHOD,
            name=java_method.name,
            line_start=java_method.position.line if hasattr(java_method, 'position') else 0,
            line_end=0,
            modifiers=modifiers,
            return_type=return_type,
            parameters=parameters
        )
        
        return node
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a Java comment."""
        return (
            line.startswith('//') or 
            line.startswith('/*') or 
            line.startswith('*') or
            line.endswith('*/')
        )

# Made with Bob
