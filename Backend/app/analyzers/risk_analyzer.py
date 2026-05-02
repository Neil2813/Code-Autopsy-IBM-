"""
Risk Analyzer

Analyzes code for security risks, code smells, and modernization blockers.
"""

import logging
import re
from typing import List, Dict, Any
from dataclasses import dataclass

from app.parsers.base_parser import ParseResult, CodeNode
from app.schemas.common import SeverityEnum

logger = logging.getLogger(__name__)


@dataclass
class RiskDetector:
    """Represents a detected risk."""
    
    title: str
    description: str
    severity: SeverityEnum
    category: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str = ""
    remediation: str = ""
    confidence: float = 1.0


class RiskAnalyzer:
    """Analyzes code for various risks and issues."""
    
    def __init__(self):
        self.risk_patterns = self._initialize_risk_patterns()
    
    def analyze(self, parse_result: ParseResult, content: str) -> List[RiskDetector]:
        """
        Analyze parsed code for risks.
        
        Args:
            parse_result: Parsed code structure
            content: Original source code
            
        Returns:
            List of detected risks
        """
        risks = []
        
        # Security risks
        risks.extend(self._detect_security_risks(parse_result, content))
        
        # Code smells
        risks.extend(self._detect_code_smells(parse_result, content))
        
        # Complexity issues
        risks.extend(self._detect_complexity_issues(parse_result))
        
        # Deprecated patterns
        risks.extend(self._detect_deprecated_patterns(parse_result, content))
        
        # Tight coupling
        risks.extend(self._detect_tight_coupling(parse_result))
        
        logger.info(f"Detected {len(risks)} risks in {parse_result.file_path}")
        return risks
    
    def _initialize_risk_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize risk detection patterns."""
        return {
            "security": [
                {
                    "pattern": r"(password|passwd|pwd)\s*=\s*['\"].*['\"]",
                    "title": "Hardcoded Password",
                    "severity": SeverityEnum.CRITICAL,
                    "category": "security"
                },
                {
                    "pattern": r"(api[_-]?key|apikey|secret[_-]?key)\s*=\s*['\"].*['\"]",
                    "title": "Hardcoded API Key",
                    "severity": SeverityEnum.CRITICAL,
                    "category": "security"
                },
                {
                    "pattern": r"eval\s*\(",
                    "title": "Use of eval() Function",
                    "severity": SeverityEnum.HIGH,
                    "category": "security"
                },
                {
                    "pattern": r"exec\s*\(",
                    "title": "Use of exec() Function",
                    "severity": SeverityEnum.HIGH,
                    "category": "security"
                }
            ],
            "code_smell": [
                {
                    "pattern": r"//\s*TODO",
                    "title": "TODO Comment",
                    "severity": SeverityEnum.LOW,
                    "category": "code_smell"
                },
                {
                    "pattern": r"//\s*FIXME",
                    "title": "FIXME Comment",
                    "severity": SeverityEnum.MEDIUM,
                    "category": "code_smell"
                },
                {
                    "pattern": r"//\s*HACK",
                    "title": "HACK Comment",
                    "severity": SeverityEnum.MEDIUM,
                    "category": "code_smell"
                }
            ],
            "deprecated": [
                {
                    "pattern": r"import\s+java\.util\.Date",
                    "title": "Deprecated java.util.Date",
                    "severity": SeverityEnum.MEDIUM,
                    "category": "deprecated"
                },
                {
                    "pattern": r"new\s+Date\s*\(",
                    "title": "Use of deprecated Date constructor",
                    "severity": SeverityEnum.MEDIUM,
                    "category": "deprecated"
                }
            ]
        }
    
    def _detect_security_risks(
        self,
        parse_result: ParseResult,
        content: str
    ) -> List[RiskDetector]:
        """
        Detect security-related risks using parser-aware methods.
        
        Combines AST analysis with pattern matching for better accuracy.
        """
        risks = []
        lines = content.split('\n')
        
        # Use parsed nodes for context-aware detection
        for node in parse_result.nodes:
            # Check for hardcoded credentials in variable assignments
            if node.node_type.value in ['variable', 'field', 'constant']:
                node_name_lower = node.name.lower()
                
                # Check for sensitive variable names
                if any(keyword in node_name_lower for keyword in ['password', 'passwd', 'pwd', 'secret', 'apikey', 'api_key', 'token']):
                    # Extract code snippet
                    snippet_lines = lines[node.line_start-1:node.line_end]
                    snippet = '\n'.join(snippet_lines).strip()
                    
                    # Check if it contains a hardcoded value (not just declaration)
                    if '=' in snippet and any(char in snippet for char in ['"', "'"]):
                        risk = RiskDetector(
                            title="Hardcoded Sensitive Data",
                            description=f"Variable '{node.name}' appears to contain hardcoded sensitive data",
                            severity=SeverityEnum.CRITICAL,
                            category="security",
                            file_path=parse_result.file_path,
                            line_start=node.line_start,
                            line_end=node.line_end,
                            code_snippet=snippet[:200],  # Limit snippet length
                            remediation="Move sensitive data to environment variables or secure configuration",
                            confidence=0.8
                        )
                        risks.append(risk)
            
            # Check for dangerous function calls
            if node.node_type.value in ['function_call', 'method_call']:
                dangerous_functions = ['eval', 'exec', 'system', 'shell_exec', 'passthru']
                if any(func in node.name.lower() for func in dangerous_functions):
                    snippet_lines = lines[node.line_start-1:node.line_end]
                    snippet = '\n'.join(snippet_lines).strip()
                    
                    risk = RiskDetector(
                        title=f"Dangerous Function: {node.name}",
                        description=f"Use of potentially dangerous function '{node.name}' detected",
                        severity=SeverityEnum.HIGH,
                        category="security",
                        file_path=parse_result.file_path,
                        line_start=node.line_start,
                        line_end=node.line_end,
                        code_snippet=snippet[:200],
                        remediation="Avoid using dynamic code execution; use safer alternatives",
                        confidence=0.9
                    )
                    risks.append(risk)
        
        # Fallback to regex patterns for cases not covered by AST
        for pattern_info in self.risk_patterns["security"]:
            pattern = re.compile(pattern_info["pattern"], re.IGNORECASE)
            
            for i, line in enumerate(lines, 1):
                # Skip if already detected by AST analysis
                already_detected = any(
                    risk.line_start <= i <= risk.line_end
                    for risk in risks
                )
                if already_detected:
                    continue
                
                if pattern.search(line):
                    risk = RiskDetector(
                        title=pattern_info["title"],
                        description=f"Security risk detected: {pattern_info['title']}",
                        severity=pattern_info["severity"],
                        category=pattern_info["category"],
                        file_path=parse_result.file_path,
                        line_start=i,
                        line_end=i,
                        code_snippet=line.strip(),
                        remediation="Move sensitive data to environment variables or secure configuration",
                        confidence=0.6  # Lower confidence for regex-only detection
                    )
                    risks.append(risk)
        
        return risks
    
    def _detect_code_smells(
        self,
        parse_result: ParseResult,
        content: str
    ) -> List[RiskDetector]:
        """
        Detect code smells using context-aware analysis.
        
        Combines parsed structure analysis with pattern matching.
        """
        risks = []
        lines = content.split('\n')
        
        # Detect long methods/functions from parsed nodes
        for node in parse_result.nodes:
            if node.node_type.value in ['method', 'function', 'procedure']:
                method_length = node.line_end - node.line_start + 1
                
                # Long method smell
                if method_length > 50:
                    severity = SeverityEnum.MEDIUM if method_length < 100 else SeverityEnum.HIGH
                    risk = RiskDetector(
                        title="Long Method",
                        description=f"Method '{node.name}' is {method_length} lines long",
                        severity=severity,
                        category="code_smell",
                        file_path=parse_result.file_path,
                        line_start=node.line_start,
                        line_end=node.line_end,
                        code_snippet=f"Method: {node.name}",
                        remediation="Consider breaking this method into smaller, more focused methods",
                        confidence=1.0
                    )
                    risks.append(risk)
                
                # Too many parameters
                if node.metadata and 'parameter_count' in node.metadata:
                    param_count = node.metadata['parameter_count']
                    if param_count > 5:
                        risk = RiskDetector(
                            title="Too Many Parameters",
                            description=f"Method '{node.name}' has {param_count} parameters",
                            severity=SeverityEnum.MEDIUM,
                            category="code_smell",
                            file_path=parse_result.file_path,
                            line_start=node.line_start,
                            line_end=node.line_start,
                            code_snippet=f"Method: {node.name}",
                            remediation="Consider using parameter objects or builder pattern",
                            confidence=1.0
                        )
                        risks.append(risk)
            
            # Detect god classes
            if node.node_type.value == 'class':
                if node.metadata:
                    method_count = node.metadata.get('method_count', 0)
                    if method_count > 20:
                        risk = RiskDetector(
                            title="God Class",
                            description=f"Class '{node.name}' has {method_count} methods",
                            severity=SeverityEnum.HIGH,
                            category="code_smell",
                            file_path=parse_result.file_path,
                            line_start=node.line_start,
                            line_end=node.line_end,
                            code_snippet=f"Class: {node.name}",
                            remediation="Consider splitting this class into smaller, more cohesive classes",
                            confidence=0.9
                        )
                        risks.append(risk)
        
        # Pattern-based detection for TODO/FIXME comments
        for pattern_info in self.risk_patterns["code_smell"]:
            pattern = re.compile(pattern_info["pattern"], re.IGNORECASE)
            
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    risk = RiskDetector(
                        title=pattern_info["title"],
                        description=f"Code smell detected: {pattern_info['title']}",
                        severity=pattern_info["severity"],
                        category=pattern_info["category"],
                        file_path=parse_result.file_path,
                        line_start=i,
                        line_end=i,
                        code_snippet=line.strip(),
                        remediation="Address the comment or remove if no longer relevant",
                        confidence=0.7
                    )
                    risks.append(risk)
        
        return risks
    
    def _detect_complexity_issues(self, parse_result: ParseResult) -> List[RiskDetector]:
        """Detect complexity-related issues."""
        risks = []
        
        # Check for high complexity nodes
        for node in parse_result.nodes:
            if node.complexity and node.complexity > 20:
                risk = RiskDetector(
                    title="High Complexity",
                    description=f"{node.node_type.value} '{node.name}' has high complexity ({node.complexity})",
                    severity=SeverityEnum.MEDIUM if node.complexity < 30 else SeverityEnum.HIGH,
                    category="complexity",
                    file_path=parse_result.file_path,
                    line_start=node.line_start,
                    line_end=node.line_end,
                    remediation="Consider refactoring into smaller, more manageable units"
                )
                risks.append(risk)
        
        # Check for very long files
        if parse_result.lines_of_code > 1000:
            risk = RiskDetector(
                title="Large File",
                description=f"File has {parse_result.lines_of_code} lines of code",
                severity=SeverityEnum.MEDIUM,
                category="complexity",
                file_path=parse_result.file_path,
                line_start=1,
                line_end=parse_result.lines_of_code,
                remediation="Consider splitting into multiple smaller files"
            )
            risks.append(risk)
        
        return risks
    
    def _detect_deprecated_patterns(
        self,
        parse_result: ParseResult,
        content: str
    ) -> List[RiskDetector]:
        """
        Detect deprecated patterns and APIs using parsed structure.
        
        Checks imports and API usage from AST.
        """
        risks = []
        lines = content.split('\n')
        
        # Check deprecated imports from parsed structure
        deprecated_imports = {
            'java.util.Date': 'Use java.time.LocalDate or java.time.Instant',
            'java.util.Vector': 'Use ArrayList or other modern collections',
            'java.util.Hashtable': 'Use HashMap or ConcurrentHashMap',
            'javax.xml.bind': 'Deprecated in Java 11, use jakarta.xml.bind',
        }
        
        for imp in parse_result.imports:
            for deprecated, alternative in deprecated_imports.items():
                if deprecated in imp:
                    risk = RiskDetector(
                        title=f"Deprecated Import: {deprecated}",
                        description=f"Import '{imp}' uses deprecated API",
                        severity=SeverityEnum.MEDIUM,
                        category="deprecated",
                        file_path=parse_result.file_path,
                        line_start=1,  # Imports are typically at the top
                        line_end=1,
                        code_snippet=imp,
                        remediation=alternative,
                        confidence=1.0
                    )
                    risks.append(risk)
        
        # Check for deprecated API usage in nodes
        for node in parse_result.nodes:
            if node.node_type.value in ['function_call', 'method_call', 'constructor']:
                # Check for deprecated constructors/methods
                deprecated_apis = ['Date(', 'Vector(', 'Hashtable(', 'StringBuffer']
                for api in deprecated_apis:
                    if api in node.name:
                        snippet_lines = lines[node.line_start-1:node.line_end]
                        snippet = '\n'.join(snippet_lines).strip()
                        
                        risk = RiskDetector(
                            title=f"Deprecated API Usage: {api}",
                            description=f"Use of deprecated API '{api}' detected",
                            severity=SeverityEnum.MEDIUM,
                            category="deprecated",
                            file_path=parse_result.file_path,
                            line_start=node.line_start,
                            line_end=node.line_end,
                            code_snippet=snippet[:200],
                            remediation="Update to use modern alternatives",
                            confidence=0.9
                        )
                        risks.append(risk)
        
        # Fallback to regex patterns
        for pattern_info in self.risk_patterns["deprecated"]:
            pattern = re.compile(pattern_info["pattern"], re.IGNORECASE)
            
            for i, line in enumerate(lines, 1):
                # Skip if already detected by AST
                already_detected = any(
                    risk.line_start <= i <= risk.line_end
                    for risk in risks
                )
                if already_detected:
                    continue
                
                if pattern.search(line):
                    risk = RiskDetector(
                        title=pattern_info["title"],
                        description=f"Deprecated pattern detected: {pattern_info['title']}",
                        severity=pattern_info["severity"],
                        category=pattern_info["category"],
                        file_path=parse_result.file_path,
                        line_start=i,
                        line_end=i,
                        code_snippet=line.strip(),
                        remediation="Update to use modern alternatives",
                        confidence=0.6
                    )
                    risks.append(risk)
        
        return risks
    
    def _detect_tight_coupling(self, parse_result: ParseResult) -> List[RiskDetector]:
        """
        Detect tight coupling issues using dependency analysis.
        
        Analyzes both import count and actual usage patterns.
        """
        risks = []
        
        # Count unique dependencies from imports and explicit dependencies
        total_deps = len(set(parse_result.imports + parse_result.dependencies))
        
        # Check for excessive dependencies
        if total_deps > 20:
            severity = SeverityEnum.MEDIUM if total_deps < 30 else SeverityEnum.HIGH
            risk = RiskDetector(
                title="Excessive Dependencies",
                description=f"File has {total_deps} unique dependencies",
                severity=severity,
                category="coupling",
                file_path=parse_result.file_path,
                line_start=1,
                line_end=1,
                remediation="Consider reducing dependencies and improving modularity. Use dependency injection and interfaces.",
                confidence=1.0
            )
            risks.append(risk)
        
        # Check for circular dependencies (if metadata available)
        if parse_result.metadata and 'circular_dependencies' in parse_result.metadata:
            circular_deps = parse_result.metadata['circular_dependencies']
            if circular_deps:
                risk = RiskDetector(
                    title="Circular Dependency Detected",
                    description=f"File is part of circular dependency chain: {' -> '.join(circular_deps[:3])}...",
                    severity=SeverityEnum.HIGH,
                    category="coupling",
                    file_path=parse_result.file_path,
                    line_start=1,
                    line_end=1,
                    remediation="Break circular dependencies by introducing interfaces or reorganizing code structure",
                    confidence=1.0
                )
                risks.append(risk)
        
        # Detect feature envy (methods using too many external classes)
        for node in parse_result.nodes:
            if node.node_type.value in ['method', 'function'] and node.metadata:
                external_calls = node.metadata.get('external_calls', [])
                if len(external_calls) > 5:
                    risk = RiskDetector(
                        title="Feature Envy",
                        description=f"Method '{node.name}' makes {len(external_calls)} external calls",
                        severity=SeverityEnum.MEDIUM,
                        category="coupling",
                        file_path=parse_result.file_path,
                        line_start=node.line_start,
                        line_end=node.line_end,
                        code_snippet=f"Method: {node.name}",
                        remediation="Consider moving this method closer to the data it uses",
                        confidence=0.7
                    )
                    risks.append(risk)
        
        return risks

# Made with Bob
