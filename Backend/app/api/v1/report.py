# for IBM hackathon
"""
Report generation API endpoints.

This module provides endpoints for:
- Report generation
- Report download
- Report format conversion
"""

import logging
import json
import uuid
import base64
import html
import io
from datetime import datetime
from pathlib import Path as FilePath

from fastapi import APIRouter, Path, status, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.schemas import ErrorResponse, ReportRequest, ReportResponse
from app.storage.database import get_db_session
from app.storage.repositories import (
    get_job_repository,
    get_risk_repository,
    get_suggestion_repository
)
from app.storage.models import JobStatusEnum
from app.middleware.error_handler import NotFoundError, ConflictError

logger = logging.getLogger(__name__)

router = APIRouter()


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0, "unknown": 0}


def clean_label(value) -> str:
    return str(value or "Unknown").replace("_", " ").replace("-", " ").title()


def clean_title(value) -> str:
    return str(value or "Untitled").replace("Fix:", "").strip()


def strip_markdown(value: str) -> str:
    return (
        str(value or "")
        .replace("**", "")
        .replace("`", "")
        .replace("```", "")
        .strip()
    )


def first_file_refs(refs, limit: int = 3) -> list[dict]:
    values = []
    for ref in refs or []:
        if isinstance(ref, dict):
            values.append({
                "file_path": ref.get("file_path", "Unknown"),
                "line_start": ref.get("line_start"),
                "line_end": ref.get("line_end"),
                "snippet": ref.get("snippet") or ref.get("code_snippet"),
            })
    return values[:limit]


def build_report_data(job, files, risks, suggestions, analysis_result=None) -> dict:
    arch_data = analysis_result.content.get("architecture", {}) if analysis_result and analysis_result.content else {}
    total_lines = sum(f.lines_of_code or 0 for f in files)

    grouped_risks = {}
    for risk in risks:
        key = (clean_title(risk.title).lower(), str(risk.category or "").lower())
        item = grouped_risks.setdefault(key, {
            "title": clean_title(risk.title),
            "severity": str(risk.level or "unknown").lower(),
            "category": clean_label(risk.category),
            "description": strip_markdown(risk.description),
            "recommendation": strip_markdown(risk.recommendation),
            "instances": 0,
            "affected_files": [],
        })
        item["instances"] += max(1, len(risk.affected_files or []))
        item["affected_files"].extend(first_file_refs(risk.affected_files, limit=10))
        if SEVERITY_RANK.get(str(risk.level or "").lower(), 0) > SEVERITY_RANK.get(item["severity"], 0):
            item["severity"] = str(risk.level or "unknown").lower()

    grouped_suggestions = {}
    for suggestion in suggestions:
        key = clean_title(suggestion.title).lower()
        item = grouped_suggestions.setdefault(key, {
            "title": clean_title(suggestion.title),
            "priority": suggestion.priority,
            "effort": suggestion.effort_estimate or "medium",
            "description": strip_markdown(suggestion.description),
            "instances": 0,
            "before": suggestion.before_snippet,
            "after": suggestion.after_snippet,
        })
        item["instances"] += max(1, len(suggestion.affected_files or []))

    risks_list = sorted(
        grouped_risks.values(),
        key=lambda item: (-SEVERITY_RANK.get(item["severity"], 0), item["title"]),
    )
    suggestions_list = sorted(
        grouped_suggestions.values(),
        key=lambda item: (-(item["priority"] or 0), item["title"]),
    )

    recommended_steps = []
    seen_steps = set()
    for risk in risks_list[:5]:
        step = risk["recommendation"] or f"Review {risk['title']}."
        if step and step not in seen_steps:
            seen_steps.add(step)
            recommended_steps.append(step)

    migration_blockers = []
    seen_blockers = set()
    for risk in risks_list:
        if risk["severity"] in {"critical", "high"} and risk["title"] not in seen_blockers:
            seen_blockers.add(risk["title"])
            migration_blockers.append(risk["title"])
        if len(migration_blockers) >= 5:
            break

    return {
        "title": "Legacy Code Modernization Report",
        "job_id": str(job.id),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_files": len(files),
            "total_lines": total_lines,
            "total_risks": len(risks),
            "unique_risk_types": len(risks_list),
            "total_suggestions": len(suggestions),
            "unique_suggestion_types": len(suggestions_list),
        },
        "architecture": {
            "project_type": clean_label(arch_data.get("project_type", "Unknown")),
            "primary_language": str(arch_data.get("primary_language", "Unknown")).upper(),
            "frameworks": arch_data.get("detected_frameworks", []),
        },
        "risks": risks_list,
        "suggestions": suggestions_list,
        "migration_blockers": migration_blockers,
        "recommended_next_steps": recommended_steps,
        "dependency_graph": (analysis_result.content.get("dependency_graph", {}) if analysis_result and analysis_result.content else {}),
    }


