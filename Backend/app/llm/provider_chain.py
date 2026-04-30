"""
LLM Provider Chain

Manages multiple LLM providers with fallback logic.
"""

import logging
from typing import List, Optional

from app.llm.base_provider import BaseLLMProvider, LLMResponse
from app.llm.openai_provider import OpenAIProvider
from app.llm.groq_provider import GroqProvider
from app.llm.rule_based_provider import RuleBasedProvider

logger = logging.getLogger(__name__)


class LLMProviderChain:
    """
    Chain of LLM providers with automatic fallback.
    
    Tries providers in order:
    1. OpenAI (primary)
    2. Groq (secondary)
    3. Rule-based (tertiary, always available)
    """
    
    def __init__(self):
        self.providers: List[BaseLLMProvider] = [
            OpenAIProvider(),
            GroqProvider(),
            RuleBasedProvider()
        ]
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all providers and check availability."""
        if self._initialized:
            return
        
        logger.info("Initializing LLM provider chain...")
        
        for provider in self.providers:
            try:
                available = await provider.check_availability()
                status = "available" if available else "unavailable"
                logger.info(f"Provider {provider.get_name()}: {status}")
            except Exception as e:
                logger.error(f"Failed to initialize {provider.get_name()}: {e}")
        
        self._initialized = True
        logger.info("LLM provider chain initialized")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using the first available provider.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse from the first successful provider
        """
        if not self._initialized:
            await self.initialize()
        
        errors = []
        
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Skipping unavailable provider: {provider.get_name()}")
                continue
            
            try:
                logger.info(f"Attempting generation with {provider.get_name()}")
                
                response = await provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if response.success:
                    logger.info(
                        f"Successfully generated response with {provider.get_name()}"
                    )
                    return response
                else:
                    error_msg = f"{provider.get_name()} failed: {response.error}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"{provider.get_name()} exception: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # All providers failed
        logger.error("All LLM providers failed")
        return LLMResponse(
            content="",
            provider="none",
            model="none",
            success=False,
            error=f"All providers failed: {'; '.join(errors)}"
        )
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [
            provider.get_name()
            for provider in self.providers
            if provider.is_available()
        ]
    
    def get_provider_status(self) -> dict:
        """Get status of all providers."""
        return {
            provider.get_name(): {
                "available": provider.is_available(),
                "model": provider.get_model()
            }
            for provider in self.providers
        }


# Singleton instance
_llm_chain: Optional[LLMProviderChain] = None


def get_llm_chain() -> LLMProviderChain:
    """
    Get or create LLM provider chain singleton.
    
    Returns:
        LLMProviderChain instance
    """
    global _llm_chain
    if _llm_chain is None:
        _llm_chain = LLMProviderChain()
    return _llm_chain


async def initialize_llm_chain() -> LLMProviderChain:
    """
    Initialize and return LLM provider chain.
    
    Returns:
        Initialized LLMProviderChain instance
    """
    chain = get_llm_chain()
    await chain.initialize()
    return chain

# Made with Bob
