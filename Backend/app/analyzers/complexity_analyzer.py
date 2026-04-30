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
        Analyze code complexity.
        
        Args:
            parse_result: Parsed code structure
            content: Original source code
            
        Returns:
            Dictionary with complexity metrics
        """
        metrics = {
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(content),
            "cognitive_complexity": self._calculate_cognitive_complexity(content),
            "nesting_depth": self._calculate_nesting_depth(content),
            "method_count": self._count_methods(parse_result),
            "class_count": self._count_classes(parse_result),
            "average_method_length": self._calculate_average_method_length(parse_result),
            "maintainability_index": 0.0  # Placeholder
        }
        
        # Calculate maintainability index
        metrics["maintainability_index"] = self._calculate_maintainability_index(
            parse_result, metrics
        )
        
        logger.info(
            f"Complexity analysis for {parse_result.file_path}: "
            f"cyclomatic={metrics['cyclomatic_complexity']}, "
            f"cognitive={metrics['cognitive_complexity']}"
        )
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        """
        Calculate cyclomatic complexity.
        
        Cyclomatic complexity = number of decision points + 1
        """
        # Count decision points
        decision_keywords = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bwhile\b',
            r'\bfor\b', r'\bcase\b', r'\bcatch\b', r'\band\b',
            r'\bor\b', r'\b\?\b'
        ]
        
        complexity = 1  # Base complexity
        
        for keyword in decision_keywords:
            matches = re.findall(keyword, content, re.IGNORECASE)
            complexity += len(matches)
        
        return complexity
    
    def _calculate_cognitive_complexity(self, content: str) -> int:
        """
        Calculate cognitive complexity.
        
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
    
    def _calculate_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for char in content:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
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
        
        Simplified version for our purposes.
        """
        import math
        
        loc = parse_result.lines_of_code
        cc = metrics["cyclomatic_complexity"]
        
        if loc == 0:
            return 100.0
        
        # Simplified formula
        mi = 171 - 5.2 * math.log(max(loc, 1)) - 0.23 * cc
        
        # Normalize to 0-100
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
