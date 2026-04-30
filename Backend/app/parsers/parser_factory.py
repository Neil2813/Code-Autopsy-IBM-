"""
Parser Factory

Factory for creating appropriate parser based on file type.
"""

import logging
from typing import Optional, List

from app.parsers.base_parser import BaseParser
from app.parsers.java_parser import JavaParser
from app.parsers.cobol_parser import CobolParser
from app.parsers.rpg_parser import RpgParser
from app.parsers.mainframe_parser import MainframeParser
from app.schemas.common import LanguageEnum

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for creating language-specific parsers."""
    
    def __init__(self):
        self._parsers: List[BaseParser] = [
            JavaParser(),
            CobolParser(),
            RpgParser(),
            MainframeParser()
        ]
        logger.info(f"Initialized parser factory with {len(self._parsers)} parsers")
    
    def get_parser(self, file_path: str) -> Optional[BaseParser]:
        """
        Get appropriate parser for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parser instance if found, None otherwise
        """
        for parser in self._parsers:
            if parser.can_parse(file_path):
                logger.debug(f"Selected {parser.language} parser for {file_path}")
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
            List of file extensions
        """
        extensions = []
        test_files = [
            'test.java',
            'test.cbl', 'test.cob', 'test.cobol', 'test.cpy',
            'test.rpg', 'test.rpgle', 'test.sqlrpgle',
            'test.jcl', 'test.proc'
        ]
        
        for test_file in test_files:
            for parser in self._parsers:
                if parser.can_parse(test_file):
                    ext = '.' + test_file.split('.')[-1]
                    if ext not in extensions:
                        extensions.append(ext)
        
        return extensions


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
    
    Args:
        file_path: Path to file
        
    Returns:
        Parser instance if found, None otherwise
    """
    factory = get_parser_factory()
    return factory.get_parser(file_path)

# Made with Bob
