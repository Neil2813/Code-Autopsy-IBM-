"""
Complexity Analyzer

Analyzes code complexity using various metrics.
"""

import logging
import re
from typing import Dict, Any

from app.parsers.base_parser import ParseResult, CodeNode

logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """Analyzes code complexity metrics."""
    
    def analyze(self, parse_result: ParseResult, content: str) -> Dict[str, Any]:
        """
        Analyze code complexity using parser-aware methods.
        
        Args:
            parse_result: Parsed code structure
            content: Original source code
            
        Returns:
            Dictionary with complexity metrics
        """
        # Use parser-aware methods when possible
        metrics = {
            "cyclomatic_complexity": self._calculate_cyclomatic_from_nodes(parse_result),
            "cognitive_complexity": self._calculate_cognitive_from_nodes(parse_result, content),
            "nesting_depth": self._calculate_nesting_from_nodes(parse_result),
            "method_count": self._count_methods(parse_result),
            "class_count": self._count_classes(parse_result),
            "average_method_length": self._calculate_average_method_length(parse_result),
            "halstead_volume": self._calculate_halstead_volume(parse_result, content),
            "maintainability_index": 0.0  # Calculated below
        }
        
        # Calculate maintainability index with Halstead volume
        metrics["maintainability_index"] = self._calculate_maintainability_index(
            parse_result, metrics
        )
        
        logger.info(
            f"Complexity analysis for {parse_result.file_path}: "
            f"cyclomatic={metrics['cyclomatic_complexity']}, "
            f"cognitive={metrics['cognitive_complexity']}, "
            f"MI={metrics['maintainability_index']}"
        )
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        """
        Calculate cyclomatic complexity using parsed structure.
        
        Cyclomatic complexity = number of decision points + 1
        Falls back to regex-based counting if parse data unavailable.
        """
        # Count decision points from content (fallback method)
        decision_keywords = [
            r'\bif\b', r'\belse\s+if\b', r'\belif\b', r'\bwhile\b',
            r'\bfor\b', r'\bcase\b', r'\bcatch\b', r'\b&&\b', r'\band\b',
            r'\b\|\|\b', r'\bor\b', r'\b\?\s*:', r'\bwhen\b'
        ]
        
        complexity = 1  # Base complexity
        
        for keyword in decision_keywords:
            matches = re.findall(keyword, content, re.IGNORECASE)
            complexity += len(matches)
        
        return complexity
    
    def _calculate_cyclomatic_from_nodes(self, parse_result: ParseResult) -> int:
        """
        Calculate cyclomatic complexity from parsed nodes.
        
        More accurate than regex-based approach.
        """
        complexity = 1  # Base complexity
        
        for node in parse_result.nodes:
            # Count decision points in each node
            if node.complexity:
                complexity += node.complexity
        
        # If no node-level complexity, fall back to counting control structures
        if complexity == 1 and parse_result.nodes:
            for node in parse_result.nodes:
                node_type = node.node_type.value.lower()
                # Count control flow structures
                if node_type in ['if', 'while', 'for', 'case', 'catch', 'when']:
                    complexity += 1
        
        return max(1, complexity)
    
    def _calculate_cognitive_complexity(self, content: str) -> int:
        """
        Calculate cognitive complexity (fallback regex-based method).
        
        Cognitive complexity measures how difficult code is to understand.
        """
        cognitive = 0
        nesting_level = 0
        
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            # Increase nesting for blocks
            if re.search(r'\b(if|while|for|try|catch)\b', stripped, re.IGNORECASE):
                cognitive += (1 + nesting_level)
                if '{' in line or ':' in line:
                    nesting_level += 1
            
            # Decrease nesting
            if '}' in line or re.search(r'\bend\b', stripped, re.IGNORECASE):
                nesting_level = max(0, nesting_level - 1)
            
            # Add for logical operators
            cognitive += len(re.findall(r'\b(and|or)\b', stripped, re.IGNORECASE))
        
        return cognitive
    
    def _calculate_cognitive_from_nodes(self, parse_result: ParseResult, content: str) -> int:
        """
        Calculate cognitive complexity from parsed nodes.
        
        Uses node structure to accurately measure cognitive load.
        Falls back to regex method if nodes don't provide enough info.
        """
        if not parse_result.nodes:
            return self._calculate_cognitive_complexity(content)
        
        cognitive = 0
        
        # Calculate cognitive complexity based on node nesting and control flow
        for node in parse_result.nodes:
            node_type = node.node_type.value.lower()
            
            # Control flow structures increase cognitive load
            if node_type in ['if', 'while', 'for', 'switch', 'case', 'catch', 'when']:
                # Add base complexity plus nesting penalty
                nesting_penalty = self._get_node_nesting_level(node, parse_result.nodes)
                cognitive += (1 + nesting_penalty)
            
            # Recursion and callbacks add cognitive load
            if node_type in ['function', 'method'] and node.metadata:
                if node.metadata.get('is_recursive'):
                    cognitive += 1
                if node.metadata.get('has_callbacks'):
                    cognitive += 1
        
        # If we got no complexity from nodes, fall back to regex
        if cognitive == 0:
            return self._calculate_cognitive_complexity(content)
        
        return cognitive
    
    def _get_node_nesting_level(self, node: CodeNode, all_nodes: list) -> int:
        """Calculate nesting level of a node within its parent hierarchy."""
        level = 0
        current = node
        
        # Count parent nodes
        for potential_parent in all_nodes:
            if (potential_parent.line_start < current.line_start and
                potential_parent.line_end > current.line_end):
                level += 1
        
        return level
    
    def _calculate_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth (fallback regex method)."""
        max_depth = 0
        current_depth = 0
        
        for char in content:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _calculate_nesting_from_nodes(self, parse_result: ParseResult) -> int:
        """
        Calculate maximum nesting depth from parsed nodes.
        
        More accurate than character-based counting.
        """
        if not parse_result.nodes:
            return 0
        
        max_depth = 0
        
        for node in parse_result.nodes:
            depth = self._get_node_nesting_level(node, parse_result.nodes)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_halstead_volume(self, parse_result: ParseResult, content: str) -> float:
        """
        Calculate Halstead volume metric.
        
        Volume = (n1 + n2) * log2(N1 + N2)
        where:
        - n1 = number of distinct operators
        - n2 = number of distinct operands
        - N1 = total number of operators
        - N2 = total number of operands
        """
        import math
        
        # Define operators for different languages
        operators = {
            '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
            '&&', '||', '!', '&', '|', '^', '~', '<<', '>>',
            '++', '--', '+=', '-=', '*=', '/=', '%=',
            '.', '->', '::', '?', ':', ',', ';',
            '(', ')', '[', ']', '{', '}',
            'if', 'else', 'while', 'for', 'switch', 'case', 'return',
            'break', 'continue', 'throw', 'try', 'catch', 'finally'
        }
        
        # Extract tokens from content
        # This is a simplified tokenization
        tokens = re.findall(r'\b\w+\b|[+\-*/%=<>!&|^~]+|[()[\]{}.,;:]', content)
        
        distinct_operators = set()
        distinct_operands = set()
        total_operators = 0
        total_operands = 0
        
        for token in tokens:
            if token in operators or not token.isalnum():
                distinct_operators.add(token)
                total_operators += 1
            elif token.isalnum():
                distinct_operands.add(token)
                total_operands += 1
        
        n1 = len(distinct_operators)
        n2 = len(distinct_operands)
        N1 = total_operators
        N2 = total_operands
        
        # Calculate volume
        if n1 + n2 == 0:
            return 0.0
        
        vocabulary = n1 + n2
        length = N1 + N2
        
        if vocabulary <= 0 or length <= 0:
            return 0.0
        
        volume = length * math.log2(vocabulary)
        return round(volume, 2)
    
    def _count_methods(self, parse_result: ParseResult) -> int:
        """Count number of methods/functions."""
        method_types = ['method', 'function', 'procedure', 'subroutine']
        return sum(
            1 for node in parse_result.nodes
            if node.node_type.value in method_types
        )
    
    def _count_classes(self, parse_result: ParseResult) -> int:
        """Count number of classes."""
        return sum(
            1 for node in parse_result.nodes
            if node.node_type.value == 'class'
        )
    
    def _calculate_average_method_length(self, parse_result: ParseResult) -> float:
        """Calculate average method length in lines."""
        method_types = ['method', 'function', 'procedure', 'subroutine']
        method_nodes = [
            node for node in parse_result.nodes
            if node.node_type.value in method_types
        ]
        
        if not method_nodes:
            return 0.0
        
        total_lines = sum(
            node.line_end - node.line_start + 1
            for node in method_nodes
        )
        
        return total_lines / len(method_nodes)
    
    def _calculate_maintainability_index(
        self,
        parse_result: ParseResult,
        metrics: Dict[str, Any]
    ) -> float:
        """
        Calculate maintainability index (0-100).
        
        Higher is better. Based on Microsoft's formula:
        MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
        
        Where:
        - HV = Halstead Volume
        - CC = Cyclomatic Complexity
        - LOC = Lines of Code
        """
        import math
        
        loc = parse_result.lines_of_code
        cc = metrics.get("cyclomatic_complexity", 1)
        hv = metrics.get("halstead_volume", 0)
        
        if loc == 0:
            return 100.0
        
        # Full Microsoft formula with Halstead volume
        try:
            if hv > 0:
                mi = 171 - 5.2 * math.log(hv) - 0.23 * cc - 16.2 * math.log(loc)
            else:
                # Fallback to simplified formula if Halstead volume unavailable
                mi = 171 - 5.2 * math.log(max(loc, 1)) - 0.23 * cc
        except (ValueError, ZeroDivisionError):
            # Handle edge cases
            mi = 171 - 0.23 * cc - 16.2 * math.log(max(loc, 1))
        
        # Normalize to 0-100 scale
        mi = max(0, min(100, mi))
        
        return round(mi, 2)
    
    def get_complexity_rating(self, complexity: int) -> str:
        """
        Get human-readable complexity rating.
        
        Args:
            complexity: Complexity score
            
        Returns:
            Rating string
        """
        if complexity <= 5:
            return "low"
        elif complexity <= 10:
            return "moderate"
        elif complexity <= 20:
            return "high"
        else:
            return "very_high"
    
    def get_maintainability_rating(self, mi: float) -> str:
        """
        Get human-readable maintainability rating.
        
        Args:
            mi: Maintainability index (0-100)
            
        Returns:
            Rating string
        """
        if mi >= 80:
            return "excellent"
        elif mi >= 60:
            return "good"
        elif mi >= 40:
            return "fair"
        elif mi >= 20:
            return "poor"
        else:
            return "critical"

# Made with Bob
