# for IBM hackathon
"""
Bob-Powered Feature Endpoints — High-Impact Demo Features

Endpoints:
- /jobs/{job_id}/onboarding — New developer onboarding brief
- /jobs/{job_id}/diagram — Auto-generated Mermaid architecture diagram
- /jobs/{job_id}/migration-score — Migration readiness score (0-100)
- /jobs/{job_id}/transform — Side-by-side code transformation preview
- /explain — Stateless "Explain This Line" micro-query
- /jobs/{job_id}/stream — SSE streaming progress
"""

import logging
import json
import math
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Path, Query, status, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.storage.database import get_db_session, get_db
from app.storage.models import Job, File, AnalysisResult, Risk, Suggestion, JobStatusEnum
from app.storage.repositories import (
    get_job_repository, get_file_repository,
    get_risk_repository, get_suggestion_repository,
    get_analysis_result_repository,
)
from app.llm.provider_chain import get_llm_chain
from app.llm.prompts import PromptTemplates
from app.middleware.error_handler import NotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Request / Response Schemas ──────────────────────────────────────

class ExplainRequest(BaseModel):
    code: str = Field(..., description="Code snippet to explain")
    language: Optional[str] = Field("auto", description="Programming language")

class ExplainResponse(BaseModel):
    explanation: str
    language: str
    provider: str

class TransformRequest(BaseModel):
    file_path: str = Field(..., description="File path to transform")
    suggestion_id: Optional[str] = Field(None, description="Suggestion ID to apply")

class MigrationScoreResponse(BaseModel):
    overall_score: float = Field(..., description="Migration readiness 0-100")
    sub_scores: Dict[str, float]
    grade: str
    summary: str
    top_blockers: List[str]

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message to Bob")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Bob's reply")
    provider: str = Field(..., description="The LLM provider used")

class GenerateTestsRequest(BaseModel):
    file_path: str = Field(..., description="File to generate tests for")

class GenerateTestsResponse(BaseModel):
    file_path: str
    test_code: str
    test_framework: str
    coverage_estimate: str
    provider: str


# ─── 1. Explain This Line (§4.8) ────────────────────────────────────

@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Bob: Explain this code",
    description="Stateless micro-query — paste any code snippet and get Bob's explanation in seconds",
    tags=["Bob Features"],
)
async def explain_code(request: ExplainRequest):
    """Zero-friction explain endpoint. No job required."""
    llm = get_llm_chain()
    prompt = f"""You are IBM Bob, an expert legacy code analyst.
Explain this {request.language} code snippet clearly and concisely in 3-5 sentences.
Focus on what it does, any risks, and any modernization opportunities.

```{request.language}
{request.code[:3000]}
```"""

    response = await llm.generate(
        prompt=prompt,
        system_prompt="You are IBM Bob — a friendly, expert AI development partner for legacy code modernization.",
        temperature=0.3,
        max_tokens=800,
    )

    return ExplainResponse(
        explanation=response.content or "Unable to generate explanation. Please try again.",
        language=request.language or "auto",
        provider=response.provider,
    )


# ─── 2. Onboarding Brief (§4.3) ─────────────────────────────────────

