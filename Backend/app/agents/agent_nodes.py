# for IBM hackathon
"""
LangGraph Agent Nodes.

This module implements the 8-stage analysis workflow:
1. Ingest - Load and validate files
2. Parse - Extract code structure
3. Classify - Categorize files and components
4. Analyze - Detect risks and patterns
5. Explain - Generate human-readable explanations
6. Recommend - Generate modernization suggestions
7. Validate - Verify recommendations
8. Report - Generate final report
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.agent_state import (
    AgentState,
    FileInfo,
    ParsedFile,
    RiskItem,
    SuggestionItem,
    normalize_language,
    normalize_file_info
)

logger = logging.getLogger(__name__)


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _make_file_reference(
    file_path: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    snippet: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a consistent file reference with proper line number handling.
    
    Args:
        file_path: Path to the file
        line_start: Starting line number (1-based)
        line_end: Ending line number (1-based), defaults to line_start
        snippet: Optional code snippet
        
    Returns:
        Standardized file reference dictionary
    """
    if line_end is None and line_start is not None:
        line_end = line_start
    
    return {
        "file_path": file_path,
        "line_start": line_start,
        "line_end": line_end,
        "snippet": snippet,
    }


def _context_snippet(lines: List[str], line_start: int, line_end: Optional[int] = None, radius: int = 1) -> str:
    line_end = line_end or line_start
    start_index = max(0, line_start - 1 - radius)
    end_index = min(len(lines), line_end + radius)
    return "\n".join(lines[start_index:end_index]).strip()


def _canonical_pattern(title: str, category: str = "") -> str:
    value = f"{category} {title}".lower().replace("-", " ").replace("_", " ")
    if "string comparison" in value:
        return "string_equality"
    if "string concatenation" in value or "string building" in value:
        return "string_concat_loop"
    if "raw collection" in value or "raw type" in value:
        return "raw_collection_type"
    if "mixed type" in value:
        return "mixed_type_collection"
    if "off by one" in value:
        return "off_by_one_loop"
    if "empty catch" in value or "exception swallowed" in value:
        return "empty_catch"
    if "unbounded loop" in value or "infinite loop" in value:
        return "unbounded_loop"
    if "recursive call" in value or "recursion" in value:
        return "unguarded_recursion"
    if "null dereference" in value:
        return "null_dereference"
    if "random exception" in value:
        return "random_exception"
    if "cache" in value and "null" in value:
        return "cache_null_ambiguity"
    if "procedural utility" in value:
        return "procedural_utility"
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "general"


STRICT_SEVERITY_BY_PATTERN = {
    "unbounded_execution": "critical",
    "unbounded_loop": "high",
    "unguarded_recursion": "high",
    "off_by_one_loop": "high",
    "null_dereference": "high",
    "random_exception": "high",
    "empty_catch": "high",
    "mixed_type_collection": "high",
    "cache_null_ambiguity": "high",
    "string_equality": "high",
    "raw_collection_type": "medium",
    "string_concat_loop": "medium",
    "procedural_utility": "low",
}


STRICT_CATEGORY_BY_PATTERN = {
    "unbounded_execution": "runtime_safety",
    "unbounded_loop": "runtime_safety",
    "unguarded_recursion": "runtime_safety",
    "off_by_one_loop": "runtime_safety",
    "null_dereference": "runtime_safety",
    "random_exception": "runtime_safety",
    "empty_catch": "runtime_safety",
    "mixed_type_collection": "type_safety",
    "cache_null_ambiguity": "logic_bug",
    "string_equality": "logic_bug",
    "raw_collection_type": "type_safety",
    "string_concat_loop": "performance",
    "procedural_utility": "architecture",
}


def _normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    pattern = issue.get("pattern_key") or _canonical_pattern(issue.get("title", ""), issue.get("category", ""))
    issue["pattern_key"] = pattern
    issue["level"] = STRICT_SEVERITY_BY_PATTERN.get(pattern, str(issue.get("level") or issue.get("severity") or "medium").lower())
    issue["category"] = STRICT_CATEGORY_BY_PATTERN.get(pattern, str(issue.get("category") or "maintainability").lower())
    issue["confidence"] = max(0.0, min(float(issue.get("confidence", 0.75)), 0.99))
    return issue


def _validate_issue(issue: Dict[str, Any]) -> bool:
    pattern = issue.get("pattern_key") or _canonical_pattern(issue.get("title", ""), issue.get("category", ""))
    refs = issue.get("affected_files") or []
    snippet = "\n".join(str(ref.get("snippet", "")) for ref in refs if isinstance(ref, dict))

    if pattern == "string_equality":
        if "==" not in snippet or "null" in snippet:
            return False
        return bool(re.search(r'"(?:\\.|[^"\\])*"', snippet) or re.search(r"\bString\b|\.\w*(?:Text|String|trim|substring|concat)\s*\(", snippet))

    if pattern == "string_concat_loop":
        return "+=" in snippet or bool(re.search(r"\w+\s*=\s*\w+\s*\+", snippet))

    return True


