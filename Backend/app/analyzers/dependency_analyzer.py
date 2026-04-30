"""
Dependency Analyzer

Analyzes code dependencies and builds dependency graphs.
"""

import logging
from typing import List, Dict, Set, Any
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
            language=parse_result.language,
            lines_of_code=parse_result.lines_of_code,
            complexity_score=parse_result.complexity_score,
            metadata={
                "imports": parse_result.imports,
                "dependencies": parse_result.dependencies,
                "node_count": len(parse_result.nodes)
            }
        )
        
        self.nodes[node_id] = node
    
    def _add_dependency_edges(self, parse_result: ParseResult) -> None:
        """Add dependency edges from a file to its dependencies."""
        source_id = self._get_node_id(parse_result.file_path)
        
        # Track unique dependencies to avoid duplicate edges
        seen_targets: Set[str] = set()
        
        for dep in parse_result.dependencies:
            # Try to find matching node
            target_id = self._find_dependency_node(dep)
            
            if target_id and target_id != source_id and target_id not in seen_targets:
                edge = DependencyEdge(
                    source=source_id,
                    target=target_id,
                    type="imports",
                    weight=1.0
                )
                self.edges.append(edge)
                seen_targets.add(target_id)
        
        # Add edges for imports
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
    
    def _determine_node_type(self, parse_result: ParseResult) -> str:
        """Determine the type of node based on parsed content."""
        # Check for specific patterns in nodes
        node_types = [node.node_type.value for node in parse_result.nodes]
        
        if "class" in node_types:
            return "class"
        elif "interface" in node_types:
            return "interface"
        elif "procedure" in node_types or "subroutine" in node_types:
            return "procedure"
        elif "division" in node_types:
            return "program"
        elif "job" in node_types or "step" in node_types:
            return "job"
        else:
            return "module"
    
    def _get_node_id(self, file_path: str) -> str:
        """Generate a unique node ID from file path."""
        # Use file path as ID, normalized
        return file_path.replace('\\', '/').replace(' ', '_')
    
    def _get_file_name(self, file_path: str) -> str:
        """Extract file name from path."""
        return file_path.split('/')[-1].split('\\')[-1]
    
    def _find_dependency_node(self, dependency: str) -> str:
        """Find a node ID that matches the dependency."""
        # Try exact match first
        for node_id, node in self.nodes.items():
            if dependency in node.name or dependency in node.file_path:
                return node_id
        
        # Try partial match
        for node_id, node in self.nodes.items():
            if dependency.split('.')[-1] in node.name:
                return node_id
        
        return None
    
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
