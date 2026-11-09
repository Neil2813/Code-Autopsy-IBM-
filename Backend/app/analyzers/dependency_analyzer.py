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

        # Build symbol table ONCE — avoids O(n²) per-edge rebuild (§3.3)
        symbol_table = self._build_symbol_table()

        # Build edges from dependencies
        for result in parse_results:
            self._add_dependency_edges(result, symbol_table)

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

    def detect_dead_code(self, parse_results: List[ParseResult]) -> List[Dict[str, Any]]:
        """
        §4.7 Dead Code Detection: identify functions/methods that are defined
        but never called anywhere in the analyzed codebase.

        Returns a list of risk-shaped dicts ready to be appended to state["risks"].
        """
        # Collect all defined symbol names
        defined: Dict[str, Dict[str, Any]] = {}  # symbol -> {file_path, line}
        for result in parse_results:
            for node in result.nodes:
                ntype = node.node_type.value.lower()
                if ntype in ("function", "method", "procedure", "subroutine"):
                    defined[node.name] = {
                        "file_path": result.file_path,
                        "line_start": node.line_start,
                        "line_end": node.line_end,
                    }

        # Collect all call references from metadata
        called: Set[str] = set()
        for result in parse_results:
            for node in result.nodes:
                if node.metadata:
                    for call in node.metadata.get("calls", []):
                        # Strip class/module prefix for simple name match
                        called.add(call.split(".")[-1])

        # Entry-point names are exempt (never "called" by internal code)
        incoming_targets = {edge.target for edge in self.edges}
        entry_point_files = {
            node.file_path for nid, node in self.nodes.items()
            if nid not in incoming_targets
        }

        dead: List[Dict[str, Any]] = []
        for symbol, info in defined.items():
            if symbol in called:
                continue
            if info["file_path"] in entry_point_files:
                continue
            # Common main-like names are exempt
            if symbol.lower() in ("main", "init", "setup", "teardown", "run"):
                continue
            dead.append({
                "title": f"Dead code: `{symbol}` defined but never called",
                "description": (
                    f"The function/method `{symbol}` in `{info['file_path']}` "
                    "is defined but has no detected callers within this codebase. "
                    "It may be safely removed or is unreachable legacy code."
                ),
                "severity": "low",
                "category": "maintainability",
                "affected_files": [{
                    "file_path": info["file_path"],
                    "line_start": info["line_start"],
                    "line_end": info["line_end"],
                    "snippet": symbol,
                }],
                "recommendation": (
                    f"Verify `{symbol}` is not called via reflection or dynamic dispatch "
                    "before deleting. If truly unused, remove it to reduce maintenance surface."
                ),
                "confidence": 0.65,
                "mcp_solution_available": False,
            })

        logger.info(f"Dead code detection: {len(dead)} unused symbols found")
        return dead
    
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
    
    def _add_dependency_edges(self, parse_result: ParseResult, symbol_table: Dict[str, str]) -> None:
        """
        Add dependency edges from a file to its dependencies.

        Accepts a pre-built symbol_table to avoid O(n²) rebuilds (§3.3).
        """
        source_id = self._get_node_id(parse_result.file_path)
        seen_targets: Set[str] = set()

        def _resolve(dep: str) -> Optional[str]:
            """Resolve a dependency name to a node ID using the shared symbol table."""
            if not dep:
                return None
            if dep in symbol_table:
                return symbol_table[dep]
            parts = dep.split(".")
            for i in range(len(parts)):
                partial = ".".join(parts[i:])
                if partial in symbol_table:
                    return symbol_table[partial]
            if parts:
                simple = parts[-1]
                if simple in symbol_table:
                    return symbol_table[simple]
            # Fallback: path substring match
            for node_id, node in self.nodes.items():
                if dep in node.file_path:
                    return node_id
                norm_dep = dep.replace(".", "/")
                if norm_dep in node.file_path.replace("\\", "/"):
                    return node_id
            return None

        for imp in parse_result.imports:
            target_id = _resolve(imp)
            if target_id and target_id != source_id and target_id not in seen_targets:
                self.edges.append(DependencyEdge(source=source_id, target=target_id, type="imports", weight=1.0))
                seen_targets.add(target_id)

        for dep in parse_result.dependencies:
            target_id = _resolve(dep)
            if target_id and target_id != source_id and target_id not in seen_targets:
                edge_type = "includes" if any(k in dep.lower() for k in ("copy", "include")) else \
                            "calls" if any(k in dep.lower() for k in ("call", "exec")) else "depends_on"
                self.edges.append(DependencyEdge(source=source_id, target=target_id, type=edge_type, weight=1.0))
                seen_targets.add(target_id)

        for node in parse_result.nodes:
            if node.metadata:
                for call in node.metadata.get("calls", []):
                    target_id = _resolve(call)
                    if target_id and target_id != source_id and target_id not in seen_targets:
                        self.edges.append(DependencyEdge(source=source_id, target=target_id, type="calls", weight=0.5))
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
        Kept for external callers. Internally, _add_dependency_edges now
        uses the shared symbol table built once in analyze() (§3.3).
        """
        if not dependency:
            return None
        symbol_table = self._build_symbol_table()
        if dependency in symbol_table:
            return symbol_table[dependency]
        parts = dependency.split(".")
        for i in range(len(parts)):
            partial = ".".join(parts[i:])
            if partial in symbol_table:
                return symbol_table[partial]
        if parts and parts[-1] in symbol_table:
            return symbol_table[parts[-1]]
        for node_id, node in self.nodes.items():
            if dependency in node.file_path:
                return node_id
            if dependency.replace(".", "/") in node.file_path.replace("\\", "/"):
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