def _merge_file_references(refs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ordered = sorted(
        [ref for ref in refs if isinstance(ref, dict)],
        key=lambda ref: (ref.get("file_path", ""), ref.get("line_start") or 0),
    )
    merged: List[Dict[str, Any]] = []
    for ref in ordered:
        if not merged:
            merged.append(dict(ref))
            continue

        last = merged[-1]
        same_file = last.get("file_path") == ref.get("file_path")
        last_end = last.get("line_end") or last.get("line_start") or 0
        ref_start = ref.get("line_start") or 0
        if same_file and ref_start and last_end and ref_start <= last_end + 2:
            last["line_end"] = max(last_end, ref.get("line_end") or ref_start)
            if ref.get("snippet") and ref["snippet"] not in str(last.get("snippet", "")):
                last["snippet"] = f"{last.get('snippet', '')}\n{ref['snippet']}".strip()
        else:
            merged.append(dict(ref))
    return merged


def _refresh_risk_text(risk: Dict[str, Any]) -> Dict[str, Any]:
    pattern = risk.get("pattern_key")
    refs = risk.get("affected_files") or []
    first_snippet = ""
    for ref in refs:
        if isinstance(ref, dict) and ref.get("snippet"):
            snippet_lines = [line.strip() for line in str(ref["snippet"]).splitlines()]
            first_snippet = next((line for line in snippet_lines if "==" in line), snippet_lines[0] if snippet_lines else "")
            break

    if pattern == "string_equality" and first_snippet:
        left, right = _split_java_equality_operands(first_snippet)
        if left and right:
            title, description, recommendation = _java_string_equality_text(left, right)
            risk["title"] = title
            instance_count = len(refs)
            risk["description"] = (
                f"{description} This finding is grouped across {instance_count} matching "
                f"instance{'s' if instance_count != 1 else ''} in this file."
            )
            risk["recommendation"] = recommendation

    return risk


def _deduplicate_and_prioritize_risks(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = [_normalize_issue(dict(risk)) for risk in risks]
    validated = [risk for risk in normalized if _validate_issue(risk)]

    by_file: Dict[str, List[Dict[str, Any]]] = {}
    for risk in validated:
        refs = risk.get("affected_files") or []
        file_path = refs[0].get("file_path", "") if refs and isinstance(refs[0], dict) else ""
        by_file.setdefault(file_path, []).append(risk)

    compound_risks: List[Dict[str, Any]] = []
    consumed: set[int] = set()
    for file_path, file_risks in by_file.items():
        loop = next((risk for risk in file_risks if risk.get("pattern_key") == "unbounded_loop"), None)
        recursion = next((risk for risk in file_risks if risk.get("pattern_key") == "unguarded_recursion"), None)
        if loop and recursion:
            compound_risks.append({
                "job_id": loop.get("job_id"),
                "risk_id": loop.get("risk_id"),
                "title": "Unbounded execution",
                "description": "Infinite looping and unguarded recursion appear in the same file, creating a compound execution risk that can hang the process or exhaust the stack.",
                "category": "runtime_safety",
                "level": "critical",
                "pattern_key": "unbounded_execution",
                "affected_files": _merge_file_references((loop.get("affected_files") or []) + (recursion.get("affected_files") or [])),
                "recommendation": "Add a deterministic loop exit condition and a recursion base case before allowing repeated execution paths.",
                "confidence": min(float(loop.get("confidence", 0.8)), float(recursion.get("confidence", 0.8)), 0.94),
                "mcp_solution_available": False,
            })
            consumed.add(id(loop))
            consumed.add(id(recursion))

        raw_collection = next((risk for risk in file_risks if risk.get("pattern_key") == "raw_collection_type"), None)
        mixed_collection = next((risk for risk in file_risks if risk.get("pattern_key") == "mixed_type_collection"), None)
        if raw_collection and mixed_collection:
            compound_risks.append({
                "job_id": mixed_collection.get("job_id"),
                "risk_id": mixed_collection.get("risk_id"),
                "title": "Unsafe collection typing",
                "description": "A raw collection is receiving mixed value types, creating a root-cause type-safety risk instead of isolated generic warnings.",
                "category": "type_safety",
                "level": "high",
                "pattern_key": "mixed_type_collection",
                "affected_files": _merge_file_references((raw_collection.get("affected_files") or []) + (mixed_collection.get("affected_files") or [])),
                "recommendation": "Declare the collection with one generic element type and convert or reject incompatible values before insertion.",
                "confidence": min(float(raw_collection.get("confidence", 0.8)), float(mixed_collection.get("confidence", 0.8)), 0.9),
                "mcp_solution_available": False,
            })
            consumed.add(id(raw_collection))
            consumed.add(id(mixed_collection))

    grouped: Dict[tuple, Dict[str, Any]] = {}
    for risk in validated + compound_risks:
        if id(risk) in consumed:
            continue
        refs = risk.get("affected_files") or []
        file_path = refs[0].get("file_path", "") if refs and isinstance(refs[0], dict) else ""
        key = (risk.get("pattern_key"), file_path)
        if key not in grouped:
            grouped[key] = dict(risk)
            grouped[key]["affected_files"] = list(refs)
            continue

        existing = grouped[key]
        existing["affected_files"] = _merge_file_references((existing.get("affected_files") or []) + refs)
        existing["confidence"] = min(float(existing.get("confidence", 0.75)), float(risk.get("confidence", 0.75)))
        if SEVERITY_RANK.get(risk.get("level", "low"), 0) > SEVERITY_RANK.get(existing.get("level", "low"), 0):
            existing["level"] = risk["level"]

    result = []
    for risk in grouped.values():
        refs = _merge_file_references(risk.get("affected_files") or [])
        risk["affected_files"] = refs
        risk["line_numbers"] = [refs[0].get("line_start")] if refs and refs[0].get("line_start") is not None else []
        risk["level"] = STRICT_SEVERITY_BY_PATTERN.get(risk.get("pattern_key"), risk.get("level", "medium"))
        risk = _refresh_risk_text(risk)
        result.append(risk)

    return sorted(
        result,
        key=lambda risk: (
            -SEVERITY_RANK.get(risk.get("level", "low"), 0),
            (risk.get("affected_files") or [{}])[0].get("file_path", ""),
            (risk.get("affected_files") or [{}])[0].get("line_start") or 0,
        ),
    )


def _priority_from_severity(severity: str) -> int:
    return {
        "critical": 10,
        "high": 8,
        "medium": 6,
        "low": 4,
        "info": 2,
    }.get(severity, 5)


def _effort_from_severity(severity: str) -> str:
    return {
        "critical": "high",
        "high": "medium",
        "medium": "medium",
        "low": "low",
        "info": "low",
    }.get(severity, "medium")


def _extract_java_imports(content: str) -> List[str]:
    return re.findall(r"^\s*import\s+(?:static\s+)?([\w.]+)", content, flags=re.MULTILINE)


def _extract_package(content: str) -> Optional[str]:
    match = re.search(r"^\s*package\s+([\w.]+)\s*;", content, flags=re.MULTILINE)
    return match.group(1) if match else None


def _strip_inline_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _java_side_is_string_expression(side: str, string_variables: set[str]) -> bool:
    side = side.strip()
    if not side:
        return False

    if re.search(r'"(?:\\.|[^"\\])*"', side):
        return True

    if re.search(
        r"\.(?:equals|equalsIgnoreCase|getText|toString|trim|substring|concat|toLowerCase|toUpperCase)\s*\(",
        side,
    ):
        return True

    if re.search(r"\bString\.valueOf\s*\(", side):
        return True

    return any(re.search(rf"\b{re.escape(name)}\b", side) for name in string_variables)


def _split_java_equality_operands(line: str) -> tuple[str, str]:
    clean = _strip_inline_comment(line).strip()
    clean = re.sub(r"^(?:if|while)\s*\(", "", clean).strip()
    clean = re.sub(r"\)\s*\{?\s*$", "", clean).strip()
    match = re.search(r"(.+?)==(.+)", clean)
    if not match:
        return "", ""
    left = match.group(1).strip()
    right = match.group(2).strip()
    return left, right


def _java_string_equality_text(left: str, right: str) -> tuple[str, str, str]:
    compared = f"{left} == {right}".strip()
    literal_side = right if re.fullmatch(r'"(?:\\.|[^"\\])*"', right) else left
    expression_side = left if literal_side == right else right
    literal_value = literal_side.strip('"')

    title = "String content compared with =="
    if literal_value == "":
        title = "Empty text compared with =="
        description = f"`{expression_side}` is compared to an empty string with `==`, so the branch depends on object identity instead of the actual text value."
        fix = f"Use `{expression_side}.isEmpty()` or `{expression_side}.equals(\"\")` after any needed null check."
    elif ".getText()" in compared:
        title = "UI text compared with =="
        description = f"UI text from `{expression_side}` is compared using `==`, so equal text can be missed when Java creates a different String object."
        if literal_value == "":
            fix = f"Use `{expression_side}.isEmpty()` after any needed null check, or use `Objects.equals({expression_side}, \"\")`."
        else:
            fix = f"Use `{literal_side}.equals({expression_side})` or `Objects.equals({expression_side}, {literal_side})`."
    elif "getSelectedItem()" in compared:
        title = "Selected item text compared with =="
        description = f"The selected item expression `{expression_side}` is compared with `==`, which checks object identity rather than the selected text value."
        fix = f"Convert the selected item to a String and compare with `.equals`, for example `{literal_side}.equals(String.valueOf({expression_side}))`."
    else:
        description = f"`{compared}` uses `==` on string-like values, so the condition can be false even when both sides contain the same characters."
        fix = f"Replace this comparison with `.equals` or `Objects.equals`, using the literal/constant side first when one side may be null."

    return title, description, fix


def _infer_layer(file_path: str) -> str:
    normalized = file_path.replace("\\", "/").lower()
    if "controller" in normalized:
        return "controller"
    if "service" in normalized:
        return "service"
    if "repository" in normalized or "dao" in normalized:
        return "repository"
    if "model" in normalized or "entity" in normalized or "dto" in normalized:
        return "model"
    if "config" in normalized:
        return "config"
    if "util" in normalized or "helper" in normalized:
        return "utility"
    return "source"


def _detect_java_issues(file_info: FileInfo) -> List[Dict[str, Any]]:
    content = file_info.get("content", "") or ""
    if not content:
        return []

    issues: List[Dict[str, Any]] = []
    lines = content.splitlines()
    file_path = file_info["file_path"]
    string_variables = set(re.findall(r"\bString\s+([A-Za-z_]\w*)\b", content))
    raw_collections: set[str] = set()
    collection_adds: Dict[str, Dict[str, Any]] = {}

    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()

        raw_match = re.search(r"\b(?:List|ArrayList|Map|HashMap|Set|HashSet)\s+([A-Za-z_]\w*)\s*=", line)
        if raw_match and "<" not in line:
            raw_collections.add(raw_match.group(1))
            issues.append({
                "title": "Raw collection type used",
                "description": "Collection declared without generics, which weakens type safety and makes runtime casting errors more likely.",
                "category": "type_safety",
                "level": "medium",
                "pattern_key": "raw_collection_type",
                "recommendation": "Replace raw collections with parameterized types such as List<String> or Map<Key, Value>.",
                "confidence": 0.88,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number, radius=0))],
            })

        add_match = re.search(r"\b([A-Za-z_]\w*)\.add\s*\((.*)\)\s*;", stripped)
        if add_match:
            name, value = add_match.group(1), add_match.group(2).strip()
            value_type = (
                "null" if value == "null" else
                "string" if re.search(r'"(?:\\.|[^"\\])*"', value) else
                "number" if re.fullmatch(r"-?\d+(?:\.\d+)?[fFdDlL]?", value) else
                "boolean" if value in {"true", "false"} else
                "object"
            )
            data = collection_adds.setdefault(name, {"types": set(), "lines": [], "snippets": []})
            data["types"].add(value_type)
            data["lines"].append(line_number)
            data["snippets"].append(stripped)

        comparison_pairs = re.findall(r"([^!=<>]+)==([^!=<>]+)", _strip_inline_comment(line))
        for left_raw, right_raw in comparison_pairs:
            left = left_raw.strip()
            right = right_raw.strip()
            if left == "null" or right == "null":
                continue

            left_string_like = _java_side_is_string_expression(left, string_variables)
            right_string_like = _java_side_is_string_expression(right, string_variables)

            if left_string_like or right_string_like:
                title, description, recommendation = _java_string_equality_text(left, right)
                issues.append({
                    "title": title,
                    "description": description,
                    "category": "logic_bug",
                    "level": "high",
                    "pattern_key": "string_equality",
                    "recommendation": recommendation,
                    "confidence": 0.8,
                    "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
                })
                break

        if re.search(r"for\s*\([^;]*;\s*\w+\s*<=\s*[\w.]+(?:\.size\(\)|\.length)\s*;", line):
            issues.append({
                "title": "Possible off-by-one loop bound",
                "description": "Loop condition uses <= against a collection size or array length, which can produce an IndexOutOfBoundsException on the last iteration.",
                "category": "runtime_safety",
                "level": "high",
                "pattern_key": "off_by_one_loop",
                "recommendation": "Use < when iterating up to size() or length, unless the code intentionally handles the terminal index.",
                "confidence": 0.94,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
            })

        if "while (true)" in stripped or re.search(r"for\s*\(\s*;\s*;\s*\)", stripped):
            issues.append({
                "title": "Unbounded loop detected",
                "description": "Loop appears to have no termination condition, which can exhaust CPU or hang worker threads if no explicit break path is guaranteed.",
                "category": "runtime_safety",
                "level": "high",
                "pattern_key": "unbounded_loop",
                "recommendation": "Add a clear exit condition, timeout, or break strategy so the loop cannot run forever unintentionally.",
                "confidence": 0.97,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
            })

        if "+=" in stripped or re.search(r"\w+\s*=\s*\w+\s*\+\s*\w+", line):
            loop_window = "\n".join(lines[max(0, line_number - 3): min(len(lines), line_number + 2)])
            if "for (" in loop_window or "while (" in loop_window:
                concat_match = re.search(r"([A-Za-z_]\w*)\s*(?:\+=|=\s*\1\s*\+)\s*(.+?);", stripped)
                target = concat_match.group(1) if concat_match else "the accumulated string"
                value = concat_match.group(2) if concat_match else "the appended value"
                issues.append({
                    "title": "String concatenation inside loop",
                    "description": "Repeated string concatenation inside a loop can devolve into quadratic-time behavior and create unnecessary allocations.",
                    "category": "performance",
                    "level": "medium",
                    "pattern_key": "string_concat_loop",
                    "recommendation": f"Create a StringBuilder before the loop and replace this update with builder.append({value.strip()}). Convert it back with {target}.toString() after the loop.",
                    "confidence": 0.78,
                    "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
                })

        null_call = re.search(r"\b([A-Za-z_]\w*)\.toString\s*\(", stripped)
        if null_call and not re.search(rf"\b{re.escape(null_call.group(1))}\s*!=\s*null", "\n".join(lines[max(0, line_number - 3):line_number + 1])):
            issues.append({
                "title": "Null dereference risk",
                "description": "toString() is called without a visible null guard, so a null value can crash this path at runtime.",
                "category": "runtime_safety",
                "level": "high",
                "pattern_key": "null_dereference",
                "recommendation": f"Guard {null_call.group(1)} before the call or use String.valueOf({null_call.group(1)}) when null should render safely.",
                "confidence": 0.72,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
            })

        random_window = "\n".join(lines[line_number - 1: min(len(lines), line_number + 3)])
        if "Math.random()" in random_window and "throw new" in random_window:
            issues.append({
                "title": "Random exception path",
                "description": "Exception behavior depends on Math.random(), making failures nondeterministic and hard to test or reproduce.",
                "category": "runtime_safety",
                "level": "high",
                "pattern_key": "random_exception",
                "recommendation": "Replace random exception triggering with explicit input/state validation and deterministic error conditions.",
                "confidence": 0.95,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
            })

        if re.search(r"\bcache\w*\.put\s*\([^,]+,\s*null\s*\)", stripped, flags=re.IGNORECASE):
            issues.append({
                "title": "Cache null ambiguity",
                "description": "Storing null in a cache makes a cached null indistinguishable from a missing entry when using get().",
                "category": "logic_bug",
                "level": "high",
                "pattern_key": "cache_null_ambiguity",
                "recommendation": "Store Optional values or use containsKey() alongside get() so cache misses and cached nulls are distinct.",
                "confidence": 0.9,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
            })

    for name, data in collection_adds.items():
        concrete_types = {value_type for value_type in data["types"] if value_type != "null"}
        if len(concrete_types) > 1 or ("null" in data["types"] and name in raw_collections):
            first_line = min(data["lines"])
            issues.append({
                "title": "Mixed-type collection",
                "description": f"{name} receives mixed value types, which can cause ClassCastException or unstable downstream type checks.",
                "category": "type_safety",
                "level": "high",
                "pattern_key": "mixed_type_collection",
                "recommendation": f"Parameterize {name} with one element type and reject or convert incompatible values before add().",
                "confidence": 0.86,
                "affected_files": [_make_file_reference(file_path, first_line, max(data["lines"]), "\n".join(data["snippets"]))],
            })

    for method_match in re.finditer(r"(?:public|private|protected)?\s*(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{", content):
        method_name = method_match.group(1)
        body_start = method_match.end()
        depth = 1
        pos = body_start
        while pos < len(content) and depth:
            if content[pos] == "{":
                depth += 1
            elif content[pos] == "}":
                depth -= 1
            pos += 1
        body = content[body_start:pos - 1]
        call_match = re.search(rf"\b{re.escape(method_name)}\s*\(", body)
        if call_match:
            prefix = body[:call_match.start()]
            has_base_return = bool(re.search(r"\bif\s*\([^)]*\)\s*\{?\s*return\b", prefix, flags=re.DOTALL))
        else:
            has_base_return = False
        if call_match and not has_base_return:
            line_number = content[:body_start + call_match.start()].count("\n") + 1
            issues.append({
                "title": "Recursive call without base case",
                "description": "The method calls itself before any visible base-case guard, which can exhaust the stack.",
                "category": "runtime_safety",
                "level": "high",
                "pattern_key": "unguarded_recursion",
                "recommendation": f"Add a base-case return before calling {method_name}() recursively.",
                "confidence": 0.78,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number))],
            })

    for match in re.finditer(r"catch\s*\([^)]+\)\s*\{(?P<body>.*?)\}", content, flags=re.MULTILINE | re.DOTALL):
        catch_body = re.sub(r"//.*?$|/\*.*?\*/", "", match.group("body"), flags=re.MULTILINE | re.DOTALL).strip()
        if catch_body:
            continue
        line_number = content[: match.start()].count("\n") + 1
        snippet = match.group(0).replace("\n", " ").strip()
        issues.append({
            "title": "Empty catch block",
            "description": "Exception is swallowed without logging, handling, or rethrowing, which makes production failures hard to diagnose and can hide bad state.",
            "category": "error_handling",
            "level": "high",
            "pattern_key": "empty_catch",
            "recommendation": "Log the exception with context or rethrow it after cleanup so failures remain observable.",
            "confidence": 0.96,
            "affected_files": [_make_file_reference(file_path, line_number, line_number, _context_snippet(lines, line_number) or snippet)],
        })

    class_count = len(re.findall(r"\bclass\s+\w+", content))
    static_methods = len(re.findall(r"\bstatic\b", content))
    if class_count == 1 and static_methods >= 3:
        file_name = file_path.split("\\")[-1].split("/")[-1]
        issues.append({
            "title": "Procedural utility structure",
            "description": "Single-class design is leaning heavily on static behavior, which suggests a procedural utility shape rather than a modular, testable service design.",
            "category": "architecture",
            "level": "low",
            "pattern_key": "procedural_utility",
            "recommendation": "Split responsibilities into smaller collaborating classes or layers instead of accumulating behavior in a single utility class.",
            "confidence": 0.7,
            "affected_files": [_make_file_reference(file_path, 1, 1, file_name)],
        })

    deduped: List[Dict[str, Any]] = []
    seen = set()
    for issue in issues:
        ref = issue["affected_files"][0]
        key = (issue["title"], ref["file_path"], ref.get("line_start"))
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    
    return deduped