def generate_markdown_report(
    job,
    files,
    risks,
    suggestions,
    sections,
    include_code_snippets=True,
    include_dependency_graph=True,
    analysis_result=None
) -> str:
    """Generate a markdown format report with configurable sections."""
    lines = []
    lines.append("# Legacy Code Modernization Report\n")
    lines.append(f"**Job ID:** {job.id}\n")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z\n")
    lines.append("\n---\n")
    
    # Check which sections to include
    include_all = "all" in [s.value if hasattr(s, 'value') else s for s in sections]
    section_values = [s.value if hasattr(s, 'value') else s for s in sections]
    
    # Summary
    if include_all or "summary" in section_values:
        lines.append("\n## Summary\n")
        lines.append(f"- **Total Files:** {len(files)}\n")
        lines.append(f"- **Total Lines of Code:** {sum(f.lines_of_code or 0 for f in files)}\n")
        lines.append(f"- **Risks Found:** {len(risks)}\n")
        lines.append(f"- **Suggestions:** {len(suggestions)}\n")
    
    # Architecture
    if include_all or "architecture" in section_values:
        lines.append("\n## Architecture Overview\n")
        if analysis_result and analysis_result.content:
            arch_data = analysis_result.content.get("architecture", {})
            if arch_data:
                lines.append(f"**Project Type:** {arch_data.get('project_type', 'Unknown')}\n")
                lines.append(f"**Primary Language:** {arch_data.get('primary_language', 'Unknown')}\n")
                frameworks = arch_data.get('detected_frameworks', [])
                if frameworks:
                    lines.append(f"**Frameworks:** {', '.join(frameworks)}\n")
    
    # Risks
    if (include_all or "risks" in section_values) and risks:
        lines.append("\n## Detected Risks\n")
        for i, risk in enumerate(risks[:10], 1):
            lines.append(f"\n### {i}. {risk.title}\n")
            lines.append(f"**Severity:** {risk.level}\n")
            lines.append(f"**Category:** {risk.category}\n")
            lines.append(f"\n{risk.description}\n")
            if risk.recommendation:
                lines.append(f"\n**Recommendation:** {risk.recommendation}\n")
            
            # Include code snippets if requested
            if include_code_snippets and risk.affected_files:
                lines.append(f"\n**Affected Files:**\n")
                for file_ref in risk.affected_files[:3]:  # Limit to 3 files
                    if isinstance(file_ref, dict):
                        lines.append(f"- {file_ref.get('file_path', 'Unknown')}\n")
    
    # Suggestions
    if (include_all or "suggestions" in section_values) and suggestions:
        lines.append("\n## Modernization Suggestions\n")
        for i, sug in enumerate(suggestions[:10], 1):
            lines.append(f"\n### {i}. {sug.title}\n")
            lines.append(f"**Priority:** {sug.priority}\n")
            lines.append(f"**Effort:** {sug.effort_estimate}\n")
            lines.append(f"\n{sug.description}\n")
            
            # Include code snippets if requested
            if include_code_snippets and sug.before_snippet:
                lines.append(f"\n**Before:**\n```\n{sug.before_snippet}\n```\n")
            if include_code_snippets and sug.after_snippet:
                lines.append(f"\n**After:**\n```\n{sug.after_snippet}\n```\n")
    
    # Dependencies
    if (include_all or "dependencies" in section_values) and include_dependency_graph:
        lines.append("\n## Dependency Graph\n")
        if analysis_result and analysis_result.content:
            dep_graph = analysis_result.content.get("dependency_graph", {})
            if dep_graph:
                nodes = dep_graph.get("nodes", [])
                edges = dep_graph.get("edges", [])
                lines.append(f"**Nodes:** {len(nodes)}\n")
                lines.append(f"**Edges:** {len(edges)}\n")
                lines.append("\n*Note: Full dependency graph available in JSON format*\n")
    
    # Migration Blockers
    if include_all or "migration_blockers" in section_values:
        lines.append("\n## Migration Blockers\n")
        if analysis_result and analysis_result.content:
            blockers = analysis_result.content.get("migration_blockers", [])
            if blockers:
                for blocker in blockers[:5]:
                    lines.append(f"- {blocker}\n")
    
    # Next Steps
    if include_all or "next_steps" in section_values:
        lines.append("\n## Recommended Next Steps\n")
        if analysis_result and analysis_result.content:
            steps = analysis_result.content.get("recommended_next_steps", [])
            if steps:
                for step in steps[:5]:
                    lines.append(f"1. {step}\n")
    
    lines.append("\n---\n")
    lines.append("\n*Generated by IBM BOB - Legacy Code Modernization Assistant*\n")
    
    return "".join(lines)


