"""Check a biochemistry lab-report TeX file for common format issues."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


MAIN_SECTIONS = ["Introduction", "Methods", "Results", "Discussion", "References"]
METHOD_SUBSECTIONS = ["Materials and Reagents", "Equipment", "Workflow", "Experimental Procedure"]
FORBIDDEN_HEADINGS = [
    "Experiment Principle",
    "Materials and Methods",
    "Results and Analysis",
    "Discussion and Conclusion",
    "Conclusion",
]
EXTRA_COVER_FIELDS = ["Course", "Technique"]


@dataclass
class Issue:
    level: str
    message: str


def strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        escaped = False
        kept = []
        for char in line:
            if char == "%" and not escaped:
                break
            kept.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        lines.append("".join(kept))
    return "\n".join(lines)


def find_headings(text: str, command: str) -> list[str]:
    pattern = re.compile(rf"\\{command}\*?\{{([^{{}}]+)\}}")
    return [match.group(1).strip() for match in pattern.finditer(text)]


def has_heading(headings: list[str], expected: str) -> bool:
    return any(heading == expected for heading in headings)


def heading_index(headings: list[str], expected: str) -> int | None:
    for index, heading in enumerate(headings):
        if heading == expected:
            return index
    return None


def check_report(path: Path) -> list[Issue]:
    raw = path.read_text(encoding="utf-8")
    text = strip_comments(raw)
    sections = find_headings(text, "section")
    subsections = find_headings(text, "subsection")
    issues: list[Issue] = []

    for section in MAIN_SECTIONS:
        if not has_heading(sections, section):
            issues.append(Issue("ERROR", f"Missing main section: {section}"))

    indexes = [heading_index(sections, section) for section in MAIN_SECTIONS]
    if all(index is not None for index in indexes) and indexes != sorted(indexes):
        issues.append(Issue("ERROR", "Main sections are not in the expected order."))

    for heading in FORBIDDEN_HEADINGS:
        if has_heading(sections, heading) or has_heading(subsections, heading):
            issues.append(Issue("ERROR", f"Forbidden standalone heading found: {heading}"))

    if has_heading(sections, "Methods"):
        for subsection in METHOD_SUBSECTIONS:
            if not has_heading(subsections, subsection):
                issues.append(Issue("WARN", f"Methods subsection not found: {subsection}"))

    for field in EXTRA_COVER_FIELDS:
        if re.search(rf"\\textbf\{{{re.escape(field)}:\}}", text):
            issues.append(Issue("WARN", f"Cover contains extra default field: {field}"))

    if re.search(r"\\captionsetup(?:\[[^\]]+\])?\{[^}]*labelsep\s*=\s*colon", text):
        issues.append(Issue("ERROR", "Caption setup uses colon separators. Use labelsep=period."))

    if re.search(r"\\caption\{[^{}]*(?:Figure|Fig\.|Table)\s*\d+\s*:", text, flags=re.IGNORECASE):
        issues.append(Issue("ERROR", "Caption text appears to manually include a Figure/Table label with a colon."))

    for kind in ["Figure", "Table"]:
        if re.search(rf"{kind}~?\\ref\{{[^}}]+\}}:", text):
            issues.append(Issue("WARN", f"Possible colon after {kind} reference in prose."))

    if "\\caption" in text and "labelsep=period" not in text:
        issues.append(Issue("WARN", "No explicit labelsep=period found for captions."))

    if "\\begin{table}" in text and "\\toprule" not in text:
        issues.append(Issue("WARN", "Tables found but no booktabs top rule detected. Use three-line tables."))

    if "\\begin{table}" in text and "\\begin{tablenotes}" not in text:
        issues.append(Issue("WARN", "Tables found but no tablenotes environment detected for data-processing notes."))

    if re.search(r"\\begin\{abstract\}|\\keywords\{", text, flags=re.IGNORECASE):
        issues.append(Issue("WARN", "Abstract or keywords found; ordinary homework reports should omit them."))

    citation_scan_text = "\n".join(
        line for line in text.splitlines() if not re.search(r"\\(?:re)?newcommand", line)
    )
    if re.search(r"(?<!\\textsuperscript\{)(?<!\\upcite\{)~?\[\d+(?:,\d+)*\]", citation_scan_text):
        issues.append(Issue("WARN", "Plain bracket citation found. Use superscript bracket citations such as \\upcite{1}."))

    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tex", type=Path)
    args = parser.parse_args()

    issues = check_report(args.tex)
    if not issues:
        print(f"OK: {args.tex}")
        return

    for issue in issues:
        print(f"{issue.level}: {issue.message}")

    if any(issue.level == "ERROR" for issue in issues):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