def _detect_cobol_issues(file_info: FileInfo) -> List[Dict[str, Any]]:
    """Detect common issues in COBOL code."""
    content = file_info.get("content", "") or ""
    if not content:
        return []

    issues: List[Dict[str, Any]] = []
    lines = content.splitlines()
    file_path = file_info["file_path"]

    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        upper_line = line.upper()

        # Fixed position data parsing (hardcoded offsets)
        if re.search(r'MOVE\s+\w+-RECORD\s*\(\s*\d+\s*:\s*\d+\s*\)', upper_line):
            issues.append({
                "title": "Fixed Position Data Parsing",
                "description": "The program extracts fields using hardcoded positional offsets, making it fragile to input format changes.",
                "category": "maintainability",
                "level": "high",
                "recommendation": "Use structured record definitions or copybooks instead of positional slicing.",
                "confidence": 0.95,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, stripped)],
            })

        # Missing input validation before numeric moves
        if re.search(r'MOVE\s+\w+-RECORD\s*\([^)]+\)\s+TO\s+\w+-\w+', upper_line):
            # Check if target is numeric (PIC 9)
            target_match = re.search(r'TO\s+([\w-]+)', upper_line)
            if target_match:
                issues.append({
                    "title": "Missing Input Validation",
                    "description": "No validation is performed before moving string data into numeric fields, which can cause runtime errors.",
                    "category": "bug",
                    "level": "high",
                    "recommendation": "Validate numeric fields before conversion using condition checks or NUMERIC test.",
                    "confidence": 0.88,
                    "affected_files": [_make_file_reference(file_path, line_number, line_number, stripped)],
                })

        # Hardcoded business rules (magic numbers in IF statements)
        if re.search(r'IF\s+[\w-]+\s*>\s*\d{3,}', upper_line):
            issues.append({
                "title": "Hardcoded Business Rule",
                "description": "Threshold values are hardcoded in the code, reducing flexibility and maintainability.",
                "category": "architecture",
                "level": "medium",
                "recommendation": "Externalize threshold values into configuration or constants section.",
                "confidence": 0.92,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, stripped)],
            })

        # Missing error handling for file operations
        if 'OPEN INPUT' in upper_line or 'READ' in upper_line:
            # Check if there's error handling nearby
            context_lines = lines[max(0, line_number-1):min(len(lines), line_number+5)]
            context = '\n'.join(context_lines).upper()
            if 'FILE STATUS' not in context and 'INVALID KEY' not in context:
                issues.append({
                    "title": "Lack of Error Handling",
                    "description": "No handling for file open/read failures or malformed records.",
                    "category": "reliability",
                    "level": "high",
                    "recommendation": "Add explicit error handling for file operations using FILE STATUS or error branches.",
                    "confidence": 0.85,
                    "affected_files": [_make_file_reference(file_path, line_number, line_number, stripped)],
                })

        # Tight coupling - business logic in I/O paragraph
        if 'PERFORM' in upper_line and 'READ' in upper_line:
            issues.append({
                "title": "Tight Coupling of I/O and Business Logic",
                "description": "File reading and business logic are intertwined, making testing and reuse difficult.",
                "category": "architecture",
                "level": "medium",
                "recommendation": "Separate file handling from processing logic into distinct procedures.",
                "confidence": 0.78,
                "affected_files": [_make_file_reference(file_path, line_number, line_number, stripped)],
            })

        # No separation of concerns - monolithic paragraph
        if re.search(r'^\s*[\w-]+\s*\.\s*$', line) and 'MAIN' in upper_line:
            # Check if this paragraph does multiple things
            para_start = line_number
            para_lines = []
            for i in range(line_number, min(len(lines), line_number + 30)):
                if i > line_number and re.search(r'^\s*[\w-]+\s*\.\s*$', lines[i]):
                    break
                para_lines.append(lines[i].upper())
            
            para_content = '\n'.join(para_lines)
            operations = sum([
                'OPEN' in para_content,
                'READ' in para_content,
                'DISPLAY' in para_content,
                'CLOSE' in para_content,
                'PERFORM' in para_content
            ])
            
            if operations >= 3:
                issues.append({
                    "title": "Monolithic Procedure",
                    "description": "Main paragraph handles multiple responsibilities (I/O, processing, display), violating separation of concerns.",
                    "category": "architecture",
                    "level": "medium",
                    "recommendation": "Break down into smaller, focused paragraphs with single responsibilities.",
                    "confidence": 0.82,
                    "affected_files": [_make_file_reference(file_path, para_start, para_start, "MAIN-PARA")],
                })

    # Deduplicate issues
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for issue in issues:
        ref = issue["affected_files"][0]
        key = (issue["title"], ref["file_path"], ref.get("line_start"))
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    
    return deduped
    
    return deduped
    return deduped


