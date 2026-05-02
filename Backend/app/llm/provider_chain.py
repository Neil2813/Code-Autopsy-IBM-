"""
LLM Provider Chain

Manages multiple LLM providers with fallback logic.
"""

import logging
from typing import List, Optional, Dict

from app.llm.base_provider import BaseLLMProvider, LLMResponse
from app.llm.watsonx_provider import WatsonxProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.groq_provider import GroqProvider
from app.llm.rule_based_provider import RuleBasedProvider

logger = logging.getLogger(__name__)


class LLMProviderChain:
    """
    Chain of LLM providers with automatic fallback.
    
    Tries providers in order:
    1. IBM watsonx.ai (primary) - Enterprise-grade foundation models
    2. OpenAI (secondary) - Fallback for high availability
    3. Groq (tertiary) - Fast inference fallback
    4. Rule-based (quaternary) - Always available deterministic fallback
    """
    
    def __init__(self):
        self.providers: List[BaseLLMProvider] = [
            WatsonxProvider(),
            OpenAIProvider(),
            GroqProvider(),
            RuleBasedProvider()
        ]
        self._initialized = False
        self._last_check_time: Dict[str, float] = {}
        self._check_interval_seconds = 300  # Re-check every 5 minutes
    
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
                
                # Record check time
                import time
                self._last_check_time[provider.get_name()] = time.time()
            except Exception as e:
                logger.error(f"Failed to initialize {provider.get_name()}: {e}")
                provider.available = False
        
        self._initialized = True
        logger.info("LLM provider chain initialized")
    
    async def refresh_provider_status(self, force: bool = False) -> None:
        """
        Refresh availability status of all providers.
        
        Args:
            force: Force refresh even if recently checked
        """
        import time
        current_time = time.time()
        
        for provider in self.providers:
            provider_name = provider.get_name()
            last_check = self._last_check_time.get(provider_name, 0)
            
            # Skip if recently checked (unless forced)
            if not force and (current_time - last_check) < self._check_interval_seconds:
                continue
            
            try:
                logger.debug(f"Refreshing status for {provider_name}")
                available = await provider.check_availability()
                self._last_check_time[provider_name] = current_time
                
                # Log status changes
                if available != provider.is_available():
                    status = "available" if available else "unavailable"
                    logger.info(f"Provider {provider_name} status changed to: {status}")
            except Exception as e:
                logger.warning(f"Failed to refresh {provider_name}: {e}")
                provider.available = False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using the first available provider with fallback.
        
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
        
        # Refresh provider status if needed
        await self.refresh_provider_status(force=False)
        
        errors = []
        attempted_providers = []
        
        for provider in self.providers:
            provider_name = provider.get_name()
            
            if not provider.is_available():
                logger.debug(f"Skipping unavailable provider: {provider_name}")
                errors.append(f"{provider_name}: not available")
                continue
            
            try:
                logger.info(f"Attempting generation with {provider_name}")
                attempted_providers.append(provider_name)
                
                response = await provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if response.success:
                    logger.info(
                        f"Successfully generated response with {provider_name} "
                        f"({response.tokens_used} tokens, {response.latency_ms:.0f}ms)"
                    )
                    return response
                else:
                    error_msg = f"{provider_name} failed: {response.error or 'unknown error'}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
                    # Mark provider as temporarily unavailable on repeated failures
                    provider.available = False
                    
            except Exception as e:
                error_msg = f"{provider_name} exception: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                provider.available = False
        
        # All providers failed
        diagnostic_info = {
            "attempted": attempted_providers,
            "total_providers": len(self.providers),
            "errors": errors
        }
        
        logger.error(
            f"All LLM providers failed. Attempted: {attempted_providers}. "
            f"Errors: {'; '.join(errors[:3])}"
        )
        
        return LLMResponse(
            content="",
            provider="none",
            model="none",
            success=False,
            error=f"All {len(attempted_providers)} providers failed",
            metadata=diagnostic_info
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
