# for IBM hackathon
"""
Parser Factory

Factory for creating appropriate parser based on file type.
"""

import logging
from typing import Optional, List, Dict, Any

from app.parsers.base_parser import BaseParser
from app.parsers.java_parser import JavaParser
from app.parsers.cobol_parser import CobolParser
from app.parsers.rpg_parser import RpgParser
from app.parsers.mainframe_parser import MainframeParser
from app.schemas.common import LanguageEnum

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for creating language-specific parsers."""
    
    # Extension to parser class mapping (centralized)
    EXTENSION_MAP = {
        # Java
        '.java': JavaParser,
        
        # COBOL
        '.cbl': CobolParser,
        '.cob': CobolParser,
        '.cobol': CobolParser,
        '.cpy': CobolParser,  # Copybook
        
        # RPG
        '.rpg': RpgParser,
        '.rpgle': RpgParser,
        '.sqlrpgle': RpgParser,
        '.rpg4': RpgParser,
        
        # Mainframe/JCL
        '.jcl': MainframeParser,
        '.proc': MainframeParser,
    }
    
    def __init__(self):
        # Initialize parser instances (singleton pattern per factory)
        self._parser_instances = {}
        self._parsers: List[BaseParser] = [
            JavaParser(),
            CobolParser(),
            RpgParser(),
            MainframeParser()
        ]
        logger.info(f"Initialized parser factory with {len(self._parsers)} parsers")
    
    def get_parser(self, file_path: str) -> Optional[BaseParser]:
        """
        Get appropriate parser for a file using extension mapping.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parser instance if found, None otherwise
        """
        # Normalize file path
        file_path_lower = file_path.lower()
        
        # Try extension-based lookup first (faster)
        for ext, parser_class in self.EXTENSION_MAP.items():
            if file_path_lower.endswith(ext):
                # Get or create parser instance
                if parser_class not in self._parser_instances:
                    self._parser_instances[parser_class] = parser_class()
                
                parser = self._parser_instances[parser_class]
                logger.debug(f"Selected {parser.language} parser for {file_path} (extension: {ext})")
                return parser
        
        # Fallback: check if any parser can handle it (for special cases)
        for parser in self._parsers:
            if parser.can_parse(file_path):
                logger.debug(f"Selected {parser.language} parser for {file_path} (fallback)")
                return parser
        
        logger.warning(f"No parser found for {file_path}")
        return None
    
    def get_parser_by_language(self, language: LanguageEnum) -> Optional[BaseParser]:
        """
        Get parser by language enum.
        
        Args:
            language: Language enum value
            
        Returns:
            Parser instance if found, None otherwise
        """
        language_map = {
            LanguageEnum.JAVA: JavaParser,
            LanguageEnum.COBOL: CobolParser,
            LanguageEnum.RPG: RpgParser,
            LanguageEnum.MAINFRAME: MainframeParser,
            LanguageEnum.JCL: MainframeParser
        }
        
        parser_class = language_map.get(language)
        if parser_class:
            return parser_class()
        
        logger.warning(f"No parser found for language: {language}")
        return None
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of file extensions (sorted)
        """
        return sorted(list(self.EXTENSION_MAP.keys()))
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of all supported languages.
        
        Returns:
            List of language names
        """
        languages = set()
        for parser in self._parsers:
            languages.add(parser.language)
        return sorted(list(languages))
    
    def get_parser_info(self) -> Dict[str, Any]:
        """
        Get information about all available parsers.
        
        Returns:
            Dictionary with parser information
        """
        info = {
            'total_parsers': len(self._parsers),
            'supported_extensions': self.get_supported_extensions(),
            'supported_languages': self.get_supported_languages(),
            'parsers': []
        }
        
        for parser in self._parsers:
            parser_info = {
                'language': parser.language,
                'class': parser.__class__.__name__,
                'extensions': [ext for ext, cls in self.EXTENSION_MAP.items()
                              if cls == parser.__class__]
            }
            info['parsers'].append(parser_info)
        
        return info


# Singleton instance
_parser_factory: Optional[ParserFactory] = None


def get_parser_factory() -> ParserFactory:
    """
    Get or create parser factory singleton.
    
    Returns:
        ParserFactory instance
    """
    global _parser_factory
    if _parser_factory is None:
        _parser_factory = ParserFactory()
    return _parser_factory


def get_parser_for_language(language: LanguageEnum) -> Optional[BaseParser]:
    """
    Convenience function to get parser by language.
    
    Args:
        language: Language enum
        
    Returns:
        Parser instance if found, None otherwise
    """
    factory = get_parser_factory()
    return factory.get_parser_by_language(language)


def get_parser_for_file(file_path: str) -> Optional[BaseParser]:
    """
    Convenience function to get parser by file path.
    
    This is the primary entry point for getting a parser instance.
    Uses the singleton factory and extension-based mapping for efficiency.
    
    Args:
        file_path: Path to file (can be relative or absolute)
        
    Returns:
        Parser instance if found, None otherwise
        
    Example:
        >>> parser = get_parser_for_file('src/Main.java')
        >>> if parser:
        ...     result = parser.parse('src/Main.java', content)
    """
    factory = get_parser_factory()
    return factory.get_parser(file_path)


def is_supported_file(file_path: str) -> bool:
    """
    Check if a file is supported by any parser.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file is supported, False otherwise
    """
    return get_parser_for_file(file_path) is not None


def get_language_for_file(file_path: str) -> Optional[str]:
    """
    Get the language name for a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Language name if supported, None otherwise
    """
    parser = get_parser_for_file(file_path)
    return parser.language if parser else None

# Made with Bob
