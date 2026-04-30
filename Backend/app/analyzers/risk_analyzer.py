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
        """Detect security-related risks."""
        risks = []
        lines = content.split('\n')
        
        for pattern_info in self.risk_patterns["security"]:
            pattern = re.compile(pattern_info["pattern"], re.IGNORECASE)
            
            for i, line in enumerate(lines, 1):
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
                        remediation="Move sensitive data to environment variables or secure configuration"
                    )
                    risks.append(risk)
        
        return risks
    
    def _detect_code_smells(
        self,
        parse_result: ParseResult,
        content: str
    ) -> List[RiskDetector]:
        """Detect code smells."""
        risks = []
        lines = content.split('\n')
        
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
                        remediation="Address the comment or remove if no longer relevant"
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
        """Detect deprecated patterns and APIs."""
        risks = []
        lines = content.split('\n')
        
        for pattern_info in self.risk_patterns["deprecated"]:
            pattern = re.compile(pattern_info["pattern"], re.IGNORECASE)
            
            for i, line in enumerate(lines, 1):
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
                        remediation="Update to use modern alternatives"
                    )
                    risks.append(risk)
        
        return risks
    
    def _detect_tight_coupling(self, parse_result: ParseResult) -> List[RiskDetector]:
        """Detect tight coupling issues."""
        risks = []
        
        # Check for excessive dependencies
        if len(parse_result.dependencies) > 20:
            risk = RiskDetector(
                title="Excessive Dependencies",
                description=f"File has {len(parse_result.dependencies)} dependencies",
                severity=SeverityEnum.MEDIUM,
                category="coupling",
                file_path=parse_result.file_path,
                line_start=1,
                line_end=1,
                remediation="Consider reducing dependencies and improving modularity"
            )
            risks.append(risk)
        
        return risks

# Made with Bob
