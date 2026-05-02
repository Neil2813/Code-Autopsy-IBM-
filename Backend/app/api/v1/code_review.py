# for IBM hackathon
"""
Code Review API endpoint.

Returns structured, line-level findings for every file in a completed job,
grouped by file with severity, type, code snippet, problem, and fix.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Path, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.schemas import ErrorResponse
from app.storage.database import get_db_session
from app.storage.repositories import (
    get_job_repository,
    get_risk_repository,
    get_suggestion_repository,
)
from app.storage.models import JobStatusEnum, File
from app.llm.provider_chain import get_llm_chain
from app.middleware.error_handler import NotFoundError, ConflictError

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Schema helpers (plain dicts – validated by the LLM prompt)
# ---------------------------------------------------------------------------

SEVERITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _rank_issues(issues: list) -> list:
    """Sort issues within a file by descending severity."""
    return sorted(issues, key=lambda i: SEVERITY_RANK.get(i.get("severity", "LOW"), 0), reverse=True)


def _build_system_prompt() -> str:
    return (
        "You are a senior software engineer performing an expert code review. "
        "Your output is ONLY valid JSON — no prose, no markdown, no explanation outside the JSON. "
        "Group findings by file_path. "
        "For each issue include: line (integer or null), severity (HIGH|MEDIUM|LOW), "
        "type (runtime_safety|logic_bug|type_safety|performance|maintainability|security|reliability), "
        "title (short), code_snippet (exact or minimal), problem (direct technical explanation), "
        "fix (one-sentence direct fix). "
        "Do not invent issues. Do not repeat. Do not use vague phrases."
    )


def _build_review_prompt(
    file_summaries: list,
    risks: list,
    suggestions: list,
) -> str:
    files_text = "\n".join(
        f"- {f['file_path']} ({f['language'] or 'unknown'}, {f['lines_of_code'] or 0} LOC, "
        f"complexity={f['complexity_score'] or 'n/a'})"
        for f in file_summaries
    )

    risks_text = "\n".join(
        f"- [{r.get('severity','?').upper()}] {r.get('title','')} "
        f"(category={r.get('category','')}) → {r.get('recommendation','')[:120]}"
        for r in risks[:20]
    )

    suggestions_text = "\n".join(
        f"- [{s.get('priority','?').upper()}] {s.get('title','')} "
        f"→ {s.get('implementation_guide','')[:120]}"
        for s in suggestions[:20]
    )

    file_list = [f["file_path"] for f in file_summaries]

    return f"""Perform a precise code review for the following codebase.

FILES ({len(file_summaries)} total):
{files_text}

DETECTED RISKS:
{risks_text or '(none)'}

MODERNIZATION SUGGESTIONS:
{suggestions_text or '(none)'}

Return ONLY this JSON structure — fill every field:

{{
  "summary": {{
    "total_files": <int>,
    "total_issues": <int>,
    "high": <int>,
    "medium": <int>,
    "low": <int>
  }},
  "files": [
    {{
      "file_path": "<path>",
      "issues": [
        {{
          "line": <int or null>,
          "severity": "HIGH | MEDIUM | LOW",
          "type": "runtime_safety | logic_bug | type_safety | performance | maintainability | security | reliability",
          "title": "<short issue name>",
          "code_snippet": "<exact or minimal snippet>",
          "problem": "<what is wrong and why it matters>",
          "fix": "<exact fix in one sentence>"
        }}
      ]
    }}
  ]
}}

Only include files that have at least one issue. Files: {file_list}"""


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/jobs/{job_id}/code-review",
    summary="Get code review",
    description="Run a structured, line-level code review for a completed analysis job",
    responses={
        200: {"description": "Code review generated successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job not yet completed"},
    },
)
async def get_code_review(
    job_id: str = Path(..., description="Job identifier"),
    db: Session = Depends(get_db_session),
):
    """
    Generate a structured code review for every file in a completed job.

    Returns per-file findings with:
    - Exact line number (or null)
    - Severity (HIGH / MEDIUM / LOW)
    - Issue type
    - Exact code snippet
    - Plain-English problem description
    - One-sentence direct fix
    """
    logger.info(f"Code review requested for job {job_id}")

    try:
        # 1. Validate job
        job_repo = get_job_repository(db)
        job = job_repo.get_job(job_id)
        if not job:
            raise NotFoundError(f"Job {job_id} not found")

        job_status = job.status.value if hasattr(job.status, "value") else str(job.status)
        if job_status != JobStatusEnum.COMPLETED.value:
            raise ConflictError(
                f"Job {job_id} is not completed yet (status: {job_status})"
            )

        # 2. Load lightweight file metadata — excludes heavy content/parsed_content columns
        raw_files = db.query(
            File.id,
            File.file_path,
            File.language,
            File.lines_of_code,
            File.complexity_score,
        ).filter(File.job_id == job_id).all()

        file_summaries = [
            {
                "file_path": str(row.file_path),
                "language": str(row.language) if row.language else None,
                "lines_of_code": int(row.lines_of_code) if row.lines_of_code else None,
                "complexity_score": float(row.complexity_score) if row.complexity_score else None,
            }
            for row in raw_files
        ]

        # 3. Load risks and suggestions
        risk_repo = get_risk_repository(db)
        raw_risks = risk_repo.get_risks_by_job(job_id)
        risks = [
            {
                "title": r.title,
                "severity": str(r.level) if r.level else "medium",
                "category": r.category or "general",
                "recommendation": r.recommendation or "",
            }
            for r in raw_risks
        ]

        suggestion_repo = get_suggestion_repository(db)
        raw_suggestions = suggestion_repo.get_suggestions_by_job(job_id)
        suggestions = [
            {
                "title": s.title,
                "priority": str(s.priority) if s.priority else "medium",
                "implementation_guide": s.rationale or "",
            }
            for s in raw_suggestions
        ]

        # 4. Generate review via LLM
        llm_chain = get_llm_chain()
        prompt = _build_review_prompt(file_summaries, risks, suggestions)
        system_prompt = _build_system_prompt()

        llm_response = await llm_chain.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=4000,
        )

        if not llm_response.success:
            logger.error(f"LLM code review failed: {llm_response.error}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "LLM_ERROR",
                        "message": "Code review generation failed",
                        "details": {"error": llm_response.error},
                    }
                },
            )

        # 5. Parse and validate JSON from LLM
        import json
        import re

        raw_content = llm_response.content.strip()
        # Strip any markdown fences the model may have added
        raw_content = re.sub(r"^```[a-z]*\n?", "", raw_content, flags=re.IGNORECASE)
        raw_content = re.sub(r"\n?```$", "", raw_content.rstrip(), flags=re.IGNORECASE)

        try:
            review_data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}\nContent: {raw_content[:500]}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "PARSE_ERROR",
                        "message": "Code review output could not be parsed",
                        "details": {"error": str(e)},
                    }
                },
            )

        # 6. Sort issues within each file by severity
        for file_entry in review_data.get("files", []):
            file_entry["issues"] = _rank_issues(file_entry.get("issues", []))

        logger.info(
            f"Code review generated for job {job_id}: "
            f"{review_data.get('summary', {}).get('total_issues', '?')} issues across "
            f"{len(review_data.get('files', []))} files"
        )

        return review_data

    except (NotFoundError, ConflictError) as e:
        logger.warning(f"Code review failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Code review failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to generate code review",
                    "details": {"error": str(e)},
                }
            },
        )

# Made with Bob