def _build_dependency_graph_from_parsed(parsed_files: List[ParsedFile]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build dependency graph using parser-derived dependencies.
    
    This function creates edges based on:
    - Java imports
    - COBOL COPY statements
    - RPG /COPY directives
    - JCL EXEC statements
    - Parsed symbol references
    
    Args:
        parsed_files: List of parsed files with dependencies
        
    Returns:
        Dictionary with 'nodes' and 'edges' lists
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen_nodes = set()
    seen_edges = set()
    
    # Build symbol table for resolution
    symbol_table: Dict[str, str] = {}  # symbol -> file_path
    
    for parsed_file in parsed_files:
        file_path = parsed_file["file_path"]
        language = normalize_language(parsed_file.get("language", "unknown"))
        
        # Add node
        node_id = file_path
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            file_name = file_path.split("\\")[-1].split("/")[-1]
            
            # Extract base name for symbol table
            base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            symbol_table[base_name.lower()] = file_path
            
            nodes.append({
                "id": node_id,
                "name": file_name,
                "type": "file",
                "file_path": file_path,
                "language": language,
                "metadata": {
                    "language": language,
                    "classes": len(parsed_file.get("classes", [])),
                    "functions": len(parsed_file.get("functions", [])),
                },
            })
            
            # Add class names to symbol table
            for cls in parsed_file.get("classes", []):
                if isinstance(cls, dict) and "name" in cls:
                    symbol_table[cls["name"].lower()] = file_path
    
    # Build edges from dependencies
    for parsed_file in parsed_files:
        source_path = parsed_file["file_path"]
        language = normalize_language(parsed_file.get("language", "unknown"))
        
        # Process imports (Java, Python, etc.)
        for imp in parsed_file.get("imports", []):
            target_path = _resolve_dependency(imp, symbol_table, parsed_files)
            if target_path and target_path != source_path:
                edge_key = (source_path, target_path)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "source": source_path,
                        "target": target_path,
                        "type": "imports",
                        "weight": 1.0,
                    })
        
        # Process explicit dependencies (COBOL COPY, JCL EXEC, RPG /COPY)
        for dep in parsed_file.get("dependencies", []):
            target_path = _resolve_dependency(dep, symbol_table, parsed_files)
            if target_path and target_path != source_path:
                edge_key = (source_path, target_path)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    
                    # Determine edge type based on language and dependency pattern
                    edge_type = "depends_on"
                    if language == "cobol" and any(kw in dep.upper() for kw in ["COPY", "INCLUDE"]):
                        edge_type = "copybook"
                    elif language == "jcl" and "EXEC" in dep.upper():
                        edge_type = "executes"
                    elif language == "rpg" and "/COPY" in dep.upper():
                        edge_type = "includes"
                    elif "call" in dep.lower():
                        edge_type = "calls"
                    
                    edges.append({
                        "source": source_path,
                        "target": target_path,
                        "type": edge_type,
                        "weight": 1.0,
                    })
    
    return {"nodes": nodes, "edges": edges}


