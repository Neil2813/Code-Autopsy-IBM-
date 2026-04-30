"""
Base LLM Provider

Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must inherit from this class and implement
    the generate method.
    """
    
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.available = False
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """
        Check if the provider is available.
        
        Returns:
            True if provider is available and configured
        """
        pass
    
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        return self.available
    
    def get_name(self) -> str:
        """Get provider name."""
        return self.name
    
    def get_model(self) -> str:
        """Get model name."""
        return self.model

# Made with Bob