def generate_clean_text_report(report_data: dict, sections) -> str:
    section_values = [s.value if hasattr(s, "value") else s for s in sections]
    include_all = "all" in section_values
    lines = [
        report_data["title"],
        f"Job ID: {report_data['job_id']}",
        f"Generated: {report_data['generated_at']}",
        "",
    ]

    if include_all or "summary" in section_values:
        summary = report_data["summary"]
        lines.extend([
            "Summary",
            f"Total files: {summary['total_files']}",
            f"Total lines of code: {summary['total_lines']}",
            f"Risks found: {summary['total_risks']} ({summary['unique_risk_types']} unique types)",
            f"Suggestions: {summary['total_suggestions']} ({summary['unique_suggestion_types']} unique types)",
            "",
        ])

    if include_all or "architecture" in section_values:
        arch = report_data["architecture"]
        lines.extend([
            "Architecture Overview",
            f"Project type: {arch['project_type']}",
            f"Primary language: {arch['primary_language']}",
            f"Frameworks: {', '.join(arch['frameworks']) if arch['frameworks'] else 'None detected'}",
            "",
        ])

    if (include_all or "risks" in section_values) and report_data["risks"]:
        lines.append("Detected Risks")
        for index, risk in enumerate(report_data["risks"][:15], 1):
            lines.extend([
                f"{index}. {risk['title']}",
                f"Severity: {clean_label(risk['severity'])}",
                f"Category: {risk['category']}",
                f"Instances: {risk['instances']}",
                f"Problem: {risk['description']}",
                f"Fix: {risk['recommendation']}",
            ])
            if risk["affected_files"]:
                lines.append("Affected examples:")
                for ref in risk["affected_files"][:3]:
                    line = f"  - {ref['file_path']}"
                    if ref.get("line_start"):
                        line += f":{ref['line_start']}"
                    lines.append(line)
            lines.append("")

    if (include_all or "suggestions" in section_values) and report_data["suggestions"]:
        lines.append("Modernization Suggestions")
        for index, suggestion in enumerate(report_data["suggestions"][:10], 1):
            lines.extend([
                f"{index}. {suggestion['title']}",
                f"Priority: {suggestion['priority']}",
                f"Effort: {suggestion['effort']}",
                f"Instances: {suggestion['instances']}",
                f"Action: {suggestion['description']}",
                "",
            ])

    if (include_all or "dependencies" in section_values) and report_data["dependency_graph"]:
        graph = report_data["dependency_graph"]
        lines.extend([
            "Dependency Graph",
            f"Nodes: {len(graph.get('nodes', []))}",
            f"Edges: {len(graph.get('edges', []))}",
            "",
        ])

    if include_all or "migration_blockers" in section_values:
        lines.append("Migration Blockers")
        if report_data["migration_blockers"]:
            lines.extend([f"- {item}" for item in report_data["migration_blockers"]])
        else:
            lines.append("No high severity blockers were identified.")
        lines.append("")

    if include_all or "next_steps" in section_values:
        lines.append("Recommended Next Steps")
        if report_data["recommended_next_steps"]:
            lines.extend([f"{index}. {step}" for index, step in enumerate(report_data["recommended_next_steps"], 1)])
        else:
            lines.append("No next steps were generated.")
        lines.append("")

    lines.append("Generated by IBM BOB - Legacy Code Modernization Assistant")
    return "\n".join(lines)


