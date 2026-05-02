# for IBM hackathon
"""
LLM Prompt Templates

Prompt templates for different analysis stages.
"""

from typing import Dict, Any, List


class PromptTemplates:
    """Collection of prompt templates for LLM interactions."""
    
    @staticmethod
    def explain_code(code: str, language: str, context: Dict[str, Any]) -> str:
        """Generate prompt for code explanation."""
        return f"""You are an expert software engineer analyzing legacy code.

Language: {language}
Context: {context.get('file_path', 'Unknown file')}

Code to analyze:
```{language}
{code}
```

Please provide a clear, concise explanation of:
1. What this code does (main purpose and functionality)
2. Key components and their roles
3. Data flow and logic
4. Any notable patterns or approaches used

Keep the explanation practical and focused on understanding the code's behavior."""
    
    @staticmethod
    def analyze_risks(
        file_path: str,
        code: str,
        language: str,
        detected_risks: List[Dict[str, Any]]
    ) -> str:
        """Generate prompt for deep risk analysis with specific locations."""
        risks_summary = "\n".join([
            f"- Line {risk.get('line_start', '?')}: {risk.get('title', 'Unknown')} [{risk.get('severity', 'unknown')}]"
            for risk in detected_risks[:5]
        ]) if detected_risks else "No static analysis risks detected yet"
        
        # Count lines for validation
        line_count = code.count('\n') + 1
        
        return f"""You are a code analysis engine. Return ONLY valid JSON matching the exact schema below.

FILE: {file_path}
LANGUAGE: {language}
LINES: 1-{line_count}

STATIC ANALYSIS FINDINGS:
{risks_summary}

CODE:
```{language}
{code[:2000]}{"..." if len(code) > 2000 else ""}
```

REQUIRED JSON SCHEMA (return ONLY this, no markdown, no explanations):
{{
  "summary": "string: 1-2 sentence summary of code quality",
  "overall_severity": "critical|high|medium|low",
  "issues": [
    {{
      "title": "string: Specific issue (e.g., 'SQL Injection in login query')",
      "description": "string: What is wrong and impact",
      "severity": "critical|high|medium|low",
      "category": "security|logic_bug|performance|maintainability|architecture",
      "file_path": "{file_path}",
      "line_start": "integer: actual line number (1-{line_count})",
      "line_end": "integer: actual line number (1-{line_count})",
      "code_snippet": "string: exact code from those lines",
      "recommendation": "string: Specific action (e.g., 'Use parameterized queries')",
      "confidence": "float: 0.0-1.0"
    }}
  ],
  "what_to_fix_first": ["string: Top 3 actionable priorities"]
}}

STRICT RULES:
1. line_start and line_end MUST be integers between 1 and {line_count}
2. severity MUST be exactly: "critical", "high", "medium", or "low"
3. category MUST be exactly one of: "security", "logic_bug", "performance", "maintainability", "architecture"
4. code_snippet MUST be actual code from the file, not paraphrased
5. recommendation MUST be actionable (e.g., "Replace X with Y", not "improve code")
6. confidence MUST be a float between 0.0 and 1.0
7. NO markdown formatting, NO explanatory text, ONLY the JSON object
8. If no issues found, return empty issues array: {{"summary": "No significant issues", "overall_severity": "low", "issues": [], "what_to_fix_first": []}}"""
    
    @staticmethod
    def generate_modernization_suggestions(
        code: str,
        language: str,
        architecture_summary: str,
        risks: List[Dict[str, Any]]
    ) -> str:
        """Generate prompt for modernization suggestions."""
        risk_count = len(risks)
        high_severity_count = sum(1 for r in risks if r.get('severity') in ['critical', 'high'])
        
        return f"""You are a modernization architect. Return ONLY valid JSON matching the exact schema below.

LANGUAGE: {language}
ARCHITECTURE: {architecture_summary}
RISKS: {risk_count} total ({high_severity_count} high/critical)

CODE SAMPLE:
```{language}
{code[:1500]}{"..." if len(code) > 1500 else ""}
```

REQUIRED JSON SCHEMA (return ONLY this, no markdown):
{{
  "summary": "string: 1-2 sentence modernization assessment",
  "priority_score": "integer: 1-10 (urgency of modernization)",
  "suggestions": [
    {{
      "title": "string: Specific suggestion (e.g., 'Migrate to Spring Boot 3.x')",
      "description": "string: What to do and why",
      "priority": "critical|high|medium|low",
      "category": "framework|architecture|security|performance|testing",
      "estimated_effort": "low|medium|high",
      "benefits": ["string: Specific benefit 1", "string: Specific benefit 2"],
      "risks": ["string: Specific risk 1"],
      "implementation_steps": ["string: Step 1", "string: Step 2"],
      "affected_files": ["string: file path"],
      "confidence": "float: 0.0-1.0"
    }}
  ],
  "migration_strategy": {{
    "phase_1": ["string: Quick wins"],
    "phase_2": ["string: Core changes"],
    "phase_3": ["string: Final optimizations"]
  }},
  "blockers": ["string: Potential blocker 1"]
}}

STRICT RULES:
1. priority MUST be: "critical", "high", "medium", or "low"
2. category MUST be: "framework", "architecture", "security", "performance", or "testing"
3. estimated_effort MUST be: "low", "medium", or "high"
4. implementation_steps MUST be actionable (not vague)
5. benefits and risks MUST be specific and measurable
6. NO markdown, NO explanations, ONLY JSON"""
    
    @staticmethod
    def answer_query(
        question: str,
        codebase_context: Dict[str, Any],
        relevant_files: List[str]
    ) -> str:
        """Generate prompt for answering questions about codebase."""
        files_list = "\n".join([f"- {f}" for f in relevant_files[:10]])
        
        return f"""You are a code analysis assistant helping developers understand a legacy codebase.

Question: {question}

Codebase Context:
- Language: {codebase_context.get('language', 'Unknown')}
- Total Files: {codebase_context.get('file_count', 0)}
- Lines of Code: {codebase_context.get('total_loc', 0)}

Relevant Files:
{files_list}

Please provide a clear, accurate answer based on the codebase analysis. Include:
1. Direct answer to the question
2. Supporting evidence from the code
3. File references where applicable
4. Any caveats or limitations

Be specific and reference actual code elements when possible."""
    
    @staticmethod
    def generate_architecture_summary(
        files: List[Dict[str, Any]],
        dependencies: Dict[str, Any]
    ) -> str:
        """Generate prompt for architecture summary."""
        file_types = {}
        for file in files:
            lang = file.get('language', 'unknown')
            file_types[lang] = file_types.get(lang, 0) + 1
        
        files_summary = "\n".join([
            f"- {lang}: {count} files"
            for lang, count in file_types.items()
        ])
        
        return f"""You are a software architect analyzing a legacy system's structure.

Codebase Composition:
{files_summary}

Total Files: {len(files)}
Dependencies: {len(dependencies.get('nodes', []))} modules

Please provide:
1. High-level architecture overview
2. Identified layers (UI, business logic, data access, etc.)
3. Key components and their responsibilities
4. Integration points and external dependencies
5. Architecture patterns observed (monolith, layered, etc.)

Focus on understanding the system's structure and organization."""
    
    @staticmethod
    def validate_suggestions(
        suggestions: List[Dict[str, Any]],
        codebase_context: Dict[str, Any]
    ) -> str:
        """Generate prompt for validating suggestions."""
        suggestions_text = "\n".join([
            f"{i+1}. [{s.get('priority', '?')}] {s.get('title', 'Unknown')}"
            for i, s in enumerate(suggestions[:10])
        ])
        
        loc = codebase_context.get('total_loc', 0)
        language = codebase_context.get('language', 'Unknown')
        
        return f"""You are a technical validator. Return ONLY valid JSON matching the exact schema below.

CODEBASE: {language}, {loc} LOC
SUGGESTIONS TO VALIDATE: {len(suggestions)}

SUGGESTIONS:
{suggestions_text}

REQUIRED JSON SCHEMA (return ONLY this, no markdown):
{{
  "overall_feasibility": "high|medium|low",
  "validation_summary": "string: 1-2 sentence assessment",
  "validated_suggestions": [
    {{
      "suggestion_id": "integer: index from input (0-based)",
      "title": "string: original suggestion title",
      "feasibility": "high|medium|low",
      "estimated_effort_days": "integer: realistic days estimate",
      "risks": ["string: Specific risk 1", "string: Specific risk 2"],
      "dependencies": ["integer: indices of prerequisite suggestions"],
      "validation_notes": "string: Why feasible/infeasible",
      "approved": "boolean: true if recommended"
    }}
  ],
  "implementation_order": ["integer: suggestion indices in recommended order"],
  "critical_blockers": ["string: Blocker that prevents implementation"]
}}

STRICT RULES:
1. feasibility MUST be: "high", "medium", or "low"
2. estimated_effort_days MUST be realistic integer (1-365)
3. dependencies MUST reference valid suggestion indices
4. approved MUST be boolean true/false
5. implementation_order MUST list indices in dependency-aware order
6. NO markdown, NO explanations, ONLY JSON"""
    
    @staticmethod
    def generate_test_recommendations(
        code: str,
        language: str,
        complexity: float
    ) -> str:
        """Generate prompt for test recommendations."""
        return f"""You are a test automation expert analyzing code that needs test coverage.

Language: {language}
Complexity Score: {complexity:.2f}

Code:
```{language}
{code[:1000]}...
```

Please recommend:
1. Types of tests needed (unit, integration, e2e)
2. Critical test cases to cover
3. Edge cases and error scenarios
4. Test framework recommendations
5. Mocking strategies for dependencies

Focus on practical, high-value test coverage."""
    
    @staticmethod
    def system_prompt_for_stage(stage: str) -> str:
        """Get system prompt for a specific analysis stage."""
        prompts = {
            "explain": "You are an expert software engineer specializing in legacy code analysis. Provide clear, accurate explanations of code behavior and structure.",
            "analyze": "You are a code quality and security expert. Identify risks, vulnerabilities, and technical debt with specific, actionable insights.",
            "recommend": "You are a modernization architect. Provide practical, prioritized recommendations for improving legacy systems.",
            "validate": "You are a technical reviewer. Assess feasibility and risks of proposed changes with realistic estimates.",
            "query": "You are a code analysis assistant. Answer questions about codebases with specific references and evidence."
        }
        return prompts.get(stage, "You are an AI assistant helping with code analysis and modernization.")

# Made with Bob
