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
            import tree_sitter  # type: ignore[import-untyped]
            import tree_sitter_java  # type: ignore[import-untyped]
            self._tree_sitter_available = True
            logger.info("Tree-sitter Java parser available")
        except ImportError:
            logger.warning("Tree-sitter not available, using fallback parser")
        
        # Try to import javalang
        try:
            import javalang  # type: ignore[import-untyped]
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
            import tree_sitter  # type: ignore[import-untyped]
            import tree_sitter_java  # type: ignore[import-untyped]
            
            # Initialize tree-sitter parser
            parser = tree_sitter.Parser()
            parser.set_language(tree_sitter_java.language())
            
            tree = parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # Extract package
            self._extract_package_tree_sitter(root_node, content, result)
            
            # Extract imports
            self._extract_imports_tree_sitter(root_node, content, result)
            
            # Extract classes and interfaces
            self._extract_classes_tree_sitter(root_node, content, result)
            
            logger.debug(f"Tree-sitter parsed {len(result.nodes)} nodes")
            
        except ImportError:
            logger.debug("Tree-sitter not available, using javalang fallback")
            if self._javalang_available:
                self._parse_with_javalang(content, result)
            else:
                self._parse_with_regex(content, result)
        except Exception as e:
            logger.error(f"Tree-sitter parsing failed: {e}")
            result.warnings.append(f"Tree-sitter parsing failed: {e}")
            if self._javalang_available:
                self._parse_with_javalang(content, result)
            else:
                self._parse_with_regex(content, result)
    
    def _parse_with_javalang(self, content: str, result: ParseResult) -> None:
        """Parse using javalang library (primary parser)."""
        try:
            import javalang  # type: ignore[import-untyped]
            
            tree = javalang.parse.parse(content)
            lines = content.split('\n')
            
            # Extract package
            if tree.package:
                result.metadata['package'] = tree.package.name
            
            # Extract imports
            for imp in tree.imports:
                import_path = imp.path
                result.imports.append(import_path)
                # Add base package to dependencies
                base_package = import_path.split('.')[0]
                if base_package not in result.dependencies:
                    result.dependencies.append(base_package)
                
                # Create import node
                if hasattr(imp, 'position') and imp.position:
                    import_node = CodeNode(
                        node_type=NodeType.IMPORT,
                        name=import_path,
                        line_start=imp.position.line,
                        line_end=imp.position.line
                    )
                    result.nodes.append(import_node)
            
            # Extract classes and interfaces
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                class_node = self._create_class_node_enhanced(node, content, lines)
                result.nodes.append(class_node)
            
            for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
                interface_node = self._create_interface_node_enhanced(node, content, lines)
                result.nodes.append(interface_node)
            
            # Extract enums
            for path, node in tree.filter(javalang.tree.EnumDeclaration):
                enum_node = self._create_enum_node(node, content, lines)
                result.nodes.append(enum_node)
            
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
    
    def _create_class_node_enhanced(self, java_class, content: str, lines: list) -> CodeNode:
        """Create enhanced CodeNode from javalang ClassDeclaration with accurate line_end."""
        modifiers = []
        if hasattr(java_class, 'modifiers'):
            modifiers = [str(m) for m in java_class.modifiers]
        
        line_start = java_class.position.line if hasattr(java_class, 'position') else 0
        
        # Calculate accurate line_end by finding the closing brace
        line_end = self._find_class_end(lines, line_start - 1) + 1
        
        node = CodeNode(
            node_type=NodeType.CLASS,
            name=java_class.name,
            line_start=line_start,
            line_end=line_end,
            modifiers=modifiers
        )
        
        # Add extends information
        if hasattr(java_class, 'extends') and java_class.extends:
            node.metadata['extends'] = java_class.extends.name
            result_deps = node.metadata.setdefault('dependencies', [])
            result_deps.append(java_class.extends.name)
        
        # Add implements information
        if hasattr(java_class, 'implements') and java_class.implements:
            implements_list = [impl.name for impl in java_class.implements]
            node.metadata['implements'] = implements_list
            result_deps = node.metadata.setdefault('dependencies', [])
            result_deps.extend(implements_list)
        
        # Extract fields
        if hasattr(java_class, 'fields'):
            for field in java_class.fields:
                for declarator in field.declarators:
                    field_node = CodeNode(
                        node_type=NodeType.FIELD,
                        name=declarator.name,
                        line_start=field.position.line if hasattr(field, 'position') else 0,
                        line_end=field.position.line if hasattr(field, 'position') else 0,
                        modifiers=[str(m) for m in field.modifiers] if hasattr(field, 'modifiers') else [],
                        return_type=str(field.type.name) if hasattr(field.type, 'name') else 'unknown'
                    )
                    field_node.parent = java_class.name
                    node.children.append(field_node)
        
        # Extract methods
        if hasattr(java_class, 'methods'):
            for method in java_class.methods:
                method_node = self._create_method_node_enhanced(method, content, lines)
                method_node.parent = java_class.name
                node.children.append(method_node)
        
        # Extract constructors
        if hasattr(java_class, 'constructors'):
            for constructor in java_class.constructors:
                ctor_node = self._create_constructor_node(constructor, content, lines)
                ctor_node.parent = java_class.name
                node.children.append(ctor_node)
        
        # Enrich with metadata
        self._enrich_node_metadata(node, content)
        
        return node
    
    def _create_interface_node_enhanced(self, java_interface, content: str, lines: list) -> CodeNode:
        """Create enhanced CodeNode from javalang InterfaceDeclaration."""
        modifiers = []
        if hasattr(java_interface, 'modifiers'):
            modifiers = [str(m) for m in java_interface.modifiers]
        
        line_start = java_interface.position.line if hasattr(java_interface, 'position') else 0
        line_end = self._find_class_end(lines, line_start - 1) + 1
        
        node = CodeNode(
            node_type=NodeType.INTERFACE,
            name=java_interface.name,
            line_start=line_start,
            line_end=line_end,
            modifiers=modifiers
        )
        
        # Add extends information
        if hasattr(java_interface, 'extends') and java_interface.extends:
            extends_list = [ext.name for ext in java_interface.extends]
            node.metadata['extends'] = extends_list
        
        # Extract methods
        if hasattr(java_interface, 'methods'):
            for method in java_interface.methods:
                method_node = self._create_method_node_enhanced(method, content, lines)
                method_node.parent = java_interface.name
                node.children.append(method_node)
        
        self._enrich_node_metadata(node, content)
        
        return node
    
    def _create_method_node_enhanced(self, java_method, content: str, lines: list) -> CodeNode:
        """Create enhanced CodeNode from javalang MethodDeclaration with accurate line_end."""
        modifiers = []
        if hasattr(java_method, 'modifiers'):
            modifiers = [str(m) for m in java_method.modifiers]
        
        return_type = None
        if hasattr(java_method, 'return_type') and java_method.return_type:
            return_type = str(java_method.return_type.name)
        
        parameters = []
        if hasattr(java_method, 'parameters'):
            for param in java_method.parameters:
                param_type = 'unknown'
                if hasattr(param, 'type'):
                    if hasattr(param.type, 'name'):
                        param_type = str(param.type.name)
                    else:
                        param_type = str(param.type)
                
                parameters.append({
                    'name': param.name,
                    'type': param_type
                })
        
        line_start = java_method.position.line if hasattr(java_method, 'position') else 0
        
        # Find method end by looking for closing brace
        line_end = self._find_method_end(lines, line_start - 1) + 1
        
        node = CodeNode(
            node_type=NodeType.METHOD,
            name=java_method.name,
            line_start=line_start,
            line_end=line_end,
            modifiers=modifiers,
            return_type=return_type,
            parameters=parameters
        )
        
        # Add annotations
        if hasattr(java_method, 'annotations') and java_method.annotations:
            node.annotations = [str(ann.name) for ann in java_method.annotations]
        
        # Calculate complexity for method body
        if line_end > line_start:
            node.complexity = self._calculate_cyclomatic_complexity(content, line_start, line_end)
        
        self._enrich_node_metadata(node, content)
        
        return node
    
    def _create_constructor_node(self, java_constructor, content: str, lines: list) -> CodeNode:
        """Create CodeNode from javalang ConstructorDeclaration."""
        modifiers = []
        if hasattr(java_constructor, 'modifiers'):
            modifiers = [str(m) for m in java_constructor.modifiers]
        
        parameters = []
        if hasattr(java_constructor, 'parameters'):
            for param in java_constructor.parameters:
                param_type = 'unknown'
                if hasattr(param, 'type'):
                    if hasattr(param.type, 'name'):
                        param_type = str(param.type.name)
                    else:
                        param_type = str(param.type)
                
                parameters.append({
                    'name': param.name,
                    'type': param_type
                })
        
        line_start = java_constructor.position.line if hasattr(java_constructor, 'position') else 0
        line_end = self._find_method_end(lines, line_start - 1) + 1
        
        node = CodeNode(
            node_type=NodeType.CONSTRUCTOR,
            name=java_constructor.name,
            line_start=line_start,
            line_end=line_end,
            modifiers=modifiers,
            parameters=parameters
        )
        
        if line_end > line_start:
            node.complexity = self._calculate_cyclomatic_complexity(content, line_start, line_end)
        
        self._enrich_node_metadata(node, content)
        
        return node
    
    def _create_enum_node(self, java_enum, content: str, lines: list) -> CodeNode:
        """Create CodeNode from javalang EnumDeclaration."""
        modifiers = []
        if hasattr(java_enum, 'modifiers'):
            modifiers = [str(m) for m in java_enum.modifiers]
        
        line_start = java_enum.position.line if hasattr(java_enum, 'position') else 0
        line_end = self._find_class_end(lines, line_start - 1) + 1
        
        node = CodeNode(
            node_type=NodeType.CLASS,  # Use CLASS type for enums
            name=java_enum.name,
            line_start=line_start,
            line_end=line_end,
            modifiers=modifiers + ['enum']
        )
        
        # Add enum constants
        if hasattr(java_enum, 'body') and java_enum.body:
            constants = [const.name for const in java_enum.body.constants] if hasattr(java_enum.body, 'constants') else []
            node.metadata['enum_constants'] = constants
        
        self._enrich_node_metadata(node, content)
        
        return node
    
    def _find_class_end(self, lines: list, start_idx: int) -> int:
        """Find the ending line of a class/interface by matching braces."""
        return self._find_block_end(lines, start_idx, '{', '}')
    
    def _find_method_end(self, lines: list, start_idx: int) -> int:
        """Find the ending line of a method by matching braces."""
        # Check if it's an abstract method (ends with semicolon)
        for i in range(start_idx, min(start_idx + 3, len(lines))):
            if ';' in lines[i] and '{' not in lines[i]:
                return i
        
        return self._find_block_end(lines, start_idx, '{', '}')
    
    def _extract_package_tree_sitter(self, root_node, content: str, result: ParseResult) -> None:
        """Extract package declaration using tree-sitter."""
        for node in root_node.children:
            if node.type == 'package_declaration':
                package_name = content[node.start_byte:node.end_byte]
                package_name = package_name.replace('package', '').replace(';', '').strip()
                result.metadata['package'] = package_name
                break
    
    def _extract_imports_tree_sitter(self, root_node, content: str, result: ParseResult) -> None:
        """Extract imports using tree-sitter."""
        for node in root_node.children:
            if node.type == 'import_declaration':
                import_text = content[node.start_byte:node.end_byte]
                import_path = import_text.replace('import', '').replace('static', '').replace(';', '').strip()
                result.imports.append(import_path)
                base_package = import_path.split('.')[0]
                if base_package not in result.dependencies:
                    result.dependencies.append(base_package)
    
    def _extract_classes_tree_sitter(self, root_node, content: str, result: ParseResult) -> None:
        """Extract classes and interfaces using tree-sitter."""
        lines = content.split('\n')
        
        def traverse(node):
            if node.type in ['class_declaration', 'interface_declaration', 'enum_declaration']:
                line_start = node.start_point[0] + 1
                line_end = node.end_point[0] + 1
                
                # Extract name
                name = 'Unknown'
                for child in node.children:
                    if child.type == 'identifier':
                        name = content[child.start_byte:child.end_byte]
                        break
                
                node_type = NodeType.CLASS if node.type == 'class_declaration' else \
                           NodeType.INTERFACE if node.type == 'interface_declaration' else \
                           NodeType.CLASS  # enum
                
                code_node = CodeNode(
                    node_type=node_type,
                    name=name,
                    line_start=line_start,
                    line_end=line_end
                )
                
                result.nodes.append(code_node)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a Java comment."""
        return (
            line.startswith('//') or 
            line.startswith('/*') or 
            line.startswith('*') or
            line.endswith('*/')
        )

# Made with Bob