def _resolve_dependency(dependency: str, symbol_table: Dict[str, str], parsed_files: List[ParsedFile]) -> Optional[str]:
    """
    Resolve a dependency string to a file path using symbol table.
    
    Args:
        dependency: Dependency string (import, COPY name, etc.)
        symbol_table: Map of symbols to file paths
        parsed_files: List of all parsed files
        
    Returns:
        Resolved file path or None
    """
    if not dependency:
        return None
    
    # Normalize dependency
    dep_normalized = dependency.strip().lower()
    
    # Try direct symbol lookup
    if dep_normalized in symbol_table:
        return symbol_table[dep_normalized]
    
    # Try extracting last component (class name, copybook name)
    parts = dependency.replace('.', '/').replace('\\', '/').split('/')
    last_part = parts[-1].lower() if parts else ""
    
    if last_part and last_part in symbol_table:
        return symbol_table[last_part]
    
    # Try partial path matching
    if last_part:
        for file_path in [pf["file_path"] for pf in parsed_files]:
            file_path_lower = file_path.lower()
            if dep_normalized in file_path_lower or last_part in file_path_lower:
                return file_path
    
    return None


def ingest_node(state: AgentState) -> AgentState:
    """
    Stage 1: Ingest - Load and validate files.
    
    This node:
    - Validates uploaded files
    - Detects file languages
    - Calculates basic metrics
    - Identifies primary language
    """
    logger.info(f"[Job {state['job_id']}] Starting ingest stage")
    
    start_time = datetime.utcnow()
    
    try:
        uploaded_files = state.get("uploaded_files", [])
        
        # Process each file
        ingested_files: List[FileInfo] = []
        detected_languages = set()
        total_lines = 0
        
        for file_info in uploaded_files:
            # TODO: Implement actual file validation and language detection
            # For now, use provided information
            ingested_files.append(file_info)
            
            if "language" in file_info:
                detected_languages.add(file_info["language"])
            
            if "lines_of_code" in file_info:
                total_lines += file_info["lines_of_code"]
        
        # Determine primary language (most common) - use strings for consistency
        language_counts: Dict[str, int] = {}
        for file_info in ingested_files:
            lang = file_info.get("language")
            if lang:
                lang_str = normalize_language(lang)
                language_counts[lang_str] = language_counts.get(lang_str, 0) + 1
        
        primary_language: Optional[str] = max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else None
        
        # Update state
        state["ingested_files"] = ingested_files
        state["detected_languages"] = list(detected_languages)
        state["primary_language"] = primary_language
        state["total_files"] = len(ingested_files)
        state["total_lines"] = total_lines
        state["current_stage"] = "parse"
        state["progress_percent"] = 12.5
        state["status"] = "processing"
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["ingest"] = elapsed
        
        logger.info(
            f"[Job {state['job_id']}] Ingest complete: "
            f"{len(ingested_files)} files, "
            f"{len(detected_languages)} languages, "
            f"primary={primary_language}"
        )
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Ingest failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Ingest stage failed: {str(e)}"
    
    return state


