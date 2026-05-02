# for IBM hackathon
"""
LLM Provider Chain

This package provides LLM integrations with fallback support:
- Primary: OpenAI GPT
- Secondary: Groq
- Tertiary: Rule-based fallback
"""

from app.llm.base_provider import BaseLLMProvider, LLMResponse
from app.llm.openai_provider import OpenAIProvider
from app.llm.groq_provider import GroqProvider
from app.llm.rule_based_provider import RuleBasedProvider
from app.llm.provider_chain import LLMProviderChain, get_llm_chain

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "OpenAIProvider",
    "GroqProvider",
    "RuleBasedProvider",
    "LLMProviderChain",
    "get_llm_chain"
]

# Made with Bob
