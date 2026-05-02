# for IBM hackathon
"""
Dependency Analyzer

Analyzes code dependencies and builds dependency graphs.
"""

import logging
from typing import List, Dict, Set, Any, Optional
from collections import defaultdict

from app.parsers.base_parser import ParseResult
from app.schemas.common import DependencyNode, DependencyEdge, DependencyGraph

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes code dependencies and relationships."""
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.edges: List[DependencyEdge] = []
    
    def analyze(self, parse_results: List[ParseResult]) -> DependencyGraph:
        """
        Analyze dependencies across multiple files.
        
        Args:
            parse_results: List of parsed files
            
        Returns:
            DependencyGraph with nodes and edges
        """
        self.nodes = {}
        self.edges = []
        
        # Build nodes from files
        for result in parse_results:
            self._add_file_node(result)
        
        # Build edges from dependencies
        for result in parse_results:
            self._add_dependency_edges(result)
        
        # Calculate metrics
        self._calculate_metrics()
        
        graph = DependencyGraph(
            nodes=list(self.nodes.values()),
            edges=self.edges
        )
        
        logger.info(
            f"Built dependency graph: {len(graph.nodes)} nodes, "
            f"{len(graph.edges)} edges"
        )
        
        return graph
    
    def _add_file_node(self, parse_result: ParseResult) -> None:
        """Add a file as a node in the dependency graph."""
        node_id = self._get_node_id(parse_result.file_path)
        
        # Determine node type based on file content
        node_type = self._determine_node_type(parse_result)
        
        node = DependencyNode(
            id=node_id,
            name=self._get_file_name(parse_result.file_path),
            type=node_type,
            file_path=parse_result.file_path,
            metadata={
                "language": parse_result.language,
                "lines_of_code": parse_result.lines_of_code,
                "complexity_score": parse_result.complexity_score,
                "imports": parse_result.imports,
                "dependencies": parse_result.dependencies,
                "node_count": len(parse_result.nodes)
            }
        )
        
        self.nodes[node_id] = node
    
    def _add_dependency_edges(self, parse_result: ParseResult) -> None:
        """
        Add dependency edges from a file to its dependencies.
        
        Uses parsed imports and dependencies for accurate edge creation.
        """
        source_id = self._get_node_id(parse_result.file_path)
        
        # Track unique dependencies to avoid duplicate edges
        seen_targets: Set[str] = set()
        
        # Process parsed imports (more reliable than dependencies list)
        for imp in parse_result.imports:
            target_id = self._find_dependency_node(imp)
            
            if target_id and target_id != source_id and target_id not in seen_targets:
                edge = DependencyEdge(
                    source=source_id,
                    target=target_id,
                    type="imports",
                    weight=1.0
                )
                self.edges.append(edge)
                seen_targets.add(target_id)
        
        # Process explicit dependencies (from COBOL COPY, JCL EXEC, etc.)
        for dep in parse_result.dependencies:
            target_id = self._find_dependency_node(dep)
            
            if target_id and target_id != source_id and target_id not in seen_targets:
                # Determine edge type based on dependency nature
                edge_type = "depends_on"
                if any(keyword in dep.lower() for keyword in ['copy', 'include']):
                    edge_type = "includes"
                elif any(keyword in dep.lower() for keyword in ['call', 'exec']):
                    edge_type = "calls"
                
                edge = DependencyEdge(
                    source=source_id,
                    target=target_id,
                    type=edge_type,
                    weight=1.0
                )
                self.edges.append(edge)
                seen_targets.add(target_id)
        
        # Extract dependencies from parsed nodes (method calls, class references)
        for node in parse_result.nodes:
            if node.metadata:
                # Process method calls
                calls = node.metadata.get('calls', [])
                for call in calls:
                    target_id = self._find_dependency_node(call)
                    if target_id and target_id != source_id and target_id not in seen_targets:
                        edge = DependencyEdge(
                            source=source_id,
                            target=target_id,
                            type="calls",
                            weight=0.5  # Lower weight for method-level dependencies
                        )
                        self.edges.append(edge)
                        seen_targets.add(target_id)
    
    def _determine_node_type(self, parse_result: ParseResult) -> str:
        """
        Determine the type of node based on parsed structure.
        
        Uses actual parsed nodes instead of filename guessing.
        """
        if not parse_result.nodes:
            return "module"
        
        # Count node types from parsed structure
        node_type_counts = {}
        for node in parse_result.nodes:
            node_type = node.node_type.value.lower()
            node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
        
        # Determine primary type based on parsed content
        if "class" in node_type_counts:
            return "class"
        elif "interface" in node_type_counts:
            return "interface"
        elif "procedure" in node_type_counts or "subroutine" in node_type_counts:
            return "procedure"
        elif "division" in node_type_counts or "program" in node_type_counts:
            return "program"
        elif "job" in node_type_counts or "step" in node_type_counts:
            return "job"
        elif "function" in node_type_counts or "method" in node_type_counts:
            # If only functions/methods, it's a module
            return "module"
        else:
            return "module"
    
    def _get_node_id(self, file_path: str) -> str:
        """Generate a unique node ID from file path."""
        # Use file path as ID, normalized
        return file_path.replace('\\', '/').replace(' ', '_')
    
    def _get_file_name(self, file_path: str) -> str:
        """Extract file name from path."""
        return file_path.split('/')[-1].split('\\')[-1]
    
    def _find_dependency_node(self, dependency: str) -> Optional[str]:
        """
        Find a node ID that matches the dependency using symbol resolution.
        
        Uses proper package/module resolution instead of substring matching.
        """
        if not dependency:
            return None
        
        # Build symbol table for lookup
        symbol_table = self._build_symbol_table()
        
        # Try exact symbol match first
        if dependency in symbol_table:
            return symbol_table[dependency]
        
        # Try package-qualified match
        parts = dependency.split('.')
        for i in range(len(parts)):
            partial_name = '.'.join(parts[i:])
            if partial_name in symbol_table:
                return symbol_table[partial_name]
        
        # Try class/module name match (last component)
        if parts:
            simple_name = parts[-1]
            if simple_name in symbol_table:
                return symbol_table[simple_name]
        
        # Try file path match as fallback
        for node_id, node in self.nodes.items():
            # Match by file path components
            if dependency in node.file_path:
                return node_id
            
            # Match by normalized names
            normalized_dep = dependency.replace('.', '/').replace('\\', '/')
            normalized_path = node.file_path.replace('\\', '/')
            if normalized_dep in normalized_path:
                return node_id
        
        return None
    
    def _build_symbol_table(self) -> Dict[str, str]:
        """
        Build a symbol table mapping fully qualified names to node IDs.
        
        Returns:
            Dictionary mapping symbol names to node IDs
        """
        symbol_table = {}
        
        for node_id, node in self.nodes.items():
            # Add file name without extension
            file_name = node.name
            base_name = file_name
            
            if '.' in file_name:
                base_name = file_name.rsplit('.', 1)[0]
                symbol_table[base_name] = node_id
            
            symbol_table[file_name] = node_id
            
            # Add package-qualified names from metadata
            if node.metadata:
                package = node.metadata.get('package')
                if package:
                    qualified_name = f"{package}.{base_name}"
                    symbol_table[qualified_name] = node_id
                
                # Add class names
                classes = node.metadata.get('classes', [])
                for cls in classes:
                    symbol_table[cls] = node_id
                    if package:
                        symbol_table[f"{package}.{cls}"] = node_id
        
        return symbol_table
    
    def _calculate_metrics(self) -> None:
        """Calculate dependency metrics for each node."""
        # Count incoming and outgoing edges
        incoming: Dict[str, int] = defaultdict(int)
        outgoing: Dict[str, int] = defaultdict(int)
        
        for edge in self.edges:
            outgoing[edge.source] += 1
            incoming[edge.target] += 1
        
        # Update node metadata
        for node_id, node in self.nodes.items():
            node.metadata["incoming_dependencies"] = incoming[node_id]
            node.metadata["outgoing_dependencies"] = outgoing[node_id]
            node.metadata["total_dependencies"] = incoming[node_id] + outgoing[node_id]
    
    def get_entry_points(self) -> List[DependencyNode]:
        """
        Get entry point nodes (nodes with no incoming dependencies).
        
        Returns:
            List of entry point nodes
        """
        incoming_nodes = {edge.target for edge in self.edges}
        entry_points = [
            node for node_id, node in self.nodes.items()
            if node_id not in incoming_nodes
        ]
        return entry_points
    
    def get_leaf_nodes(self) -> List[DependencyNode]:
        """
        Get leaf nodes (nodes with no outgoing dependencies).
        
        Returns:
            List of leaf nodes
        """
        outgoing_nodes = {edge.source for edge in self.edges}
        leaf_nodes = [
            node for node_id, node in self.nodes.items()
            if node_id not in outgoing_nodes
        ]
        return leaf_nodes
    
    def get_highly_coupled_nodes(self, threshold: int = 5) -> List[DependencyNode]:
        """
        Get nodes with high coupling (many dependencies).
        
        Args:
            threshold: Minimum number of dependencies to be considered highly coupled
            
        Returns:
            List of highly coupled nodes
        """
        highly_coupled = [
            node for node in self.nodes.values()
            if node.metadata.get("total_dependencies", 0) >= threshold
        ]
        return sorted(
            highly_coupled,
            key=lambda n: n.metadata.get("total_dependencies", 0),
            reverse=True
        )
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.
        
        Returns:
            List of circular dependency chains
        """
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node_id: str, path: List[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            # Get outgoing edges
            for edge in self.edges:
                if edge.source == node_id:
                    target = edge.target
                    
                    if target not in visited:
                        dfs(target, path.copy())
                    elif target in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(target)
                        cycle = path[cycle_start:] + [target]
                        if cycle not in cycles:
                            cycles.append(cycle)
            
            rec_stack.remove(node_id)
        
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles

# Made with Bob
