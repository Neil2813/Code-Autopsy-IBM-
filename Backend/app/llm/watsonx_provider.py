"""
IBM watsonx.ai Provider

LLM provider for IBM watsonx.ai foundation models.
Supports both watsonx.ai API and IBM Cloud Pak for Data deployments.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.llm.base_provider import BaseLLMProvider, LLMResponse
from app.config.settings import settings

logger = logging.getLogger(__name__)


class WatsonxProvider(BaseLLMProvider):
    """IBM watsonx.ai foundation model provider."""
    
    def __init__(self):
        super().__init__("watsonx", settings.watsonx_model)
        self.api_key = settings.watsonx_api_key
        self.project_id = settings.watsonx_project_id
        self.url = settings.watsonx_url
        self.client = None
        self.model_instance = None
    
    async def check_availability(self) -> bool:
        """Check if watsonx.ai is available and properly configured."""
        self.available = bool(
            self.api_key and 
            self.api_key != "your-watsonx-api-key-here" and
            self.project_id and
            self.project_id != "your-project-id-here" and
            self.url
        )
        
        if self.available:
            try:
                from ibm_watson_machine_learning.foundation_models import Model  # type: ignore[import-untyped]
                from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams  # type: ignore[import-untyped]
                
                # Initialize credentials
                credentials = {
                    "url": self.url,
                    "apikey": self.api_key
                }
                
                # Initialize model parameters
                self.gen_params = {
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MIN_NEW_TOKENS: 1,
                    GenParams.MAX_NEW_TOKENS: 2000,
                    GenParams.TEMPERATURE: 0.7,
                    GenParams.TOP_K: 50,
                    GenParams.TOP_P: 1,
                    GenParams.REPETITION_PENALTY: 1.0
                }
                
                # Initialize model
                self.model_instance = Model(
                    model_id=self.model,
                    params=self.gen_params,
                    credentials=credentials,
                    project_id=self.project_id
                )
                
                logger.info(f"watsonx.ai provider initialized successfully with model: {self.model}")
                
            except ImportError as e:
                logger.error(f"watsonx.ai library not installed: {e}")
                logger.error("Install with: pip install ibm-watson-machine-learning")
                self.available = False
            except Exception as e:
                logger.error(f"Failed to initialize watsonx.ai client: {e}")
                self.available = False
        else:
            logger.warning("watsonx.ai credentials not properly configured")
        
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
        Generate text using IBM watsonx.ai foundation models.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional, will be prepended to prompt)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional watsonx parameters
            
        Returns:
            LLMResponse with generated content
        """
        start_time = datetime.utcnow()
        
        if not self.available:
            await self.check_availability()
        
        if not self.available or not self.model_instance:
            return LLMResponse(
                content="",
                provider=self.name,
                model=self.model,
                success=False,
                error="watsonx.ai provider not available"
            )
        
        try:
            from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams  # type: ignore[import-untyped]
            
            # Build full prompt with system context
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Update generation parameters
            gen_params = self.gen_params.copy()
            gen_params[GenParams.TEMPERATURE] = temperature
            gen_params[GenParams.MAX_NEW_TOKENS] = max_tokens
            
            # Apply any additional parameters
            if "top_p" in kwargs:
                gen_params[GenParams.TOP_P] = kwargs["top_p"]
            if "top_k" in kwargs:
                gen_params[GenParams.TOP_K] = kwargs["top_k"]
            if "repetition_penalty" in kwargs:
                gen_params[GenParams.REPETITION_PENALTY] = kwargs["repetition_penalty"]
            if "decoding_method" in kwargs:
                gen_params[GenParams.DECODING_METHOD] = kwargs["decoding_method"]
            
            # Update model parameters
            self.model_instance.params = gen_params
            
            # Generate response
            logger.info(f"Generating with watsonx.ai model: {self.model}")
            response = self.model_instance.generate_text(prompt=full_prompt)
            
            # Extract content and initialize token counts
            tokens_used = 0
            input_tokens = 0
            
            if isinstance(response, dict):
                content = response.get("results", [{}])[0].get("generated_text", "")
                tokens_used = response.get("results", [{}])[0].get("generated_token_count", 0)
                input_tokens = response.get("results", [{}])[0].get("input_token_count", 0)
                total_tokens = tokens_used + input_tokens
            else:
                content = str(response)
                total_tokens = 0
            
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                f"watsonx.ai generation successful: {total_tokens} tokens, "
                f"{elapsed_ms:.2f}ms"
            )
            
            return LLMResponse(
                content=content,
                provider=self.name,
                model=self.model,
                tokens_used=total_tokens,
                latency_ms=elapsed_ms,
                success=True,
                metadata={
                    "project_id": self.project_id,
                    "model_id": self.model,
                    "input_tokens": input_tokens if isinstance(response, dict) else 0,
                    "generated_tokens": tokens_used if isinstance(response, dict) else 0
                }
            )
            
        except Exception as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"watsonx.ai generation failed: {e}")
            
            return LLMResponse(
                content="",
                provider=self.name,
                model=self.model,
                latency_ms=elapsed_ms,
                success=False,
                error=str(e)
            )
    
    async def generate_with_orchestrate(
        self,
        prompt: str,
        workflow_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate using watsonx Orchestrate for workflow automation.
        
        Args:
            prompt: User prompt
            workflow_id: Optional workflow ID for Orchestrate
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with generated content
        """
        start_time = datetime.utcnow()
        
        try:
            # This is a placeholder for watsonx Orchestrate integration
            # Actual implementation would use the Orchestrate API
            logger.info("watsonx Orchestrate integration - using standard generation")
            
            # For now, fall back to standard generation
            # In production, this would call Orchestrate workflows
            return await self.generate(prompt=prompt, **kwargs)
            
        except Exception as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"watsonx Orchestrate generation failed: {e}")
            
            return LLMResponse(
                content="",
                provider=f"{self.name}-orchestrate",
                model=self.model,
                latency_ms=elapsed_ms,
                success=False,
                error=str(e)
            )


# Made with Bob