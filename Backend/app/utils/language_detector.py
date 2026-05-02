"""
Language detection utilities for source code files.
"""

import logging
import re
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect programming languages from files."""
    
    # Extension to language mapping
    EXTENSION_MAP = {
        '.java': 'java',
        '.class': 'java',
        '.jar': 'java',
        '.cbl': 'cobol',
        '.cob': 'cobol',
        '.cobol': 'cobol',
        '.rpg': 'rpg',
        '.rpgle': 'rpg',
        '.sqlrpgle': 'rpg',
        '.jcl': 'jcl',
        '.proc': 'jcl',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.sql': 'sql',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.properties': 'properties',
        '.sh': 'shell',
        '.bash': 'shell',
        '.pl': 'perl',
        '.rb': 'ruby',
        '.php': 'php',
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'spring': ['@SpringBootApplication', 'org.springframework'],
        'jakarta': ['jakarta.', 'javax.'],
        'hibernate': ['org.hibernate', '@Entity'],
        'struts': ['org.apache.struts'],
        'jsf': ['javax.faces', 'jakarta.faces'],
    }
    
    # Content-based detection patterns (language -> patterns)
    CONTENT_PATTERNS = {
        'java': {
            'keywords': ['public class', 'private class', 'protected class', 'package ', 'import java.', 'import javax.', 'import jakarta.'],
            'patterns': [r'\bpublic\s+(?:static\s+)?(?:final\s+)?class\b', r'\bpublic\s+interface\b', r'@Override', r'@Autowired'],
            'weight': 10
        },
        'cobol': {
            'keywords': ['identification division', 'procedure division', 'working-storage', 'data division', 'environment division'],
            'patterns': [r'^\s*\d{6}\s+', r'\bPIC\s+[X9]+', r'\bMOVE\s+\w+\s+TO\b', r'\bPERFORM\s+\w+'],
            'weight': 10
        },
        'rpg': {
            'keywords': ['dcl-s ', 'dcl-pr ', 'dcl-pi ', 'begsr', 'endsr', 'dcl-proc', 'end-proc'],
            'patterns': [r'\bDCL-\w+\b', r'\bEXSR\b', r'\bDOU\b', r'\bDOW\b', r'\bIF\b.*\bENDIF\b'],
            'weight': 10
        },
        'jcl': {
            'keywords': ['//'],
            'patterns': [r'^//\w+\s+JOB\b', r'^//\w+\s+EXEC\b', r'^//\w+\s+DD\b', r'//\*'],
            'weight': 10
        },
        'python': {
            'keywords': ['def ', 'import ', 'from ', 'class ', '__init__', '__main__'],
            'patterns': [r'\bdef\s+\w+\s*\(', r'\bclass\s+\w+\s*[:\(]', r'if\s+__name__\s*==\s*["\']__main__["\']'],
            'weight': 8
        },
        'javascript': {
            'keywords': ['function ', 'const ', 'let ', 'var ', '=>', 'console.log'],
            'patterns': [r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=', r'=>\s*{', r'require\(["\']'],
            'weight': 7
        },
        'typescript': {
            'keywords': ['interface ', 'type ', ': string', ': number', ': boolean', 'export ', 'import '],
            'patterns': [r'\binterface\s+\w+\s*{', r'\btype\s+\w+\s*=', r':\s*(?:string|number|boolean|any)\b'],
            'weight': 8
        },
        'sql': {
            'keywords': ['SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE'],
            'patterns': [r'\bSELECT\s+.*\s+FROM\b', r'\bINSERT\s+INTO\b', r'\bCREATE\s+TABLE\b'],
            'weight': 9
        },
        'xml': {
            'keywords': ['<?xml', '<beans', '<project', '<configuration'],
            'patterns': [r'<\?xml\s+version=', r'<\w+[^>]*xmlns='],
            'weight': 10
        },
        'shell': {
            'keywords': ['#!/bin/bash', '#!/bin/sh', 'echo ', 'export ', 'if [', 'fi'],
            'patterns': [r'^#!/bin/(?:ba)?sh', r'\$\{?\w+\}?', r'\bif\s+\[.*\]\s*;\s*then\b'],
            'weight': 8
        }
    }
    
    def detect_from_extension(self, filename: str) -> Optional[str]:
        """Detect language from file extension."""
        ext = Path(filename).suffix.lower()
        return self.EXTENSION_MAP.get(ext)
    
    def _score_language_content(self, content: str, language: str, patterns: Dict) -> int:
        """
        Score how well content matches a language's patterns.
        
        Args:
            content: File content
            language: Language to check
            patterns: Pattern dictionary for the language
            
        Returns:
            Score (higher = better match)
        """
        score = 0
        content_lower = content.lower()
        
        # Check keywords
        for keyword in patterns.get('keywords', []):
            if keyword.lower() in content_lower:
                score += 1
        
        # Check regex patterns
        for pattern in patterns.get('patterns', []):
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                score += 2  # Patterns are more specific, weight them higher
        
        # Apply language weight
        score *= patterns.get('weight', 1)
        
        return score
    
    async def detect_from_content(self, content: str, filename: str = "") -> Optional[str]:
        """
        Detect language from file content using enhanced heuristics.
        
        Args:
            content: File content
            filename: Optional filename for extension-based detection
            
        Returns:
            Detected language or None
        """
        # First try extension (most reliable)
        if filename:
            lang = self.detect_from_extension(filename)
            if lang:
                return lang
        
        if not content or len(content.strip()) == 0:
            return None
        
        # Score each language
        scores = {}
        for language, patterns in self.CONTENT_PATTERNS.items():
            score = self._score_language_content(content, language, patterns)
            if score > 0:
                scores[language] = score
        
        # Return language with highest score (if above threshold)
        if scores:
            best_language = max(scores.items(), key=lambda x: x[1])
            if best_language[1] >= 3:  # Minimum confidence threshold
                logger.debug(f"Detected language: {best_language[0]} (score: {best_language[1]})")
                return best_language[0]
        
        logger.debug("Could not detect language from content")
        return None
    
    def detect_language_with_confidence(self, content: str, filename: str = "") -> tuple[Optional[str], float]:
        """
        Detect language with confidence score.
        
        Args:
            content: File content
            filename: Optional filename
            
        Returns:
            Tuple of (language, confidence) where confidence is 0.0-1.0
        """
        # Extension-based detection has highest confidence
        if filename:
            lang = self.detect_from_extension(filename)
            if lang:
                return (lang, 1.0)
        
        if not content or len(content.strip()) == 0:
            return (None, 0.0)
        
        # Score each language
        scores = {}
        max_possible_score = 0
        
        for language, patterns in self.CONTENT_PATTERNS.items():
            score = self._score_language_content(content, language, patterns)
            if score > 0:
                scores[language] = score
            
            # Calculate max possible score for this language
            keyword_count = len(patterns.get('keywords', []))
            pattern_count = len(patterns.get('patterns', []))
            weight = patterns.get('weight', 1)
            lang_max = (keyword_count + pattern_count * 2) * weight
            max_possible_score = max(max_possible_score, lang_max)
        
        if scores:
            best_language, best_score = max(scores.items(), key=lambda x: x[1])
            confidence = min(best_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
            
            if confidence >= 0.3:  # Minimum confidence threshold
                return (best_language, confidence)
        
        return (None, 0.0)
    
    def detect_framework(self, files: List[Path], language: str) -> List[str]:
        """Detect frameworks used in the codebase."""
        frameworks = set()
        
        if language != 'java':
            return list(frameworks)
        
        # Check files for framework patterns
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                        if any(pattern in content for pattern in patterns):
                            frameworks.add(framework)
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                continue
        
        return list(frameworks)
    
    def is_supported_language(self, language: str) -> bool:
        """Check if language is supported."""
        supported = {'java', 'cobol', 'rpg', 'jcl', 'python', 'javascript', 'typescript'}
        return language.lower() in supported
    
    def get_language_stats(self, files: List[Path]) -> dict:
        """Get statistics about languages in file list."""
        stats = {}
        
        for file_path in files:
            lang = self.detect_from_extension(file_path.name)
            if lang:
                stats[lang] = stats.get(lang, 0) + 1
        
        return stats
    
    def get_primary_language(self, files: List[Path]) -> Optional[str]:
        """Determine primary language from file list."""
        stats = self.get_language_stats(files)
        
        if not stats:
            return None
        
        # Return language with most files
        return max(stats.items(), key=lambda x: x[1])[0]


# Singleton instance
language_detector = LanguageDetector()

# Made with Bob