def parse_node(state: AgentState) -> AgentState:
    """
    Stage 2: Parse - Extract code structure.
    
    This node:
    - Parses source files
    - Extracts classes, functions, imports
    - Builds AST representations
    - Handles parse errors gracefully
    """
    logger.info(f"[Job {state['job_id']}] Starting parse stage")
    
    start_time = datetime.utcnow()
    
    try:
        from app.parsers.parser_factory import get_parser_for_file

        ingested_files = state.get("ingested_files", [])
        
        parsed_files: List[ParsedFile] = []
        parse_errors: List[Dict[str, str]] = []
        
        for file_info in ingested_files:
            try:
                file_language = file_info.get("language", "unknown")
                file_path = file_info["file_path"]
                content = file_info.get("content", "") or ""

                parser = get_parser_for_file(file_path)
                parse_result = parser.parse(file_path, content) if parser else None

                nodes = [node.to_dict() for node in parse_result.nodes] if parse_result else []
                classes = [
                    node
                    for node in nodes
                    if node.get("node_type") in {"class", "interface"}
                ]
                functions = [
                    node
                    for node in nodes
                    if node.get("node_type") in {"method", "function", "procedure", "subroutine", "paragraph"}
                ]

                parsed_file: ParsedFile = {
                    "file_id": file_info["file_id"],
                    "file_path": file_path,
                    "language": normalize_language(parse_result.language if parse_result else file_language),
                    "classes": classes,
                    "functions": functions,
                    "imports": list(parse_result.imports) if parse_result else [],
                    "dependencies": list(parse_result.dependencies) if parse_result else [],
                    "ast_data": dict(parse_result.metadata) if parse_result else None,
                    "nodes": nodes,
                    "parse_success": bool(parse_result.success) if parse_result else False,
                    "parse_errors": list(parse_result.errors) if parse_result else ["No parser available for this file type"],
                }
                parsed_files.append(parsed_file)

                if parse_result and parse_result.errors:
                    parse_errors.append({
                        "file_path": file_path,
                        "error": "; ".join(parse_result.errors),
                    })
                elif not parse_result:
                    parse_errors.append({
                        "file_path": file_path,
                        "error": "No parser available for this file type",
                    })
                
            except Exception as e:
                logger.warning(f"Failed to parse {file_info['file_path']}: {e}")
                parse_errors.append({
                    "file_path": file_info["file_path"],
                    "error": str(e),
                })
        
        # Update state
        state["parsed_files"] = parsed_files
        state["parse_errors"] = parse_errors
        state["successfully_parsed"] = len(parsed_files)
        state["current_stage"] = "classify"
        state["progress_percent"] = 25.0
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["parse"] = elapsed
        
        logger.info(
            f"[Job {state['job_id']}] Parse complete: "
            f"{len(parsed_files)} parsed, "
            f"{len(parse_errors)} errors"
        )
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Parse failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Parse stage failed: {str(e)}"
    
    return state


def classify_node(state: AgentState) -> AgentState:
    """
    Stage 3: Classify - Categorize files and components.
    
    This node:
    - Classifies files by type (source, test, config, etc.)
    - Identifies entry points
    - Categorizes components by layer
    """
    logger.info(f"[Job {state['job_id']}] Starting classify stage")
    
    start_time = datetime.utcnow()
    
    try:
        parsed_files = state.get("parsed_files", [])
        
        file_classifications: Dict[str, str] = {}
        entry_points: List[str] = []
        test_files: List[str] = []
        config_files: List[str] = []
        source_files: List[str] = []
        
        for parsed_file in parsed_files:
            file_path = parsed_file["file_path"]
            file_id = parsed_file["file_id"]
            
            # TODO: Implement actual classification logic
            # For now, use simple heuristics
            if "test" in file_path.lower():
                file_classifications[file_id] = "test"
                test_files.append(file_path)
            elif any(ext in file_path.lower() for ext in [".xml", ".json", ".yaml", ".properties"]):
                file_classifications[file_id] = "config"
                config_files.append(file_path)
            elif "main" in file_path.lower() or "application" in file_path.lower():
                file_classifications[file_id] = "entry_point"
                entry_points.append(file_path)
                source_files.append(file_path)
            else:
                file_classifications[file_id] = "source"
                source_files.append(file_path)
        
        # Update state
        state["file_classifications"] = file_classifications
        state["entry_points"] = entry_points
        state["test_files"] = test_files
        state["config_files"] = config_files
        state["source_files"] = source_files
        state["current_stage"] = "analyze"
        state["progress_percent"] = 37.5
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["classify"] = elapsed
        
        logger.info(
            f"[Job {state['job_id']}] Classify complete: "
            f"{len(source_files)} source, "
            f"{len(test_files)} test, "
            f"{len(config_files)} config, "
            f"{len(entry_points)} entry points"
        )
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Classify failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Classify stage failed: {str(e)}"
    
    return state