@router.get(
    "/jobs/{job_id}/onboarding",
    summary="Bob: New developer onboarding brief",
    description="Generates a structured learning path and key-files-first guide for new developers",
    tags=["Bob Features"],
)
async def get_onboarding_brief(
    job_id: str = Path(...),
    db: Session = Depends(get_db_session),
):
    job_repo = get_job_repository(db)
    job = job_repo.get_job(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    files = get_file_repository(db).get_files_by_job(job_id)
    risks = get_risk_repository(db).get_risks_by_job(job_id)
    suggestions = get_suggestion_repository(db).get_suggestions_by_job(job_id)

    # Sort files by complexity (highest first) to find hotspots
    sorted_files = sorted(files, key=lambda f: f.complexity_score or 0, reverse=True)
    top_files = [f.file_path for f in sorted_files[:5]]
    entry_points = [f.file_path for f in files if (f.file_type or "").lower() in ("main", "entry", "source")][:5]
    if not entry_points:
        entry_points = [f.file_path for f in files[:3]]

    # Count languages
    lang_counts: Dict[str, int] = {}
    for f in files:
        lang = str(f.language or "unknown").lower()
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

    critical_risks = [r for r in risks if str(r.level).lower() in ("critical", "high")]

    # Build LLM prompt
    context = (
        f"Files: {len(files)}, Languages: {lang_counts}, "
        f"Risks: {len(risks)} ({len(critical_risks)} critical/high), "
        f"Suggestions: {len(suggestions)}"
    )
    llm = get_llm_chain()
    prompt = f"""You are IBM Bob. Generate a concise onboarding brief for a new developer joining this legacy codebase.

Codebase summary: {context}
Top complexity hotspots: {top_files}
Entry points: {entry_points}

Return a JSON object with these keys:
- "welcome_summary": 2-3 sentence overview of the codebase
- "start_here": list of 3-5 file paths a new developer should read FIRST
- "key_patterns": list of 3-5 important patterns or conventions used
- "danger_zones": list of 2-3 areas to be careful with (high risk/complexity)
- "learning_path": ordered list of 4-6 steps to ramp up
- "estimated_ramp_up_hours": integer estimate

Return ONLY valid JSON, no markdown."""

    response = await llm.generate(prompt=prompt, temperature=0.4, max_tokens=1200)

    # Parse LLM response or return structured fallback
    try:
        brief = json.loads(response.content)
    except (json.JSONDecodeError, TypeError):
        brief = {
            "welcome_summary": response.content[:500] if response.content else "Analysis complete.",
            "start_here": top_files[:5],
            "key_patterns": ["Repository pattern", "Multi-language legacy stack"],
            "danger_zones": [r.title for r in critical_risks[:3]] if critical_risks else ["No critical risks detected"],
            "learning_path": ["1. Read entry points", "2. Review high-complexity files", "3. Check risk report", "4. Explore suggestions"],
            "estimated_ramp_up_hours": max(4, len(files) // 2),
        }

    return {"job_id": job_id, "onboarding_brief": brief, "provider": response.provider}


# ─── 3. Architecture Diagram (§4.5) ─────────────────────────────────

@router.get(
    "/jobs/{job_id}/diagram",
    summary="Bob: Auto-generated architecture diagram",
    description="Returns a Mermaid.js diagram string from the dependency graph",
    tags=["Bob Features"],
)
async def get_architecture_diagram(
    job_id: str = Path(...),
    db: Session = Depends(get_db_session),
):
    job_repo = get_job_repository(db)
    job = job_repo.get_job(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    # Get analysis result for dependency graph
    result = db.query(AnalysisResult).filter(
        AnalysisResult.job_id == job_id,
        AnalysisResult.result_type == "complete_analysis",
    ).first()

    files = get_file_repository(db).get_files_by_job(job_id)
    risks = get_risk_repository(db).get_risks_by_job(job_id)

    # Build risk lookup
    risk_files = set()
    for r in risks:
        if r.affected_files:
            affected = r.affected_files if isinstance(r.affected_files, list) else []
            for af in affected:
                fname = af.get("file_path", af) if isinstance(af, dict) else str(af)
                risk_files.add(fname)

    # Build Mermaid diagram
    lines = ["graph TD"]
    node_ids: Dict[str, str] = {}

    for i, f in enumerate(files[:30]):  # Cap at 30 nodes for readability
        nid = f"F{i}"
        label = str(f.file_path).split("/")[-1].split("\\")[-1]
        lang = str(f.language or "unknown").upper()
        node_ids[str(f.file_path)] = nid
        lines.append(f'    {nid}["{label}<br/>{lang}"]')

    # Add dependency edges from analysis result
    if result and result.content:
        content = result.content if isinstance(result.content, dict) else {}
        arch = content.get("architecture", {})
        dep_graph = arch.get("dependency_graph", {})
        edges = dep_graph.get("edges", [])
        for edge in edges[:50]:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            if src in node_ids and tgt in node_ids:
                lines.append(f"    {node_ids[src]} --> {node_ids[tgt]}")

    # Style risky nodes
    for fpath, nid in node_ids.items():
        if fpath in risk_files:
            lines.append(f"    style {nid} fill:#ff6b6b,stroke:#c0392b,color:#fff")

    mermaid = "\n".join(lines)

    return {
        "job_id": job_id,
        "diagram_type": "mermaid",
        "diagram": mermaid,
        "node_count": len(node_ids),
        "risky_nodes": len(risk_files & set(node_ids.keys())),
    }


# ─── 4. Migration Readiness Score (§4.6) ────────────────────────────

@router.get(
    "/jobs/{job_id}/migration-score",
    response_model=MigrationScoreResponse,
    summary="Bob: Migration readiness score",
    description="Composite 0-100 score showing how ready this codebase is for modernization",
    tags=["Bob Features"],
)
async def get_migration_score(
    job_id: str = Path(...),
    db: Session = Depends(get_db_session),
):
    job_repo = get_job_repository(db)
    job = job_repo.get_job(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    files = get_file_repository(db).get_files_by_job(job_id)
    risks = get_risk_repository(db).get_risks_by_job(job_id)
    suggestions = get_suggestion_repository(db).get_suggestions_by_job(job_id)

    result = db.query(AnalysisResult).filter(
        AnalysisResult.job_id == job_id,
        AnalysisResult.result_type == "complete_analysis",
    ).first()

    # ── Sub-score calculations ──
    # 1. Complexity score (lower complexity = higher readiness)
    complexities = [f.complexity_score for f in files if f.complexity_score is not None]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 50
    complexity_score = max(0, min(100, 100 - avg_complexity))

    # 2. Risk score (fewer/lower risks = higher readiness)
    severity_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2, "info": 1}
    total_risk_weight = sum(
        severity_weights.get(str(r.level).lower(), 3) for r in risks
    )
    max_risk = max(1, len(files) * 10)
    risk_score = max(0, min(100, 100 - (total_risk_weight / max_risk * 100)))

    # 3. Test coverage estimate (test files / total files ratio)
    test_files = [f for f in files if "test" in str(f.file_path).lower() or str(f.file_type or "").lower() == "test"]
    test_ratio = len(test_files) / max(1, len(files))
    test_score = min(100, test_ratio * 500)  # 20% test files = 100 score

    # 4. Documentation score
    doc_files = [f for f in files if str(f.file_type or "").lower() in ("documentation", "config")]
    doc_ratio = len(doc_files) / max(1, len(files))
    doc_score = min(100, doc_ratio * 1000)

    # 5. Coupling score from dependency graph
    coupling_score = 70.0  # Default
    if result and result.content:
        content = result.content if isinstance(result.content, dict) else {}
        arch = content.get("architecture", {})
        dep = arch.get("dependency_graph", {})
        edges = dep.get("edges", [])
        nodes = dep.get("nodes", [])
        if nodes:
            avg_edges = len(edges) / max(1, len(nodes))
            coupling_score = max(0, min(100, 100 - avg_edges * 15))

    # ── Weighted composite ──
    weights = {
        "complexity": 0.25,
        "risk": 0.30,
        "test_coverage": 0.15,
        "documentation": 0.10,
        "coupling": 0.20,
    }
    sub_scores = {
        "complexity": round(complexity_score, 1),
        "risk": round(risk_score, 1),
        "test_coverage": round(test_score, 1),
        "documentation": round(doc_score, 1),
        "coupling": round(coupling_score, 1),
    }
    overall = sum(sub_scores[k] * weights[k] for k in weights)
    overall = round(max(0, min(100, overall)), 1)

    # Grade
    if overall >= 80: grade = "A"
    elif overall >= 60: grade = "B"
    elif overall >= 40: grade = "C"
    elif overall >= 20: grade = "D"
    else: grade = "F"

    # Top blockers
    blockers = []
    if risk_score < 40:
        blockers.append(f"{len([r for r in risks if str(r.level).lower() in ('critical','high')])} critical/high risks must be resolved")
    if test_score < 30:
        blockers.append("Insufficient test coverage for safe migration")
    if complexity_score < 30:
        blockers.append("High code complexity — refactor before migrating")
    if coupling_score < 30:
        blockers.append("Tight coupling makes incremental migration difficult")
    if not blockers:
        blockers.append("No major blockers — ready for phased migration")

    summary = f"This codebase scores {overall}/100 for migration readiness (Grade {grade}). "
    if overall >= 60:
        summary += "It is reasonably well-positioned for modernization with targeted improvements."
    elif overall >= 40:
        summary += "Moderate preparatory work is needed before migration can proceed safely."
    else:
        summary += "Significant remediation is required before modernization is feasible."

    return MigrationScoreResponse(
        overall_score=overall,
        sub_scores=sub_scores,
        grade=grade,
        summary=summary,
        top_blockers=blockers,
    )


# ─── 5. Side-by-Side Transform Preview (§4.2) ──────────────────────

@router.post(
    "/jobs/{job_id}/transform",
    summary="Bob: Code transformation preview",
    description="Generate modernized version of a file with before/after diff",
    tags=["Bob Features"],
)
async def transform_code(
    job_id: str = Path(...),
    request: TransformRequest = ...,
    db: Session = Depends(get_db_session),
):
    job_repo = get_job_repository(db)
    job = job_repo.get_job(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    # Find the file
    files = get_file_repository(db).get_files_by_job(job_id)
    target_file = None
    for f in files:
        if request.file_path in str(f.file_path):
            target_file = f
            break

    if not target_file:
        raise NotFoundError(f"File {request.file_path} not found in job {job_id}")

    # Read file content
    content = str(target_file.content or "")
    if not content:
        try:
            from pathlib import Path as P
            content = P(str(target_file.file_path)).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = "// File content unavailable"

    language = str(target_file.language or "unknown")

    # Get relevant suggestion context
    suggestion_context = ""
    if request.suggestion_id:
        suggestions = get_suggestion_repository(db).get_suggestions_by_job(job_id)
        for s in suggestions:
            if str(s.suggestion_id) == request.suggestion_id:
                suggestion_context = f"\nApply this suggestion: {s.title}\nDetails: {s.description}\nGuide: {s.rationale}"
                break

    llm = get_llm_chain()
    prompt = f"""You are IBM Bob. Transform this legacy {language} code into a modernized version.
{suggestion_context}

ORIGINAL CODE:
```{language}
{content[:3000]}
```

Return ONLY valid JSON with these keys:
- "before_snippet": the original code (first 50 lines)
- "after_snippet": the modernized equivalent
- "changes_summary": list of 3-5 key changes made
- "target_language": recommended target language/framework

Return ONLY JSON, no markdown."""

    response = await llm.generate(prompt=prompt, temperature=0.4, max_tokens=2000)

    try:
        result = json.loads(response.content)
    except (json.JSONDecodeError, TypeError):
        result = {
            "before_snippet": content[:1000],
            "after_snippet": response.content[:1000] if response.content else "// Transformation pending",
            "changes_summary": ["Modernization suggestions generated"],
            "target_language": "java",
        }

    return {
        "job_id": job_id,
        "file_path": request.file_path,
        "language": language,
        "transform": result,
        "provider": response.provider,
    }


# ─── 6. SSE Streaming Progress (§3.1) ───────────────────────────────

@router.get(
    "/jobs/{job_id}/stream",
    summary="Stream analysis progress (SSE)",
    description="Server-Sent Events endpoint for live stage-by-stage progress updates",
    tags=["Bob Features"],
)
async def stream_job_progress(job_id: str = Path(...)):
    """SSE endpoint that polls job status and streams updates."""
    import asyncio

    async def event_generator():
        last_stage = ""
        last_progress = -1.0
        max_polls = 300  # 5 minutes max

        for _ in range(max_polls):
            try:
                with get_db() as db:
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if not job:
                        yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                        return

                    current_status = job.status.value if hasattr(job.status, 'value') else str(job.status)
                    current_stage = str(job.current_stage or "unknown")
                    progress = float(job.progress or 0)

                    if current_stage != last_stage or progress != last_progress:
                        event = {
                            "job_id": job_id,
                            "status": current_status,
                            "stage": current_stage,
                            "progress": progress,
                        }
                        yield f"data: {json.dumps(event)}\n\n"
                        last_stage = current_stage
                        last_progress = progress

                    if current_status in ("completed", "failed", "cancelled"):
                        event = {
                            "job_id": job_id,
                            "status": current_status,
                            "stage": current_stage,
                            "progress": 100.0 if current_status == "completed" else progress,
                            "done": True,
                        }
                        yield f"data: {json.dumps(event)}\n\n"
                        return
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ─── 7. Live Chat (§4.9) ──────────────────────────────────────────

@router.post(
    "/jobs/{job_id}/chat",
    response_model=ChatResponse,
    summary="Bob: Live Chat",
    description="Multi-turn conversational AI interaction with memory persistence",
    tags=["Bob Features"],
)
async def chat_with_bob(
    job_id: str = Path(...),
    request: ChatRequest = ...,
    db: Session = Depends(get_db_session),
):
    from app.storage.repositories import get_query_repository
    
    job_repo = get_job_repository(db)
    job = job_repo.get_job(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")
        
    query_repo = get_query_repository(db)
    past_queries = query_repo.get_queries_by_job(job_id)
    
    # Build conversation history
    history_text = ""
    if past_queries:
        # Reverse to get chronological order (since they are fetched desc by created_at)
        for pq in reversed(past_queries[:5]): 
            history_text += f"User: {pq.question}\nBob: {pq.answer}\n\n"
            
    files = get_file_repository(db).get_files_by_job(job_id)
    file_names = [str(f.file_path).split("/")[-1] for f in files[:10]]
    
    llm = get_llm_chain()
    prompt = f"""You are IBM Bob, an AI assistant analyzing a legacy codebase with files: {file_names}.
    
Conversation History:
{history_text}

User's new message: {request.message}

Please respond concisely and helpfully."""

    response = await llm.generate(
        prompt=prompt,
        system_prompt="You are IBM Bob, the expert AI companion for legacy modernization.",
        temperature=0.6,
        max_tokens=1000
    )
    
    reply = response.content or "I'm sorry, I couldn't process that right now."
    
    # Save the interaction to the DB
    query_repo.create_query({
        "job_id": job_id,
        "question": request.message,
        "answer": reply,
        "confidence": 0.9,
    })
    
    return ChatResponse(reply=reply, provider=response.provider)


# ─── 8. Test Generation (§4.4) ──────────────────────────────────────

@router.post(
    "/jobs/{job_id}/generate-tests",
    response_model=GenerateTestsResponse,
    summary="Bob: Generate Unit Tests",
    description="Automatically generate boilerplate and edge-case unit tests based on code complexity",
    tags=["Bob Features"],
)
async def generate_tests(
    job_id: str = Path(...),
    request: GenerateTestsRequest = ...,
    db: Session = Depends(get_db_session),
):
    job_repo = get_job_repository(db)
    job = job_repo.get_job(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")
        
    files = get_file_repository(db).get_files_by_job(job_id)
    target_file = next((f for f in files if request.file_path in str(f.file_path)), None)
    
    if not target_file:
        raise NotFoundError(f"File {request.file_path} not found in job {job_id}")
        
    content = str(target_file.content or "")
    if not content:
        content = "// File content unavailable"
        
    language = str(target_file.language or "unknown")
    complexity = target_file.complexity_score or 1.0
    
    test_framework = "JUnit 5 / Mockito" if language.lower() == "java" else "pytest" if language.lower() == "python" else "Jest"
    
    llm = get_llm_chain()
    prompt = f"""You are IBM Bob. Generate robust {test_framework} unit tests for this {language} code.
The code has a complexity score of {complexity:.1f}. Ensure you generate edge cases to cover the cyclomatic complexity paths.

ORIGINAL CODE:
```{language}
{content[:4000]}
```

Return ONLY the test code implementation. No markdown formatting, just the raw code so it can be saved directly to a file."""

    response = await llm.generate(
        prompt=prompt,
        system_prompt="You are IBM Bob. Output ONLY raw test code. Do not wrap in markdown blocks.",
        temperature=0.3,
        max_tokens=2500
    )
    
    test_code = response.content or "// Failed to generate tests"
    test_code = test_code.replace("```" + language, "").replace("```java", "").replace("```", "").strip()
    
    return GenerateTestsResponse(
        file_path=request.file_path,
        test_code=test_code,
        test_framework=test_framework,
        coverage_estimate="~75-85% Line Coverage",
        provider=response.provider
    )

# Made with Bob