def generate_html_report(markdown_content: str) -> str:
    """Generate a simple standalone HTML report from the markdown report content."""
    body_lines = []
    in_list = False
    in_code = False
    code_lines = []

    for raw_line in markdown_content.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                body_lines.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if line.startswith("- "):
            if not in_list:
                body_lines.append("<ul>")
                in_list = True
            body_lines.append(f"<li>{html.escape(line[2:])}</li>")
            continue

        if in_list:
            body_lines.append("</ul>")
            in_list = False

        if not line or line == "---":
            continue
        if line.startswith("# "):
            body_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body_lines.append(f"<h3>{html.escape(line[4:])}</h3>")
        else:
            text = html.escape(line).replace("**", "")
            body_lines.append(f"<p>{text}</p>")

    if in_list:
        body_lines.append("</ul>")

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Legacy Code Modernization Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #172033; line-height: 1.55; }}
    h1 {{ color: #4f46e5; }}
    h2 {{ margin-top: 28px; border-bottom: 1px solid #d7dce5; padding-bottom: 6px; }}
    pre {{ background: #111827; color: #f9fafb; padding: 14px; border-radius: 6px; overflow-x: auto; }}
    li {{ margin: 6px 0; }}
  </style>
</head>
<body>
{chr(10).join(body_lines)}
</body>
</html>"""


def generate_pdf_report(markdown_content: str) -> bytes:
    """Generate a PDF report using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    story = []
    in_code = False
    code_lines = []

    for raw_line in markdown_content.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["Code"]))
                story.append(Spacer(1, 8))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(raw_line)
            continue
        if not line or line == "---":
            continue

        clean = html.escape(line.replace("**", ""))
        if line.startswith("# "):
            story.append(Paragraph(clean[2:], styles["Title"]))
        elif line.startswith("## "):
            story.append(Spacer(1, 10))
            story.append(Paragraph(clean[3:], styles["Heading2"]))
        elif line.startswith("### "):
            story.append(Paragraph(clean[4:], styles["Heading3"]))
        elif line.startswith("- "):
            story.append(Paragraph(f"• {clean[2:]}", styles["BodyText"]))
        else:
            story.append(Paragraph(clean, styles["BodyText"]))
        story.append(Spacer(1, 6))

    doc.build(story)
    return buffer.getvalue()


@router.post(
    "/report",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate report",
    description="Generate a modernization report for analyzed code",
    responses={
        201: {"description": "Report generated successfully"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job not yet completed"},
    },
)
async def generate_report(request: ReportRequest, db: Session = Depends(get_db_session)):
    """
    Generate a modernization report for analyzed code.
    
    Supports multiple formats:
    - **Markdown**: Human-readable text format
    - **JSON**: Machine-readable structured data
    - **HTML**: Web-viewable format
    - **PDF**: Printable document format
    
    Report sections:
    - **Summary**: High-level overview
    - **Architecture**: System architecture analysis
    - **Risks**: Detected risks with severity levels
    - **Suggestions**: Modernization recommendations
    - **Dependencies**: Dependency graph visualization
    - **Migration Blockers**: Critical issues preventing migration
    - **Next Steps**: Recommended action plan
    
    Options:
    - Include/exclude code snippets
    - Include/exclude dependency graph
    - Select specific sections
    """
    logger.info(f"Received report generation request for job {request.job_id} in format {request.format}")
    
    try:
        # 1. Validate job exists and is completed (lightweight: no eager-load of file content)
        job_repo = get_job_repository(db)
        job = job_repo.get_job(request.job_id)
        
        if not job:
            raise NotFoundError(f"Job {request.job_id} not found")
        
        job_status_value = job.status.value if hasattr(job.status, 'value') else str(job.status)
        if job_status_value != JobStatusEnum.COMPLETED.value:
            raise ConflictError(
                f"Job {request.job_id} is not completed yet (status: {job_status_value})"
            )
        
        # 2. Load analysis results via targeted repos (avoids memory blowup from join-loading file content)
        from app.storage.repositories import get_file_repository, get_analysis_result_repository
        file_repo = get_file_repository(db)
        files = file_repo.get_files_by_job(request.job_id)

        risk_repo = get_risk_repository(db)
        risks = risk_repo.get_risks_by_job(request.job_id)
        
        suggestion_repo = get_suggestion_repository(db)
        suggestions = suggestion_repo.get_suggestions_by_job(request.job_id)
        
        # Load analysis result for additional data
        result_repo = get_analysis_result_repository(db)
        analysis_result = result_repo.get_result_by_job(request.job_id)
        
        # 3. Generate report in requested format (honoring all request fields)
        report_id = str(uuid.uuid4())
        
        markdown_content = generate_markdown_report(
            job,
            files,
            risks,
            suggestions,
            sections=request.sections,
            include_code_snippets=request.include_code_snippets,
            include_dependency_graph=request.include_dependency_graph,
            analysis_result=analysis_result
        )

        if request.format == "markdown":
            content = markdown_content
            size_bytes = len(content.encode('utf-8'))
        elif request.format == "json":
            report_data = {
                "job_id": request.job_id,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "summary": {
                    "total_files": len(files),
                    "total_lines": sum(f.lines_of_code or 0 for f in files),
                    "total_risks": len(risks),
                    "total_suggestions": len(suggestions)
                },
                "risks": [
                    {
                        "title": r.title,
                        "level": str(r.level) if r.level is not None else "unknown",
                        "category": r.category,
                        "description": r.description
                    }
                    for r in risks
                ],
                "suggestions": [
                    {
                        "title": s.title,
                        "priority": s.priority,  # type: ignore
                        "description": s.description
                    }
                    for s in suggestions
                ]
            }
            content = json.dumps(report_data, indent=2)
            size_bytes = len(content.encode('utf-8'))
        elif request.format == "html":
            content = generate_html_report(markdown_content)
            size_bytes = len(content.encode('utf-8'))
        elif request.format == "pdf":
            pdf_bytes = generate_pdf_report(markdown_content)
            content = base64.b64encode(pdf_bytes).decode("ascii")
            size_bytes = len(pdf_bytes)
        else:
            content = f"Report format '{request.format}' not supported."
            size_bytes = len(content.encode('utf-8'))
        
        logger.info(f"Generated {request.format} report for job {request.job_id} ({size_bytes} bytes)")
        
        # 4. Return report response
        return ReportResponse(
            report_id=report_id,
            job_id=request.job_id,
            format=request.format,
            download_url=f"/api/v1/report/{report_id}/download",
            content=content,
            size_bytes=size_bytes,
            generated_at=datetime.utcnow().isoformat() + "Z"
        )
        
    except (NotFoundError, ConflictError) as e:
        logger.warning(f"Report generation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to generate report",
                    "details": {"error": str(e)},
                }
            },
        )


@router.get(
    "/report/{report_id}/download",
    response_class=FileResponse,
    summary="Download report",
    description="Download a generated report file",
    responses={
        200: {"description": "Report file"},
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
)
async def download_report(
    report_id: str = Path(..., description="Report identifier")
):
    """
    Download a generated report file.
    
    Returns the report file with appropriate content type:
    - Markdown: text/markdown
    - JSON: application/json
    - HTML: text/html
    - PDF: application/pdf
    """
    # TODO: Implement report download
    # 1. Validate report exists
    # 2. Get report file path
    # 3. Return file response
    
    logger.info(f"Received report download request for: {report_id}")
    
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "Report download endpoint not yet implemented",
                "details": {"report_id": report_id},
            }
        },
    )


@router.get(
    "/report/{report_id}",
    response_model=ReportResponse,
    summary="Get report metadata",
    description="Get metadata for a generated report",
    responses={
        200: {"description": "Report metadata retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
)
async def get_report_metadata(
    report_id: str = Path(..., description="Report identifier")
):
    """
    Get metadata for a generated report.
    
    Returns:
    - Report ID
    - Job ID
    - Format
    - Download URL
    - Size
    - Generation timestamp
    """
    # TODO: Implement report metadata retrieval
    # 1. Validate report exists
    # 2. Load report metadata
    # 3. Return response
    
    logger.info(f"Received report metadata request for: {report_id}")
    
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "Report metadata endpoint not yet implemented",
                "details": {"report_id": report_id},
            }
        },
    )

# Made with Bob