async def analyze_node(state: AgentState) -> AgentState:
    """
    Stage 4: Analyze - Detect risks and patterns using rule-based + Groq LLM.
    
    This node:
    - Builds dependency graph (fixed to avoid "undefined")
    - Detects frameworks and patterns
    - Uses Groq LLM for deep, context-aware analysis
    - Deduplicates risks
    - Ensures all risks have specific file paths and line numbers
    """
    logger.info(f"[Job {state['job_id']}] Starting analyze stage with Groq enhancement")
    
    start_time = datetime.utcnow()
    
    try:
        import uuid
        import json
        from app.llm.provider_chain import get_llm_chain
        from app.llm.prompts import PromptTemplates

        ingested_files = state.get("ingested_files", [])
        parsed_files = state.get("parsed_files", [])
        primary_language = str(state.get("primary_language", "unknown") or "unknown")
        total_files = state.get("total_files", 0)

        # Build dependency graph (fixed to avoid "undefined" nodes)
        dependency_graph = _build_dependency_graph_from_parsed(parsed_files)
        layers: Dict[str, List[str]] = {}
        detected_frameworks = set()
        entry_points: List[str] = []
        all_risks: List[Dict[str, Any]] = []
        code_smells: List[Dict[str, Any]] = []

        # Get LLM provider chain
        provider_chain = get_llm_chain()

        for file_info in ingested_files:
            file_path = file_info["file_path"]
            content = file_info.get("content", "") or ""
            layer = _infer_layer(file_path)
            layers.setdefault(layer, []).append(file_path)

            # Detect frameworks
            if "springframework" in content:
                detected_frameworks.add("Spring")
            if "@RestController" in content:
                detected_frameworks.add("Spring MVC")
            if "@Entity" in content:
                detected_frameworks.add("JPA")
            if "public static void main" in content or "SpringApplication.run" in content:
                entry_points.append(file_path)

            # Step 1: Rule-based analysis
            rule_based_issues = []
            file_language = str(file_info.get("language", "")).lower()
            
            if file_language == "java":
                rule_based_issues = _detect_java_issues(file_info)
            elif file_language == "cobol":
                rule_based_issues = _detect_cobol_issues(file_info)
            
            for issue in rule_based_issues:
                all_risks.append({
                    "job_id": state["job_id"],
                    "risk_id": f"risk_{uuid.uuid4().hex[:12]}",
                    "title": issue["title"],
                    "description": issue["description"],
                    "category": issue["category"],
                    "level": issue["level"],
                    "pattern_key": issue.get("pattern_key"),
                    "affected_files": issue["affected_files"],
                    "line_numbers": [
                        ref["line_start"] for ref in issue["affected_files"] if ref.get("line_start") is not None
                    ],
                    "recommendation": issue["recommendation"],
                    "confidence": issue["confidence"],
                    "mcp_solution_available": False,
                })
                code_smells.append(issue)

            # Step 2: Groq LLM deep analysis (only for files with content)
            if content and len(content) > 50:
                try:
                    logger.info(f"[Job {state['job_id']}] Running Groq analysis on {file_path}")
                    
                    # Generate prompt for deep analysis
                    prompt = PromptTemplates.analyze_risks(
                        file_path=file_path,
                        code=content[:4000],  # Limit to avoid token limits
                        language=str(file_info.get("language", "unknown")),
                        detected_risks=rule_based_issues
                    )
                    
                    # Call Groq
                    response = await provider_chain.generate(
                        prompt=prompt,
                        system_prompt="You are an expert code analyzer. Return ONLY valid JSON.",
                        temperature=0.3,  # Lower temperature for more consistent analysis
                        max_tokens=2000
                    )
                    
                    if response.success and response.content:
                        try:
                            # Parse JSON response
                            analysis = json.loads(response.content)
                            
                            # Extract issues from Groq analysis
                            for issue in analysis.get("issues", []):
                                # Only add if it has specific line numbers
                                if issue.get("line_start") and issue.get("file_path"):
                                    all_risks.append({
                                        "job_id": state["job_id"],
                                        "risk_id": f"risk_{uuid.uuid4().hex[:12]}",
                                        "title": issue.get("title", "Unknown issue"),
                                        "description": issue.get("description", ""),
                                        "category": issue.get("category", "general"),
                                        "level": issue.get("severity", "medium"),
                                        "pattern_key": _canonical_pattern(issue.get("title", ""), issue.get("category", "")),
                                        "affected_files": [{
                                            "file_path": issue["file_path"],
                                            "line_start": issue.get("line_start"),
                                            "line_end": issue.get("line_end"),
                                            "snippet": issue.get("code_snippet", "")
                                        }],
                                        "line_numbers": [issue.get("line_start")],
                                        "recommendation": issue.get("recommendation", ""),
                                        "confidence": issue.get("confidence", 0.85),
                                        "mcp_solution_available": False,
                                    })
                            
                            logger.info(f"[Job {state['job_id']}] Groq found {len(analysis.get('issues', []))} additional issues in {file_path}")
                        except json.JSONDecodeError as e:
                            logger.warning(f"[Job {state['job_id']}] Failed to parse Groq JSON response: {e}")
                    else:
                        logger.warning(f"[Job {state['job_id']}] Groq analysis failed for {file_path}: {response.error}")
                        
                except Exception as e:
                    logger.error(f"[Job {state['job_id']}] Groq analysis error for {file_path}: {e}")

        # Step 3: Validate, normalize, group root causes, and prioritize risks.
        logger.info(f"[Job {state['job_id']}] Normalizing {len(all_risks)} risks")
        deduplicated_risks = _deduplicate_and_prioritize_risks(all_risks)
        
        logger.info(f"[Job {state['job_id']}] After deduplication: {len(deduplicated_risks)} unique risks")
        
        # Add architecture-level risks if applicable
        if not dependency_graph["edges"]:
            logger.info("[Job %s] No internal dependencies detected", state["job_id"])

        if total_files > 200:
            deduplicated_risks.append({
                "job_id": state["job_id"],
                "risk_id": f"risk_{uuid.uuid4().hex[:12]}",
                "title": "Large codebase coordination risk",
                "description": f"The repository spans {total_files} files, so even small refactors may have broad blast radius without strong tests and module boundaries.",
                "category": "architecture",
                "level": "medium",
                "affected_files": [],
                "line_numbers": [],
                "recommendation": "Prioritize modularization and test coverage before large modernization moves.",
                "confidence": 0.74,
                "mcp_solution_available": False,
            })

        architecture_patterns = []
        if len(entry_points) <= 1 and len(layers) <= 2:
            architecture_patterns.append("single-class procedural design")
        elif {"controller", "service", "repository"}.issubset(layers.keys()):
            architecture_patterns.append("layered architecture")

        from app.schemas.common import DependencyGraph, DependencyNode, DependencyEdge

        # Convert dict nodes and edges to proper Pydantic models
        nodes = [DependencyNode(**node) for node in dependency_graph["nodes"]]
        edges = [DependencyEdge(**edge) for edge in dependency_graph["edges"]]
        state["dependency_graph"] = DependencyGraph(nodes=nodes, edges=edges)
        state["detected_frameworks"] = sorted(detected_frameworks)
        state["architecture_patterns"] = architecture_patterns
        state["project_type"] = "monolith" if total_files > 1 else "single_file"
        state["layers"] = layers
        state["entry_points"] = entry_points
        state["risks"] = deduplicated_risks
        state["code_smells"] = code_smells
        state["security_issues"] = [risk for risk in deduplicated_risks if risk["category"] in {"security", "logic_bug", "runtime_safety"}]
        state["complexity_metrics"] = {
            "total_files": total_files,
            "files_with_issues": len({ref["file_path"] for risk in deduplicated_risks for ref in risk.get("affected_files", [])}),
            "dependency_count": len(dependency_graph["edges"]),
        }
        state["current_stage"] = "explain"
        state["progress_percent"] = 50.0
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["analyze"] = elapsed
        
        logger.info(f"[Job {state['job_id']}] Analyze complete with {len(deduplicated_risks)} unique risks")
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Analyze failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Analyze stage failed: {str(e)}"
    
    return state


def explain_node(state: AgentState) -> AgentState:
    """
    Stage 5: Explain - Generate human-readable explanations.
    
    This node:
    - Generates summary
    - Explains architecture
    - Explains individual files
    - Describes data flow
    """
    logger.info(f"[Job {state['job_id']}] Starting explain stage")
    
    start_time = datetime.utcnow()
    
    try:
        total_files = state.get("total_files", 0)
        primary_language = str(state.get("primary_language", "unknown") or "unknown")
        risks = state.get("risks", [])
        critical_or_high = [risk for risk in risks if SEVERITY_RANK.get(risk.get("level", "low"), 0) >= 3]
        architecture_patterns = state.get("architecture_patterns", [])
        layers = state.get("layers", {})
        dependency_graph = state.get("dependency_graph")
        dependency_edges = []
        if dependency_graph:
            dependency_edges = dependency_graph.edges if hasattr(dependency_graph, "edges") else []
        dependency_count = len(dependency_edges)

        if critical_or_high:
            dominant_issues = ", ".join(risk.get("title", "").lower() for risk in critical_or_high[:3] if risk.get("title"))
            summary = (
                f"{primary_language.upper()} codebase with {len(critical_or_high)} high-severity reliability risks, "
                f"including {dominant_issues}."
            )
        else:
            summary = (
                f"{primary_language.upper()} codebase with {total_files} files and no high-severity rule matches in the current pass."
            )

        if architecture_patterns:
            summary += f" Structural signal suggests {architecture_patterns[0]}."

        architecture_explanation = (
            f"Detected {len(layers)} logical layer groups and {dependency_count} import relationships. "
            f"Primary language is {primary_language.upper()}."
        )
        if not dependency_count:
            architecture_explanation += " No external dependency relationships were detected, so dependency analysis was intentionally kept lightweight."

        file_explanations = {}
        for risk in risks:
            for ref in risk.get("affected_files", []):
                # Handle both dict and string types for affected_files
                if isinstance(ref, dict):
                    file_path = ref.get("file_path")
                elif isinstance(ref, str):
                    file_path = ref
                else:
                    continue
                    
                if file_path and file_path not in file_explanations:
                    title = risk.get("title", "Unknown issue")
                    description = risk.get("description", "")
                    file_explanations[file_path] = f"{title}: {description}"

        state["summary"] = summary
        state["architecture_explanation"] = architecture_explanation
        state["file_explanations"] = file_explanations
        state["data_flow_explanation"] = "Data flow inferred from imports, entry points, and risk-bearing files."
        state["current_stage"] = "recommend"
        state["progress_percent"] = 62.5
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["explain"] = elapsed
        
        logger.info(f"[Job {state['job_id']}] Explain complete")
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Explain failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Explain stage failed: {str(e)}"
    
    return state


