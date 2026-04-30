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
        code: str,
        language: str,
        detected_risks: List[Dict[str, Any]]
    ) -> str:
        """Generate prompt for risk analysis."""
        risks_summary = "\n".join([
            f"- {risk.get('title', 'Unknown')}: {risk.get('description', '')}"
            for risk in detected_risks[:5]
        ])
        
        return f"""You are a security and code quality expert analyzing legacy code.

Language: {language}

Detected Issues (from static analysis):
{risks_summary}

Code:
```{language}
{code[:1000]}...
```

Please analyze and provide:
1. Severity assessment of detected issues
2. Additional risks not caught by static analysis
3. Security vulnerabilities
4. Maintainability concerns
5. Technical debt indicators

Focus on actionable insights."""
    
    @staticmethod
    def generate_modernization_suggestions(
        code: str,
        language: str,
        architecture_summary: str,
        risks: List[Dict[str, Any]]
    ) -> str:
        """Generate prompt for modernization suggestions."""
        return f"""You are a modernization architect helping migrate legacy systems.

Language: {language}
Architecture: {architecture_summary}

Current Issues:
{len(risks)} risks detected including security, complexity, and maintainability concerns.

Code Sample:
```{language}
{code[:1000]}...
```

Please provide:
1. Top 5 modernization priorities (ranked by impact)
2. Specific refactoring recommendations
3. Framework/library upgrade suggestions
4. Architecture improvements
5. Migration strategy (step-by-step approach)

Focus on practical, implementable suggestions."""
    
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
            f"{i+1}. {s.get('title', 'Unknown')}: {s.get('description', '')[:100]}"
            for i, s in enumerate(suggestions[:5])
        ])
        
        return f"""You are a technical reviewer validating modernization recommendations.

Codebase: {codebase_context.get('language', 'Unknown')} project
Size: {codebase_context.get('total_loc', 0)} lines of code

Proposed Suggestions:
{suggestions_text}

Please review and provide:
1. Feasibility assessment for each suggestion
2. Potential risks or challenges
3. Estimated effort (low/medium/high)
4. Dependencies between suggestions
5. Recommended implementation order

Be realistic about complexity and effort required."""
    
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
