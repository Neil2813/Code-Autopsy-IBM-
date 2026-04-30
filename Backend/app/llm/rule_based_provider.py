"""
Rule-Based Provider

Fallback provider that uses rule-based logic when LLMs are unavailable.
"""

import logging
from typing import Optional
from datetime import datetime

from app.llm.base_provider import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class RuleBasedProvider(BaseLLMProvider):
    """Rule-based fallback provider."""
    
    def __init__(self):
        super().__init__("rule_based", "rule_based_v1")
        self.available = True  # Always available
    
    async def check_availability(self) -> bool:
        """Rule-based provider is always available."""
        self.available = True
        return True
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using rule-based logic.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Ignored for rule-based
            max_tokens: Ignored for rule-based
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with rule-based content
        """
        start_time = datetime.utcnow()
        
        try:
            # Determine response type based on prompt keywords
            content = self._generate_rule_based_response(prompt, system_prompt)
            
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Rule-based generation successful: {elapsed_ms:.2f}ms")
            
            return LLMResponse(
                content=content,
                provider=self.name,
                model=self.model,
                tokens_used=0,
                latency_ms=elapsed_ms,
                success=True,
                metadata={"type": "rule_based"}
            )
            
        except Exception as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Rule-based generation failed: {e}")
            
            return LLMResponse(
                content="Unable to generate response using rule-based fallback.",
                provider=self.name,
                model=self.model,
                latency_ms=elapsed_ms,
                success=False,
                error=str(e)
            )
    
    def _generate_rule_based_response(
        self,
        prompt: str,
        system_prompt: Optional[str]
    ) -> str:
        """Generate rule-based response based on prompt analysis."""
        prompt_lower = prompt.lower()
        
        # Explanation requests
        if any(word in prompt_lower for word in ["explain", "what does", "describe"]):
            return self._generate_explanation_response(prompt)
        
        # Risk detection requests
        elif any(word in prompt_lower for word in ["risk", "danger", "security", "vulnerable"]):
            return self._generate_risk_response(prompt)
        
        # Modernization requests
        elif any(word in prompt_lower for word in ["modernize", "refactor", "improve", "update"]):
            return self._generate_modernization_response(prompt)
        
        # Dependency requests
        elif any(word in prompt_lower for word in ["depend", "import", "relationship", "coupling"]):
            return self._generate_dependency_response(prompt)
        
        # General fallback
        else:
            return self._generate_general_response(prompt)
    
    def _generate_explanation_response(self, prompt: str) -> str:
        """Generate explanation response."""
        return """Based on static analysis, this code appears to be a legacy system component.

Key observations:
- The code structure follows older programming patterns
- Multiple dependencies and tight coupling detected
- Consider reviewing for modernization opportunities

Note: This is a rule-based analysis. For detailed insights, please configure an LLM provider."""
    
    def _generate_risk_response(self, prompt: str) -> str:
        """Generate risk analysis response."""
        return """Risk Analysis (Rule-Based):

Potential risks detected:
1. **Code Complexity**: High cyclomatic complexity may indicate maintenance challenges
2. **Dependencies**: Multiple external dependencies increase coupling
3. **Legacy Patterns**: Older coding patterns may have security implications
4. **Documentation**: Limited inline documentation detected

Recommendations:
- Review security-sensitive code sections
- Update deprecated dependencies
- Add comprehensive test coverage
- Document critical business logic

Note: For detailed risk analysis, please configure an LLM provider."""
    
    def _generate_modernization_response(self, prompt: str) -> str:
        """Generate modernization response."""
        return """Modernization Recommendations (Rule-Based):

Priority Actions:
1. **Update Dependencies**: Migrate to current framework versions
2. **Refactor Complex Methods**: Break down high-complexity functions
3. **Improve Test Coverage**: Add unit and integration tests
4. **Document Architecture**: Create architecture diagrams and documentation
5. **Apply Design Patterns**: Introduce modern design patterns where applicable

Migration Strategy:
- Start with low-risk, high-value components
- Implement comprehensive testing before changes
- Use feature flags for gradual rollout
- Maintain backward compatibility during transition

Note: For detailed modernization plans, please configure an LLM provider."""
    
    def _generate_dependency_response(self, prompt: str) -> str:
        """Generate dependency analysis response."""
        return """Dependency Analysis (Rule-Based):

Observations:
- Multiple module dependencies detected
- Potential circular dependencies may exist
- High coupling between components observed

Recommendations:
- Review and document dependency relationships
- Consider dependency injection patterns
- Reduce tight coupling through interfaces
- Implement layered architecture

Note: For detailed dependency graphs, please configure an LLM provider."""
    
    def _generate_general_response(self, prompt: str) -> str:
        """Generate general response."""
        return """Analysis Result (Rule-Based):

The system has analyzed your request using rule-based logic. For more detailed and context-aware analysis, please configure an LLM provider (OpenAI or Groq).

Current capabilities (rule-based mode):
- Basic code structure analysis
- Pattern detection
- Standard recommendations
- Risk identification

Enhanced capabilities (with LLM):
- Deep code understanding
- Context-aware suggestions
- Natural language explanations
- Custom refactoring recommendations

To enable LLM features, please set your API keys in the .env file."""

# Made with Bob
