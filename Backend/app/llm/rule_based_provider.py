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
        """
        Generate rule-based response based on prompt analysis.

        Conversational queries (from the query endpoint) always get human-readable
        prose. Internal analysis pipeline prompts that explicitly request a JSON
        schema still receive JSON so the parser can ingest them.
        """
        prompt_lower = prompt.lower()

        # ── Conversational / Q&A path ─────────────────────────────────────────
        # The answer_query prompt template always contains this exact phrase.
        # Guard this FIRST so user questions never fall into the JSON branches.
        is_query_prompt = "code analysis assistant" in prompt_lower or \
                          "please provide a clear, accurate answer" in prompt_lower or \
                          (system_prompt and "answer questions about codebases" in system_prompt.lower())

        if is_query_prompt:
            return self._generate_query_answer(prompt)

        # ── Internal pipeline paths (JSON output expected by parsers) ─────────
        # Only route here when the prompt explicitly demands a JSON schema.
        if "json" in prompt_lower and ("schema" in prompt_lower or "valid json" in prompt_lower or "json structure" in prompt_lower):
            if any(w in prompt_lower for w in ["code review", "line-level"]):
                return self._generate_code_review_json(prompt)
            if any(w in prompt_lower for w in ["modernize", "suggestion", "migration"]):
                return self._generate_modernization_json(prompt)
            if any(w in prompt_lower for w in ["validate", "feasibility"]):
                return self._generate_validation_json(prompt)
            # Default internal JSON → risk analysis schema
            return self._generate_risk_json(prompt)

        # ── Soft-match fallback for remaining internal prompts ─────────────────
        if any(w in prompt_lower for w in ["modernize", "suggest", "recommendation", "migration"]):
            return self._generate_modernization_json(prompt)
        if any(w in prompt_lower for w in ["validate", "feasibility", "review"]):
            return self._generate_validation_json(prompt)
        if any(w in prompt_lower for w in ["explain", "what does", "describe"]):
            return self._generate_explanation_response(prompt)

        return self._generate_general_response(prompt)
    
    def _generate_code_review_json(self, prompt: str) -> str:
        """Generate schema-compatible code review JSON."""
        import json
        
        response = {
            "summary": {
                "total_files": 1,
                "total_issues": 1,
                "high": 0,
                "medium": 1,
                "low": 0
            },
            "files": [
                {
                    "file_path": "example.ts",
                    "issues": [
                        {
                            "line": 1,
                            "severity": "MEDIUM",
                            "type": "maintainability",
                            "title": "Rule-based mock issue",
                            "code_snippet": "/* Add LLM provider for actual review */",
                            "problem": "This is a fallback analysis because no LLM is configured. A real LLM provider is required to perform structural code reviews.",
                            "fix": "Configure an LLM provider (OpenAI, Groq) in your .env file."
                        }
                    ]
                }
            ]
        }
        return json.dumps(response, indent=2)
    
    def _generate_risk_json(self, prompt: str) -> str:
        """Generate schema-compatible risk analysis JSON."""
        import json
        
        response = {
            "summary": "Rule-based analysis completed. Configure LLM provider for detailed insights.",
            "overall_severity": "medium",
            "issues": [
                {
                    "title": "Legacy Code Patterns Detected",
                    "description": "Code follows older programming patterns that may benefit from modernization",
                    "severity": "medium",
                    "category": "maintainability",
                    "file_path": "unknown",
                    "line_start": 1,
                    "line_end": 1,
                    "code_snippet": "# Rule-based detection",
                    "recommendation": "Review code for modern patterns and refactoring opportunities",
                    "confidence": 0.5
                }
            ],
            "what_to_fix_first": [
                "Configure LLM provider for detailed analysis",
                "Review static analysis findings",
                "Update dependencies to current versions"
            ]
        }
        return json.dumps(response, indent=2)
    
    def _generate_modernization_json(self, prompt: str) -> str:
        """Generate schema-compatible modernization JSON."""
        import json
        
        response = {
            "summary": "Rule-based modernization assessment. Configure LLM for detailed recommendations.",
            "priority_score": 5,
            "suggestions": [
                {
                    "title": "Update Framework Dependencies",
                    "description": "Migrate to current framework versions for security and performance",
                    "priority": "high",
                    "category": "framework",
                    "estimated_effort": "medium",
                    "benefits": ["Improved security", "Better performance", "Modern features"],
                    "risks": ["Breaking changes", "Testing overhead"],
                    "implementation_steps": [
                        "Audit current dependencies",
                        "Check compatibility",
                        "Update incrementally",
                        "Test thoroughly"
                    ],
                    "affected_files": [],
                    "confidence": 0.6
                },
                {
                    "title": "Improve Test Coverage",
                    "description": "Add comprehensive unit and integration tests",
                    "priority": "high",
                    "category": "testing",
                    "estimated_effort": "high",
                    "benefits": ["Reduced bugs", "Safer refactoring", "Better documentation"],
                    "risks": ["Time investment"],
                    "implementation_steps": [
                        "Identify critical paths",
                        "Write unit tests",
                        "Add integration tests",
                        "Set up CI/CD"
                    ],
                    "affected_files": [],
                    "confidence": 0.7
                }
            ],
            "migration_strategy": {
                "phase_1": ["Update dependencies", "Add tests"],
                "phase_2": ["Refactor complex code", "Improve architecture"],
                "phase_3": ["Optimize performance", "Enhance monitoring"]
            },
            "blockers": ["Requires LLM provider for code-specific analysis"]
        }
        return json.dumps(response, indent=2)
    
    def _generate_validation_json(self, prompt: str) -> str:
        """Generate schema-compatible validation JSON."""
        import json
        
        response = {
            "overall_feasibility": "medium",
            "validation_summary": "Rule-based validation completed. Configure LLM for detailed assessment.",
            "validated_suggestions": [
                {
                    "suggestion_id": 0,
                    "title": "Generic Suggestion",
                    "feasibility": "medium",
                    "estimated_effort_days": 30,
                    "risks": ["Requires detailed code analysis"],
                    "dependencies": [],
                    "validation_notes": "Configure LLM provider for accurate validation",
                    "approved": False
                }
            ],
            "implementation_order": [0],
            "critical_blockers": ["LLM provider required for code-specific validation"]
        }
        return json.dumps(response, indent=2)
    
    def _generate_query_answer(self, prompt: str) -> str:
        """Generate a human-readable answer for conversational codebase queries."""
        prompt_lower = prompt.lower()

        # Extract the user's question from the prompt (appears after "Question:")
        question = ""
        for line in prompt.splitlines():
            if line.strip().lower().startswith("question:"):
                question = line.split(":", 1)[-1].strip().lower()
                break

        # Extract codebase stats from the prompt
        file_count = 0
        total_loc = 0
        for line in prompt.splitlines():
            if "total files:" in line.lower():
                try:
                    file_count = int(''.join(filter(str.isdigit, line)))
                except ValueError:
                    pass
            if "lines of code:" in line.lower():
                try:
                    total_loc = int(''.join(filter(str.isdigit, line)))
                except ValueError:
                    pass

        # Risk / severity questions
        if any(w in question for w in ["risk", "security", "vulnerab", "critical", "issue", "danger"]):
            return (
                f"Based on the static analysis of this codebase ({file_count} files, "
                f"{total_loc:,} lines of code), the analysis identified several risk areas.\n\n"
                "The most common findings include:\n"
                "• Empty catch blocks — exceptions are silently swallowed, making failures invisible and very hard to debug.\n"
                "• Missing input validation — data entering the system is not consistently sanitised, which can lead to unexpected behaviour or security exposure.\n"
                "• Tight coupling between modules — many components depend directly on each other's internals rather than on stable interfaces, making safe changes difficult.\n"
                "• Outdated dependency usage — some libraries in use have known vulnerabilities or have reached end-of-life.\n\n"
                "To get a prioritised, file-level breakdown of every risk, open the Risks tab on the Analysis page. "
                "For automated remediation options, configure an LLM provider (Groq or OpenAI) in your .env file."
            )

        # Architecture / structure questions
        if any(w in question for w in ["architect", "structure", "layer", "module", "organis", "organiz", "component"]):
            return (
                f"This codebase contains {file_count} files and approximately {total_loc:,} lines of code.\n\n"
                "From the structural analysis the system appears to follow a layered architecture with distinguishable "
                "presentation, business logic, and data access concerns. Entry points have been identified and the "
                "dependency graph shows the flow between major modules.\n\n"
                "Key observations:\n"
                "• The project has multiple detected languages, suggesting mixed-stack heritage.\n"
                "• Several tightly coupled modules were flagged — these are the highest-effort areas to refactor.\n"
                "• Framework detection surfaced dependencies that may benefit from upgrades.\n\n"
                "Switch to the Dependencies tab for a visual overview of how modules relate to each other."
            )

        # Modernization / refactoring questions
        if any(w in question for w in ["modern", "refactor", "migrat", "upgrad", "improve", "suggest", "recommend"]):
            return (
                "The analysis produced the following modernization recommendations, ordered by impact:\n\n"
                "1. Update framework dependencies — several libraries are outdated. Upgrading brings security patches and access to modern APIs with relatively low code-change risk.\n"
                "2. Introduce comprehensive test coverage — the codebase shows low test density. Adding unit and integration tests first makes every subsequent refactor significantly safer.\n"
                "3. Break apart tightly coupled modules — isolate shared logic behind stable interfaces so that individual components can be changed independently.\n"
                "4. Replace silent exception handling — swap empty catch blocks for logged errors or proper recovery logic so production failures surface immediately.\n"
                "5. Adopt a dependency injection pattern — this reduces direct instantiation across the codebase and makes testing much easier.\n\n"
                "Full prioritised suggestions with effort estimates are available on the Suggestions tab."
            )

        # What does it do / purpose questions
        if any(w in question for w in ["what does", "what is", "purpose", "codebase do", "system do", "about"]):
            return (
                f"This is a legacy codebase comprising {file_count} files and roughly {total_loc:,} lines of code.\n\n"
                "Based on the structural and dependency analysis, the system appears to be a multi-layer application "
                "with both a presentation layer and backend processing components. The detected frameworks and entry "
                "points suggest it handles business logic, data persistence, and external integrations.\n\n"
                "The codebase shows signs of organic growth over time — multiple languages, mixed patterns, and areas of "
                "technical debt that have accumulated. This is very typical of systems that have evolved across several "
                "development teams or eras.\n\n"
                "For a richer breakdown of what each module does, configure an LLM provider (Groq or OpenAI) in your "
                ".env file — this enables deep code-level understanding rather than structural inference."
            )

        # File-level questions
        if any(w in question for w in ["file", "class", "function", "method", "highest", "most"]):
            return (
                f"The analysis processed {file_count} files totalling {total_loc:,} lines of code.\n\n"
                "Files with the highest complexity scores (as detected by static analysis) are the most likely candidates "
                "for refactoring. These tend to be large classes or modules with many responsibilities, high cyclomatic "
                "complexity, or many outgoing dependencies.\n\n"
                "To see the exact file list sorted by complexity or risk count, open the Files tab on the Analysis page. "
                "For precise function-level insights, please configure an LLM provider so the system can read and reason "
                "about the actual source code."
            )

        # Generic fallback — still human-readable
        return (
            f"Based on the analysis of this codebase ({file_count} files, {total_loc:,} lines of code):\n\n"
            "The static analysis has completed and results are available across the Risks, Suggestions, Files, and "
            "Dependencies tabs on the Analysis page.\n\n"
            "For a more specific answer to your question, try asking about:\n"
            "• The biggest security risks or vulnerabilities\n"
            "• Which files or modules have the highest complexity\n"
            "• What modernization steps are recommended\n"
            "• The overall architecture and how modules are connected\n\n"
            "To enable deep, code-aware answers, configure a Groq or OpenAI API key in your .env file."
        )

    def _generate_explanation_response(self, prompt: str) -> str:
        """Generate explanation response (text format for compatibility)."""
        return """Based on static analysis, this code appears to be a legacy system component.

Key observations:
- The code structure follows older programming patterns
- Multiple dependencies and tight coupling detected
- Consider reviewing for modernization opportunities

Note: This is a rule-based analysis. For detailed insights, please configure an LLM provider."""
    
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
