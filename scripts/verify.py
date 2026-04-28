#!/usr/bin/env python3
"""Structural linter for topic markdown files.

Checks:
1. All 9 required sections are present (heading match).
2. Every ```python code block parses as valid Python 3.
3. Every internal markdown link resolves to an existing file.

Usage:
    python scripts/verify.py                       # verify all topic files
    python scripts/verify.py path/to/topic.md ...  # verify specific files
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPICS = ROOT / "topics"

REQUIRED_SECTIONS = [
    "TL;DR",
    "Intuition",
    "Walkthrough",
    "Implementation",
    "Variants & pitfalls",
    "Complexity",
    "Problem set",
    "Related patterns",
    "Interviewer follow-ups",
]

PYTHON_BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def check_sections(text: str) -> list[str]:
    errors = []
    for section in REQUIRED_SECTIONS:
        pattern = rf"^#{{1,4}}\s+(?:\d+\.\s+)?{re.escape(section)}\s*$"
        if not re.search(pattern, text, re.MULTILINE):
            errors.append(f"missing section '{section}'")
    return errors


def check_python_blocks(text: str) -> list[str]:
    errors = []
    for i, match in enumerate(PYTHON_BLOCK_RE.finditer(text), start=1):
        code = match.group(1)
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"invalid python in block #{i}: {e.msg} (line {e.lineno})")
    return errors


def check_links(path: Path, text: str) -> list[str]:
    errors = []
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        file_part = target.split("#", 1)[0]
        if not file_part:
            continue
        candidate = (path.parent / file_part).resolve()
        if not candidate.exists():
            errors.append(f"broken internal link '{target}'")
    return errors


def verify_file(path: Path) -> list[str]:
    text = path.read_text()
    errors = []
    errors.extend(check_sections(text))
    errors.extend(check_python_blocks(text))
    errors.extend(check_links(path, text))
    return [f"{path}: {e}" for e in errors]


def collect_default_files() -> list[Path]:
    files = []
    for p in TOPICS.rglob("*.md"):
        if p.name.startswith("_"):
            continue
        files.append(p)
    return sorted(files)


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(a) for a in argv]
    else:
        files = collect_default_files()
    all_errors = []
    for f in files:
        if not f.exists():
            all_errors.append(f"{f}: file not found")
            continue
        all_errors.extend(verify_file(f))
    if all_errors:
        for e in all_errors:
            print(e)
        return 1
    print(f"OK ({len(files)} file(s) verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