def recommend_node(state: AgentState) -> AgentState:
    """
    Stage 6: Recommend - Generate modernization suggestions.
    
    This node:
    - Generates modernization suggestions
    - Identifies migration blockers
    - Recommends next steps
    - Prioritizes actions
    """
    logger.info(f"[Job {state['job_id']}] Starting recommend stage")
    
    start_time = datetime.utcnow()
    
    try:
        import uuid
        from app.storage.database import get_db
        from app.storage.repositories import get_suggestion_repository

        risks = state.get("risks", [])
        suggestions_to_create: List[Dict[str, Any]] = []
        
        # Group risks by title and category to avoid duplicate suggestions
        risk_groups: Dict[tuple, List[Dict[str, Any]]] = {}
        for risk in risks:
            severity = risk.get("level", "medium")
            if severity == "info":
                continue
            
            title = risk.get("title", "Unknown issue")
            category = risk.get("category", "general")
            key = (title, category)
            
            if key not in risk_groups:
                risk_groups[key] = []
            # Convert RiskItem TypedDict to regular dict for appending
            risk_dict: Dict[str, Any] = dict(risk)  # type: ignore[arg-type]
            risk_groups[key].append(risk_dict)
        
        # Create one suggestion per risk type, aggregating affected files
        for (title, category), risk_list in risk_groups.items():
            # Use the highest severity risk in the group
            highest_severity_risk = max(
                risk_list,
                key=lambda r: SEVERITY_RANK.get(r.get("level", "low"), 0)
            )
            
            severity = highest_severity_risk.get("level", "medium")
            implementation_guide = highest_severity_risk.get("recommendation") or "Apply a targeted fix, add coverage around the behavior, and rerun analysis."
            
            # Aggregate all affected files from all risks in this group
            all_affected_files = []
            for risk in risk_list:
                affected_files = risk.get("affected_files", [])
                all_affected_files.extend(affected_files)
            
            # Get before_snippet from first file
            before_snippet = None
            if all_affected_files:
                first_file = all_affected_files[0]
                if isinstance(first_file, dict):
                    before_snippet = first_file.get("snippet")
            
            # Create description that mentions the count
            count = len(risk_list)
            description = implementation_guide
            if count > 1:
                description = f"Found {count} instances of this issue. {implementation_guide}"
                    
            suggestions_to_create.append({
                "job_id": state["job_id"],
                "suggestion_id": f"sug_{uuid.uuid4().hex[:12]}",
                "type": category,
                "title": f"Fix: {title}",
                "description": description,
                "rationale": (
                    f"Derived from {count} {severity} severity finding{'s' if count > 1 else ''}. "
                    f"This recommendation addresses all instances of this issue."
                ),
                "priority": _priority_from_severity(severity),
                "effort_estimate": _effort_from_severity(severity),
                "affected_files": all_affected_files[:10],  # Limit to first 10 files to avoid bloat
                "before_snippet": before_snippet,
                "after_snippet": None,
                "confidence": highest_severity_risk.get("confidence", 0.75),
                "mcp_based": False,
            })

        if not suggestions_to_create and state.get("detected_frameworks"):
            suggestions_to_create.append({
                "job_id": state["job_id"],
                "suggestion_id": f"sug_{uuid.uuid4().hex[:12]}",
                "type": "architecture",
                "title": "Document framework boundaries and modernization sequence",
                "description": "Map framework-specific entry points and convert them in small, testable slices rather than broad framework rewrites.",
                "rationale": "No discrete code-level fixes were detected, so the best next step is a controlled modernization roadmap.",
                "priority": 6,
                "effort_estimate": "medium",
                "affected_files": [],
                "before_snippet": None,
                "after_snippet": None,
                "confidence": 0.62,
                "mcp_based": False,
            })

        logger.info(f"[Job {state['job_id']}] Preparing to create {len(suggestions_to_create)} suggestions")
        with get_db() as db:
            suggestion_repo = get_suggestion_repository(db)
            created_suggestions = suggestion_repo.create_suggestions(suggestions_to_create)
            logger.info(f"[Job {state['job_id']}] Successfully created {len(created_suggestions)} suggestions in database")

        sorted_risks = sorted(risks, key=lambda risk: SEVERITY_RANK.get(risk.get("level", "low"), 0), reverse=True)
        migration_blockers = [risk.get("title", "Unknown issue") for risk in sorted_risks if risk.get("level") in {"critical", "high"}][:5]
        recommended_next_steps = []
        for risk in sorted_risks[:5]:
            recommendation = risk.get("recommendation")
            if recommendation:
                recommended_next_steps.append(recommendation)
        if not recommended_next_steps:
            recommended_next_steps = [
                "Review the highest-severity issues first and confirm whether they are reproducible in tests.",
                "Apply targeted fixes file by file instead of broad rewrites.",
                "Add regression coverage around any bug or runtime-safety issue before refactoring.",
            ]

        # Store suggestions as List[SuggestionItem] - the database layer handles the conversion
        state["suggestions"] = suggestions_to_create  # type: ignore[assignment]
        state["migration_blockers"] = migration_blockers
        state["recommended_next_steps"] = recommended_next_steps
        state["prioritized_actions"] = []
        state["current_stage"] = "validate"
        state["progress_percent"] = 75.0
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["recommend"] = elapsed
        
        logger.info(f"[Job {state['job_id']}] Recommend complete with {len(suggestions_to_create)} suggestions")
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Recommend failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Recommend stage failed: {str(e)}"
    
    return state


def validate_node(state: AgentState) -> AgentState:
    """
    Stage 7: Validate - Verify recommendations.
    
    This node:
    - Validates recommendations
    - Calculates confidence scores
    - Checks MCP solutions
    - Verifies consistency
    """
    logger.info(f"[Job {state['job_id']}] Starting validate stage")
    
    start_time = datetime.utcnow()
    
    try:
        # TODO: Implement actual validation logic
        # For now, create placeholder validation results
        
        state["validation_results"] = {"status": "validated"}
        state["confidence_scores"] = {}
        state["mcp_solutions_used"] = 0
        state["fallback_used"] = False
        state["current_stage"] = "report"
        state["progress_percent"] = 87.5
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["validate"] = elapsed
        
        logger.info(f"[Job {state['job_id']}] Validate complete")
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Validate failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Validate stage failed: {str(e)}"
    
    return state


def report_node(state: AgentState) -> AgentState:
    """
    Stage 8: Report - Generate final report.
    
    This node:
    - Generates final report
    - Compiles all results
    - Creates report metadata
    - Marks job as complete
    """
    logger.info(f"[Job {state['job_id']}] Starting report stage")
    
    start_time = datetime.utcnow()
    
    try:
        risks = state.get("risks", [])
        suggestions = state.get("suggestions", [])
        summary = state.get("summary", "")

        state["report_generated"] = True
        state["report_content"] = (
            "# Modernization Report\n\n"
            f"## Summary\n{summary}\n\n"
            f"## Risks\nDetected {len(risks)} issue-level findings.\n\n"
            f"## Suggestions\nGenerated {len(suggestions)} targeted remediation steps."
        )
        state["report_metadata"] = {
            "total_files": state.get("total_files", 0),
            "total_lines": state.get("total_lines", 0),
            "primary_language": state.get("primary_language", "unknown"),
            "risk_count": len(risks),
            "suggestion_count": len(suggestions),
        }
        state["current_stage"] = "completed"
        state["progress_percent"] = 100.0
        state["status"] = "completed"
        state["completed_at"] = datetime.utcnow().isoformat()
        
        # Record timing
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        state.setdefault("stage_timings", {})["report"] = elapsed
        
        # Calculate total time
        total_time = sum(state.get("stage_timings", {}).values())
        
        logger.info(
            f"[Job {state['job_id']}] Report complete. "
            f"Total time: {total_time:.2f}s"
        )
        
    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Report failed: {e}", exc_info=True)
        state["status"] = "failed"
        state["error_message"] = f"Report stage failed: {str(e)}"
    
    return state

# Made with Bob
