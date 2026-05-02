# for IBM hackathon
"""
Groq Provider

LLM provider for Groq models (fast inference).
"""

import logging
from typing import Optional
from datetime import datetime

from app.llm.base_provider import BaseLLMProvider, LLMResponse
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider."""
    
    def __init__(self):
        super().__init__("groq", settings.groq_model)
        self.api_key = settings.groq_api_key
        self.client = None
    
    async def check_availability(self) -> bool:
        """Check if Groq is available."""
        self.available = bool(
            self.api_key and 
            self.api_key != "your-groq-key-here" and
            self.api_key.startswith("gsk_")
        )
        
        if self.available:
            try:
                from groq import AsyncGroq  # type: ignore[import-untyped]
                self.client = AsyncGroq(api_key=self.api_key)
                logger.info("Groq provider initialized successfully")
            except ImportError:
                logger.error("Groq library not installed")
                self.available = False
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.available = False
        else:
            logger.warning("Groq API key not configured")
        
        return self.available
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using Groq.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Groq parameters
            
        Returns:
            LLMResponse with generated content
        """
        start_time = datetime.utcnow()
        
        if not self.available:
            await self.check_availability()
        
        if not self.available or not self.client:
            return LLMResponse(
                content="",
                provider=self.name,
                model=self.model,
                success=False,
                error="Groq provider not available"
            )
        
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Call Groq API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                f"Groq generation successful: {tokens_used} tokens, "
                f"{elapsed_ms:.2f}ms"
            )
            
            return LLMResponse(
                content=content,
                provider=self.name,
                model=self.model,
                tokens_used=tokens_used,
                latency_ms=elapsed_ms,
                success=True,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "model": response.model
                }
            )
            
        except Exception as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Groq generation failed: {e}")
            
            return LLMResponse(
                content="",
                provider=self.name,
                model=self.model,
                latency_ms=elapsed_ms,
                success=False,
                error=str(e)
            )

# Made with Bob
