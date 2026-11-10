"""Java compiler diagnostics for source sets collected by the analysis agent."""

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

logger = logging.getLogger(__name__)

_DIAGNOSTIC_RE = re.compile(
    r"^(?P<source>.+\.java):(?P<line>\d+):\d+:\s*(?P<diagnostic>compiler\.[^\r\n]+)$"
)
_SYNTAX_CODES = (
    "compiler.err.expected",
    "compiler.err.illegal.start",
    "compiler.err.premature.eof",
    "compiler.err.unclosed",
    "compiler.err.not.stmt",
    "compiler.err.reached.end.of.file",
    "compiler.err.else.without.if",
    "compiler.err.catch.without.try",
    "compiler.err.finally.without.try",
    "compiler.err.try.without.catch.finally.or.resource.decls",
)
_TYPE_CODES = (
    "compiler.err.prob.found.req",
    "compiler.err.cant.apply.symbol",
    "compiler.err.operator.cant.be.applied",
    "compiler.err.inconvertible.types",
    "compiler.err.unexpected.type",
)


def detect_java_compiler_issues(
    files: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Compile available Java sources together and return actionable diagnostics.

    Missing external classes and packages are omitted because dependency classpaths
    are not available to the analyzer. Variable-resolution, syntax, type, and
    unreachable-code errors are still reported when javac can establish them.
    """
    javac = shutil.which("javac")
    if not javac:
        logger.debug("Skipping Java compiler diagnostics because javac is unavailable")
        return []

    java_files = [
        item for item in files
        if str(item.get("language", "")).lower() == "java"
        or str(item.get("file_path", "")).lower().endswith(".java")
    ]
    java_files = [item for item in java_files if isinstance(item.get("content"), str) and item["content"].strip()]
    if not java_files:
        return []

    source_bytes = sum(len(item["content"].encode("utf-8")) for item in java_files)
    if len(java_files) > 200 or source_bytes > 5_000_000:
        logger.warning(
            "Skipping javac analysis for oversized source set (%s files, %s bytes)",
            len(java_files),
            source_bytes,
        )
        return []

    with tempfile.TemporaryDirectory(prefix="bob-java-check-") as temporary_directory:
        root = Path(temporary_directory)
        classes_dir = root / "classes"
        classes_dir.mkdir()
        source_map: dict[str, Mapping[str, Any]] = {}
        basename_map: dict[str, Mapping[str, Any]] = {}
        ambiguous_basenames: set[str] = set()
        source_paths: list[str] = []

        for index, item in enumerate(java_files):
            original_path = str(item.get("file_path") or f"Source{index}.java")
            filename = original_path.replace("\\", "/").rsplit("/", 1)[-1]
            if not filename.endswith(".java"):
                filename = f"Source{index}.java"
            source_path = root / f"source_{index}" / filename
            source_path.parent.mkdir()
            source_path.write_text(item["content"], encoding="utf-8")
            resolved_path = str(source_path.resolve())
            source_map[resolved_path.casefold()] = item
            relative_path = str(source_path.relative_to(root)).replace("\\", "/")
            source_map[relative_path.casefold()] = item
            basename = filename.casefold()
            if basename in basename_map:
                basename_map.pop(basename, None)
                ambiguous_basenames.add(basename)
            elif basename not in ambiguous_basenames:
                basename_map[basename] = item
            source_paths.append(resolved_path)

        try:
            completed = subprocess.run(
                [
                    javac,
                    "-proc:none",
                    "-XDrawDiagnostics",
                    "-classpath",
                    str(classes_dir),
                    "-d",
                    str(classes_dir),
                    *source_paths,
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            logger.warning("Java compiler analysis could not complete: %s", error)
            return []

        diagnostics = f"{completed.stdout}\n{completed.stderr}"
        issues: list[dict[str, Any]] = []
        for line in diagnostics.splitlines():
            match = _DIAGNOSTIC_RE.match(line.strip())
            if not match:
                continue

            diagnostic_path = match.group("source")
            item = source_map.get(diagnostic_path.replace("\\", "/").casefold())
            if item is None:
                item = source_map.get(str(Path(diagnostic_path).resolve()).casefold())
            if item is None:
                basename = Path(diagnostic_path).name.casefold()
                if basename not in ambiguous_basenames:
                    item = basename_map.get(basename)
            if item is None:
                continue

            diagnostic = match.group("diagnostic")
            line_number = int(match.group("line"))
            if "compiler.err.unreachable.stmt" in diagnostic:
                category = "control_flow"
                title = "Unreachable Java statement"
                description = "javac reports that this statement cannot be reached."
                pattern_key = "java_unreachable_statement"
            elif "compiler.err.var.might.not.have.been.initialized" in diagnostic:
                category = "data_flow"
                title = "Variable may be used before initialization"
                description = "javac reports that this local variable may be read before it is definitely assigned."
                pattern_key = "java_uninitialized_variable"
            elif any(code in diagnostic for code in _SYNTAX_CODES):
                category = "syntax"
                title = "Java syntax error"
                description = f"javac rejected this source syntax: {diagnostic}."
                pattern_key = "java_syntax_error"
            elif "compiler.err.cant.resolve.location" in diagnostic:
                symbol_match = re.search(r"kindname.variable,\s*([^,]+)", diagnostic)
                if not symbol_match:
                    continue
                symbol = symbol_match.group(1).strip()
                category = "undefined_symbol"
                title = f"Undefined variable: {symbol}"
                description = f"javac cannot resolve variable `{symbol}` at this location."
                pattern_key = "java_undefined_variable"
            elif any(code in diagnostic for code in _TYPE_CODES):
                category = "type_mismatch"
                title = "Java type or method-signature mismatch"
                description = f"javac rejected this assignment or method call: {diagnostic}."
                pattern_key = "java_type_mismatch"
            else:
                continue

            source_lines = item["content"].splitlines()
            snippet = source_lines[line_number - 1] if 0 < line_number <= len(source_lines) else ""
            file_path = str(item.get("file_path") or "unknown")
            issues.append({
                "title": title,
                "description": description,
                "category": category,
                "level": "high",
                "pattern_key": pattern_key,
                "recommendation": "Correct the reported Java compilation error before runtime analysis.",
                "confidence": 0.99,
                "affected_files": [{
                    "file_path": file_path,
                    "line_start": line_number,
                    "line_end": line_number,
                    "snippet": snippet,
                }],
            })
            if len(issues) >= 100:
                break

        return issues