# LeetCode Interview Prep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 39-file Python algorithm reference for LeetCode-style interview preparation under `/Users/panibrat/dev/interview-prep`, satisfying the spec at `docs/superpowers/specs/2026-04-27-leetcode-prep-design.md`.

**Architecture:** Plain-markdown reference organized by category under `topics/`, with a consolidated `RECALL.md` (30-second cards) and a `templates/` folder of code-only Python snippets. A small `scripts/verify.py` enforces structural quality (9 required sections per topic, valid Python in code blocks, working internal links). Each topic file is independent and built from a shared `_TEMPLATE.md`.

**Tech Stack:** Markdown, Python 3 (verify script + code examples), Git.

---

## File Structure

**Created during scaffolding (Tasks 1–3):**
- `.gitignore`
- `scripts/verify.py` — structural linter for topic files
- `topics/_TEMPLATE.md` — per-topic file skeleton (9 sections)
- `topics/<category>/` — empty category directories
- `templates/` — empty, with `templates/README.md` skeleton
- `README.md` — index skeleton
- `RECALL.md` — consolidated cards skeleton
- `docs/` already exists from spec/plan

**Created during Phases 3–5 (Tasks 4–42):** 39 topic files across 10 categories, plus 16 Python files under `templates/`.

**Modified continuously:**
- `README.md` — every per-topic task appends an entry to the study order
- `RECALL.md` — every per-topic task appends a card section
- `templates/<file>.py` — created only for the 16 topics listed in spec section 3

---

## Conventions

- **Commit cadence:** one commit per task. No squashing across tasks.
- **No skips, no TODOs.** A task is not complete until verify passes and the file would be useful to the user solving problems on LeetCode.
- **All Python code blocks must be runnable.** Verify script parses every `python` block via `ast.parse`.
- **All LeetCode links use the form** `https://leetcode.com/problems/<slug>/` — no query params, no leading `www.`.

---

## Standard Per-Topic Checklist

This is the canonical 8-step checklist applied to **every task in Phases 3–5** (Tasks 5–42). Each per-topic task is complete when all eight checkboxes are ticked. Per-task variables are listed at the end of every task as **Apply checklist with:**.

- [ ] **Step 1: Copy template and rename**
  ```bash
  cp topics/_TEMPLATE.md <TOPIC_FILE>
  ```
  Edit line 1 of the new file: change `# <Topic name>` to `# <TOPIC_TITLE>`.

- [ ] **Step 2: Fill all 9 sections** per the **Topic content brief** in the task. Code blocks in Section 4 (Implementation) must parse as valid Python 3. Walkthrough must use real values (no `i`/`j`/`k` only). LeetCode links use `https://leetcode.com/problems/<slug>/`.

- [ ] **Step 3: Verify the new file**
  ```bash
  python scripts/verify.py <TOPIC_FILE>
  ```
  Expected: `OK (1 file(s) verified)`. Fix any reported issue and re-run.

- [ ] **Step 4: Append card section to `RECALL.md`** with format:
  ````markdown

  ## [<TOPIC_TITLE>](<TOPIC_FILE>) <TIER_STARS>

  <TL;DR copied verbatim from Section 1>

  ```python
  <Template code copied verbatim from Section 4>
  ```
  ````
  Where `<TIER_STARS>` is `★★★`, `★★`, or `★` per the tier in spec §7.

- [ ] **Step 5: Append entry to `README.md` study order**, format:
  ```markdown
  1. <TIER_STARS> [<TOPIC_TITLE>](<TOPIC_FILE>)
  ```
  Use `1.` for every entry — markdown auto-numbers sequential `1.` items, and Task 44 produces the canonical fixed-number ordering. Do NOT use `-` bullets here; the spec's study order is a numbered list.

- [ ] **Step 6 (only if `<TEMPLATE_FILE>` is set in the task): Create the templates file**

  Create `templates/<TEMPLATE_FILE>` with bare-bones Python bodies only — no exposition, no smoke-tests. The first line is a docstring linking back to `<TOPIC_FILE>`. Then add an index entry to `templates/README.md`:
  ```markdown
  - [`<TEMPLATE_FILE>`](<TEMPLATE_FILE>) — <one-line description>
  ```

- [ ] **Step 7: Run full verify**
  ```bash
  python scripts/verify.py
  ```
  Expected: `OK (N file(s) verified)` where N is the running file count.

- [ ] **Step 8: Commit**
  ```bash
  git add .
  git commit -m "docs: add <TOPIC_SLUG> reference"
  ```

(Task 4 — the worked example — uses the long-form version of these same steps. Tasks 5–42 use the compact form by referencing this checklist.)

---

## Phase 1: Repo Setup

### Task 1: Initialize repository and directory structure

**Files:**
- Create: `/Users/panibrat/dev/interview-prep/.gitignore`
- Create: directory tree under `/Users/panibrat/dev/interview-prep/`

- [ ] **Step 1: Initialize git**

```bash
cd /Users/panibrat/dev/interview-prep
git init
git branch -m main
```

Expected: `Initialized empty Git repository...` and current branch is `main`.

- [ ] **Step 2: Create `.gitignore`**

Create `/Users/panibrat/dev/interview-prep/.gitignore`:

```
__pycache__/
*.pyc
.DS_Store
.venv/
.idea/
.vscode/
```

- [ ] **Step 3: Create directory tree**

```bash
mkdir -p topics/searching-sorting \
         topics/two-pointers-sliding-window \
         topics/graphs \
         topics/dp \
         topics/strings \
         topics/trees \
         topics/greedy \
         topics/backtracking \
         topics/math \
         topics/nice-to-have \
         templates \
         scripts
```

- [ ] **Step 4: Verify structure**

```bash
find . -type d -not -path './.git*' -not -path './docs*' | sort
```

Expected output:
```
.
./scripts
./templates
./topics
./topics/backtracking
./topics/dp
./topics/graphs
./topics/greedy
./topics/math
./topics/nice-to-have
./topics/searching-sorting
./topics/strings
./topics/trees
./topics/two-pointers-sliding-window
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "chore: initialize repo and directory structure"
```

Note: empty directories aren't tracked by git; they'll be populated by later tasks. The commit captures `.gitignore` only.

---

### Task 2: Create `scripts/verify.py` (structural linter)

**Files:**
- Create: `scripts/verify.py`
- Create: `scripts/test_verify.py`

**Purpose:** A small CLI that lints topic markdown files for structural correctness. Used as the "test" in TDD-style task workflow throughout the rest of the plan.

- [ ] **Step 1: Write failing test for section-presence check**

Create `scripts/test_verify.py`:

```python
import subprocess
import sys
import textwrap
from pathlib import Path


def _run(tmp_path, markdown):
    f = tmp_path / "sample.md"
    f.write_text(markdown)
    result = subprocess.run(
        [sys.executable, "scripts/verify.py", str(f)],
        capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1],
    )
    return result


def test_passes_when_all_sections_present(tmp_path):
    md = textwrap.dedent("""\
        # Title
        ## 1. TL;DR
        x
        ## 2. Intuition
        x
        ## 3. Walkthrough
        x
        ## 4. Implementation
        ```python
        def f():
            return 1
        ```
        ## 5. Variants & pitfalls
        x
        ## 6. Complexity
        x
        ## 7. Problem set
        - [Easy] [Two Sum](https://leetcode.com/problems/two-sum/)
        ## 8. Related patterns
        x
        ## 9. Interviewer follow-ups
        x
        """)
    result = _run(tmp_path, md)
    assert result.returncode == 0, result.stdout + result.stderr


def test_fails_when_section_missing(tmp_path):
    md = "# Title\n## 1. TL;DR\nx\n"  # missing 8 sections
    result = _run(tmp_path, md)
    assert result.returncode != 0
    assert "Intuition" in result.stdout


def test_fails_on_invalid_python(tmp_path):
    md = textwrap.dedent("""\
        # Title
        ## 1. TL;DR
        x
        ## 2. Intuition
        x
        ## 3. Walkthrough
        x
        ## 4. Implementation
        ```python
        def broken(:
        ```
        ## 5. Variants & pitfalls
        x
        ## 6. Complexity
        x
        ## 7. Problem set
        x
        ## 8. Related patterns
        x
        ## 9. Interviewer follow-ups
        x
        """)
    result = _run(tmp_path, md)
    assert result.returncode != 0
    assert "invalid python" in result.stdout.lower()


def test_fails_on_broken_internal_link(tmp_path):
    md = textwrap.dedent("""\
        # Title
        ## 1. TL;DR
        x
        ## 2. Intuition
        x
        ## 3. Walkthrough
        x
        ## 4. Implementation
        x
        ## 5. Variants & pitfalls
        x
        ## 6. Complexity
        x
        ## 7. Problem set
        x
        ## 8. Related patterns
        See [neighbor](does-not-exist.md).
        ## 9. Interviewer follow-ups
        x
        """)
    result = _run(tmp_path, md)
    assert result.returncode != 0
    assert "broken internal link" in result.stdout.lower()
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
python -m pytest scripts/test_verify.py -v
```

Expected: all four tests fail with `FileNotFoundError` or `ModuleNotFoundError` (verify.py doesn't exist yet).

- [ ] **Step 3: Write `scripts/verify.py`**

Create `/Users/panibrat/dev/interview-prep/scripts/verify.py`:

```python
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
# matches markdown links: [text](target) — captures target
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def check_sections(text: str) -> list[str]:
    errors = []
    for section in REQUIRED_SECTIONS:
        # match `## 1. TL;DR`, `### TL;DR`, etc.
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
        # external links and anchors-only links are skipped
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # strip in-page anchor
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
```

- [ ] **Step 4: Run tests, confirm pass**

```bash
python -m pytest scripts/test_verify.py -v
```

Expected: all four tests pass.

- [ ] **Step 5: Smoke-run verify on empty topic set**

```bash
python scripts/verify.py
```

Expected: `OK (0 file(s) verified)`

- [ ] **Step 6: Commit**

```bash
git add scripts/verify.py scripts/test_verify.py
git commit -m "feat(scripts): add verify.py structural linter for topic files"
```

---

### Task 3: Create `_TEMPLATE.md`, `README.md`, `RECALL.md`, `templates/README.md` skeletons

**Files:**
- Create: `topics/_TEMPLATE.md`
- Create: `README.md`
- Create: `RECALL.md`
- Create: `templates/README.md`

- [ ] **Step 1: Create `topics/_TEMPLATE.md`**

Create `/Users/panibrat/dev/interview-prep/topics/_TEMPLATE.md`:

````markdown
# <Topic name>

## 1. TL;DR

<2–3 sentences. State what the algorithm/pattern is, the **signal** that tells you to reach for it in a problem statement, and headline time/space complexity.>

## 2. Intuition

<Mental model in plain English. Why does this approach work? What's the key insight that makes it correct? Use an analogy where it helps.>

## 3. Walkthrough

<A small, concrete example with real values, traced step-by-step. ASCII diagrams for state changes where useful.>

## 4. Implementation

<Clean, runnable Python with comments on non-obvious lines.>

```python
# implementation
```

**Template:**

```python
# bare-bones, problem-agnostic boilerplate
```

## 5. Variants & pitfalls

<Common mutations of the algorithm, off-by-one traps, edge cases. Anti-patterns folded in.>

## 6. Complexity

- **Time:** O(...) — <one-sentence justification>
- **Space:** O(...) — <one-sentence justification>

## 7. Problem set

- [Easy] [<Problem name>](https://leetcode.com/problems/<slug>/) — <one-line "what makes this instructive">
- [Medium] [<Problem name>](https://leetcode.com/problems/<slug>/) — <one-line>
- [Hard] [<Problem name>](https://leetcode.com/problems/<slug>/) — <one-line>

## 8. Related patterns

- [<Sibling topic>](../<category>/<sibling>.md) — <relationship>

## 9. Interviewer follow-ups

**Q: <Typical follow-up question>**
<Short answer or code sketch.>

**Q: <Another follow-up>**
<Short answer.>
````

- [ ] **Step 2: Create `README.md` skeleton**

Create `/Users/panibrat/dev/interview-prep/README.md`:

```markdown
# LeetCode Interview Prep — Python Reference

A long-term, high-quality reference for LeetCode-style algorithm interviews. Each topic file contains a TL;DR, intuition, walkthrough, implementation, variants, complexity, curated problem set, related patterns, and interviewer follow-ups. Solutions are practiced on LeetCode itself; this repo is the study guide.

## How to use

1. Pick a topic from the **Study order** below.
2. Read its file end to end. Solve the problem set on leetcode.com.
3. When refreshing before an interview, re-read [`RECALL.md`](RECALL.md) (TL;DRs and templates only) and copy from [`templates/`](templates/README.md).

## Tier legend

- **★★★ Must-know cold** — show up constantly. Fluent recall required.
- **★★ Strongly recommended** — show up regularly. Recognize and execute.
- **★ Nice to have** — appear occasionally, mostly at top-tier or specialized roles.

## Study order

<!-- entries appended by per-topic tasks; final ordering finalized in Task 44 -->

## See also

- [`RECALL.md`](RECALL.md) — consolidated 30-second cards (TL;DR + Template per topic)
- [`templates/README.md`](templates/README.md) — bare-bones Python snippet library
```

- [ ] **Step 3: Create `RECALL.md` skeleton**

Create `/Users/panibrat/dev/interview-prep/RECALL.md`:

```markdown
# Recall Cards

The "30 minutes before the interview" file. Each section is a single topic's TL;DR plus its Template code block, copied verbatim from the full topic file. Sections appear in study order.

For full explanations, walkthroughs, and problem sets, follow the link on each topic heading.

<!-- card sections appended by per-topic tasks -->
```

- [ ] **Step 4: Create `templates/README.md` skeleton**

Create `/Users/panibrat/dev/interview-prep/templates/README.md`:

```markdown
# Templates

Bare-bones, copy-pasteable Python snippets. No exposition. Use these in the final hour before an interview when you want code, not prose.

For full context on any template, see the corresponding topic file under [`../topics/`](../topics/).

## Index

<!-- entries appended by per-topic tasks (only for templated topics, see spec §3) -->
```

- [ ] **Step 5: Verify everything still passes**

```bash
python scripts/verify.py
python -m pytest scripts/test_verify.py -v
```

Expected: both pass. `verify.py` reports `OK (0 file(s) verified)` (the `_TEMPLATE.md` file is skipped because its name starts with `_`).

- [ ] **Step 6: Commit**

```bash
git add topics/_TEMPLATE.md README.md RECALL.md templates/README.md
git commit -m "docs: add topic template and skeleton index files"
```

---

## Phase 2: Worked Example

### Task 4: `topics/searching-sorting/binary-search.md` (worked example, full step detail)

This task is the canonical example. Tasks 5–42 follow the same workflow but in abbreviated form.

**Files:**
- Create: `topics/searching-sorting/binary-search.md`
- Create: `templates/binary-search.py`
- Modify: `RECALL.md` (append card section)
- Modify: `README.md` (append study-order entry)
- Modify: `templates/README.md` (append index entry)

**Topic content brief:**

- **Signal:** sorted array (or any monotonic predicate over an integer/real range); target lookup or "smallest/largest value satisfying X"; problem says "in O(log n)".
- **Key insight:** if a predicate is monotonic over the search space, you can repeatedly halve the candidate range while preserving an invariant about which side the answer lives on.
- **Walkthrough:** trace `nums = [1, 3, 5, 7, 9, 11], target = 7` step by step, showing `lo`/`hi`/`mid` at each iteration. Then trace a leftmost-insert variant on `nums = [1, 2, 2, 2, 3], target = 2`.
- **Variants to cover:**
  - Classic search (`lo <= hi`, return index or -1)
  - Leftmost insert (`bisect_left` semantics)
  - Rightmost insert (`bisect_right` semantics)
  - Search on rotated sorted array
  - **Search on answer space** — when the answer is itself a numeric value (e.g., minimum capacity, maximum distance) and there's a monotonic feasibility check `f(x)`. Emphasize this — spec §1 calls it out as one of the highest-leverage patterns.
- **Pitfalls:**
  - `mid = (lo + hi) // 2` overflow (non-issue in Python, mention for C++/Java context)
  - Off-by-one when the loop condition is `lo < hi` vs `lo <= hi`
  - Forgetting to update `lo = mid + 1` (infinite loop)
  - Picking the wrong half-open invariant for `bisect_*` variants
- **Complexity:** O(log n) time, O(1) space.
- **LeetCode problems (curate ~8 across difficulties):**
  - [Easy] Binary Search (704), Search Insert Position (35)
  - [Medium] Find First and Last Position of Element in Sorted Array (34), Search in Rotated Sorted Array (33), Find Peak Element (162), Find Minimum in Rotated Sorted Array (153), Koko Eating Bananas (875, search-on-answer), Capacity to Ship Packages Within D Days (1011, search-on-answer)
  - [Hard] Median of Two Sorted Arrays (4), Split Array Largest Sum (410, search-on-answer)
- **Related patterns to link:**
  - `../two-pointers-sliding-window/two-pointers.md` (related linear search alternative)
  - `quicksort-mergesort.md` (mergesort relies on the same divide-and-conquer recurrence)
  - `../trees/bst.md` (binary search on a tree shape)
- **Interviewer follow-ups:**
  - "What changes if the array has duplicates?" — leftmost vs rightmost variants.
  - "What if the array is rotated?" — find pivot via binary search, then search the appropriate half.
  - "What if it doesn't fit in memory?" — external binary search over a sorted file via `seek`/page reads; or model as binary search on a query API.

- [ ] **Step 1: Copy template**

```bash
cp topics/_TEMPLATE.md topics/searching-sorting/binary-search.md
```

- [ ] **Step 2: Replace `<Topic name>` with `Binary Search`**

Edit `topics/searching-sorting/binary-search.md` line 1: change `# <Topic name>` to `# Binary Search`.

- [ ] **Step 3: Fill all 9 sections per the brief above**

Use the brief to write each of the 9 sections. Code in Section 4 (Implementation) should include four runnable functions: `binary_search(nums, target)`, `bisect_left(nums, target)`, `bisect_right(nums, target)`, and a `search_on_answer(lo, hi, feasible)` template at the bottom of the section. Each function gets a short docstring and a one-line smoke test under `if __name__ == "__main__":` is acceptable.

- [ ] **Step 4: Run verify on the new file**

```bash
python scripts/verify.py topics/searching-sorting/binary-search.md
```

Expected: `OK (1 file(s) verified)`. If any section is missing or any code block is malformed, fix and re-run.

- [ ] **Step 5: Append card section to `RECALL.md`**

Append to `/Users/panibrat/dev/interview-prep/RECALL.md`:

````markdown

## [Binary Search](topics/searching-sorting/binary-search.md) ★★★

<paste the TL;DR from the topic file verbatim>

```python
<paste the Template code block from Section 4 verbatim>
```
````

- [ ] **Step 6: Add entry to `README.md` study order**

Under the `## Study order` heading in `README.md`, append:

```markdown
1. ★★★ [Binary Search](topics/searching-sorting/binary-search.md)
```

(Subsequent tasks will append further numbered entries; final renumbering happens in Task 44.)

- [ ] **Step 7: Create `templates/binary-search.py`**

Create `/Users/panibrat/dev/interview-prep/templates/binary-search.py` with the bare-bones template (just the four functions, no exposition, no smoke tests). Top of file: a short module docstring linking back to `topics/searching-sorting/binary-search.md`.

- [ ] **Step 8: Add entry to `templates/README.md` index**

Append:

```markdown
- [`binary-search.py`](binary-search.py) — classic, leftmost, rightmost, search-on-answer
```

- [ ] **Step 9: Run full verify**

```bash
python scripts/verify.py
python -m pytest scripts/test_verify.py -v
python templates/binary-search.py  # smoke import (file should be importable; no error)
```

Expected: all green.

- [ ] **Step 10: Commit**

```bash
git add topics/searching-sorting/binary-search.md templates/binary-search.py \
        templates/README.md README.md RECALL.md
git commit -m "docs: add binary search reference"
```

---

## Phase 3: Must-Know Tier (remaining 15 topics)

For Tasks 5–19, follow the **Per-topic task workflow** in the Conventions section. Each task below provides the **Topic content brief** that drives the writing.

### Task 5: `topics/searching-sorting/quicksort-mergesort.md`

**Files:** Create `topics/searching-sorting/quicksort-mergesort.md`. Modify `RECALL.md`, `README.md`. (No `templates/` entry — sorting templates rarely needed in interviews; encourage `sorted()` and reach for `heap.py`/`binary-search.py` instead.)

**Topic content brief:**
- **Signal:** "implement sort," "sort with constraints (in-place, stable, k-th element)," "describe how sort works."
- **Key insight:** divide-and-conquer recurrence `T(n) = 2T(n/2) + O(n)` solves to O(n log n). Quicksort's split point depends on data (pivot choice); mergesort's is structural.
- **Walkthrough:** trace mergesort on `[5, 2, 4, 6, 1, 3]` (recursion tree + merge step). Trace quicksort partition on `[3, 6, 8, 10, 1, 2, 1]` with `pivot = last`.
- **Variants to cover:** Lomuto vs Hoare partition; randomized pivot; 3-way partition (Dutch flag) for many duplicates; mergesort on linked list (no extra space for indices); quickselect for k-th element (O(n) average); when each wins (mergesort: stable, predictable, good for linked lists / external sort; quicksort: in-place, cache-friendly, average-case faster).
- **Pitfalls:** worst-case O(n²) for sorted-input quicksort without randomized pivot; mergesort O(n) auxiliary space; off-by-one in partition.
- **Complexity:** average O(n log n), worst O(n²) for quicksort / O(n log n) mergesort; space O(log n) recursion / O(n) merge.
- **LeetCode problems:**
  - [Easy] Merge Sorted Array (88)
  - [Medium] Sort an Array (912 — implement both), Sort List (148 — mergesort on linked list), Kth Largest Element in an Array (215 — quickselect), Sort Colors (75 — Dutch flag)
  - [Hard] Count of Smaller Numbers After Self (315 — mergesort + count), Reverse Pairs (493)
- **Related patterns:** `binary-search.md` (same divide-and-conquer recurrence); `heapsort.md` (alternative O(n log n) sort); `../trees/segment-tree-fenwick.md` (alternative for inversion-count problems).
- **Interviewer follow-ups:**
  - "Pick mergesort or quicksort for this scenario — which and why?"
  - "How do you make quicksort stable?" (you don't trivially; if stability matters, use mergesort.)
  - "Sort 1 TB of integers on a 16 GB machine." (External mergesort.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/searching-sorting/quicksort-mergesort.md`
- `<TOPIC_TITLE>` = `Quicksort & Mergesort`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `quicksort/mergesort`

---

### Task 6: `topics/searching-sorting/heapsort.md`

**Files:** Create `topics/searching-sorting/heapsort.md` and `templates/heap.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "k-th largest/smallest," "top k frequent," "merge k sorted things," "running median," anywhere you need "the next best item" repeatedly.
- **Key insight:** a binary heap stored in an array gives O(log n) insertion/extraction of min (or max) with O(1) peek. In Python you reach for `heapq` first; "implement heapsort" almost never comes up — "use a heap" does.
- **Walkthrough:** show `heappush`/`heappop` evolving an array of `[3, 1, 4, 1, 5, 9]`; sift-up and sift-down diagrams. Trace top-k via min-heap of size k on `nums = [4, 5, 8, 2], k = 2`.
- **Variants to cover:** min-heap vs max-heap (negate values for max-heap in Python's `heapq`); `heapify` in O(n); fixed-size top-k vs full sort; two-heap pattern (median of stream); heap with custom comparator via tuple key.
- **Pitfalls:** Python `heapq` is min-heap only — forgetting to negate; comparing tuples that contain unhashable/uncomparable items at a tie-break position; using a list as a heap and forgetting to call `heapify` first.
- **Complexity:** insertion/extraction O(log n); `heapify` O(n); k-largest in n elements with size-k min-heap: O(n log k).
- **LeetCode problems:**
  - [Easy] Last Stone Weight (1046), Kth Largest Element in a Stream (703)
  - [Medium] Top K Frequent Elements (347), K Closest Points to Origin (973), Task Scheduler (621), Reorganize String (767)
  - [Hard] Merge k Sorted Lists (23), Find Median from Data Stream (295 — two heaps), Sliding Window Median (480)
- **Related patterns:** `quicksort-mergesort.md` (alternative for k-th element via quickselect); `../graphs/shortest-paths.md` (Dijkstra uses a heap); `../two-pointers-sliding-window/sliding-window.md` (some problems use a heap inside the window).
- **Interviewer follow-ups:**
  - "Implement a max-heap from scratch." (Show `_sift_up`/`_sift_down` on an array.)
  - "Stream with billions of items, find top 10." (Min-heap of size 10.)
  - "Median of a stream." (Two heaps, balanced.)

**`templates/heap.py`:** include `top_k_largest(nums, k)` (min-heap of size k), `merge_k_sorted(lists)` skeleton, and a `MedianFinder` class skeleton.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/searching-sorting/heapsort.md`
- `<TOPIC_TITLE>` = `Heapsort & Heaps`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `heap.py`
- `<TOPIC_SLUG>` (for commit) = `heapsort`

---

### Task 7: `topics/two-pointers-sliding-window/two-pointers.md`

**Files:** Create `topics/two-pointers-sliding-window/two-pointers.md` and `templates/two-pointers.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** sorted array (or sortable input); pair/triplet sum; "largest area" type questions on a histogram-like array; in-place array compaction; problems mentioning "without extra space."
- **Key insight:** maintain two indices that move toward each other (or one fast and one slow). Each step either advances at least one pointer or rules out one element, giving O(n).
- **Walkthrough:** trace 2Sum on `[2, 7, 11, 15], target = 18`: `l=0, r=3` → sum 17, advance `l`. Trace 3Sum on `[-4, -1, -1, 0, 1, 2]` with the outer `i` fixed and inner two-pointer.
- **Variants to cover:** opposing pointers (3Sum, container with most water); same-direction (slow/fast for in-place removal — covered more in fast-slow-pointers.md); sorting first as enabler.
- **Pitfalls:** duplicate handling (skip equal neighbors after a hit); inner loops rebuilding state; misuse on unsorted arrays.
- **Complexity:** O(n) after sort, sort dominates → O(n log n) overall for 3Sum-style.
- **LeetCode problems:**
  - [Easy] Two Sum II — Input Array Is Sorted (167), Valid Palindrome (125), Remove Duplicates from Sorted Array (26), Move Zeroes (283)
  - [Medium] 3Sum (15), 3Sum Closest (16), Container With Most Water (11), Sort Colors (75)
  - [Hard] Trapping Rain Water (42), 4Sum (18)
- **Related patterns:** `sliding-window.md`, `fast-slow-pointers.md`, `binary-search.md` (alternative for the "find pair" problems), `../trees/bst.md` (BST iterators give a sorted stream — two-pointer over two BSTs).
- **Interviewer follow-ups:**
  - "What if the array isn't sorted?" (Sort first, or use a hash set; trade-off in space vs time.)
  - "kSum generalization?" (Recursion with two-pointer base case.)

**`templates/two-pointers.py`:** `two_sum_sorted(nums, target)`, `three_sum(nums)`, `container_with_most_water(heights)` — bodies only.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/two-pointers-sliding-window/two-pointers.md`
- `<TOPIC_TITLE>` = `Two Pointers`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `two-pointers.py`
- `<TOPIC_SLUG>` (for commit) = `two-pointers`

---

### Task 8: `topics/two-pointers-sliding-window/fast-slow-pointers.md`

**Files:** Create `topics/two-pointers-sliding-window/fast-slow-pointers.md`. Modify `RECALL.md`, `README.md`. (Templates folder: not added — `two-pointers.py` covers the pattern.)

**Topic content brief:**
- **Signal:** linked-list cycle, find middle of linked list, "k-th from end," duplicate-finding in array indexed-as-graph, palindrome linked list.
- **Key insight:** Floyd's tortoise and hare — if a cycle exists, a pointer moving 2× will eventually meet a pointer moving 1×. Distance math then locates the cycle's start.
- **Walkthrough:** Linked list `1 → 2 → 3 → 4 → 5 → 3 (cycle)`. Trace slow/fast meeting; reset slow to head; both step by 1; meet at cycle start (node 3). Include the math (let cycle entry be at distance `μ`, meeting point at `μ + k`).
- **Variants to cover:** detect cycle existence (just 141); find cycle entry (142); find middle (876); palindrome linked list (234 — find middle, reverse second half, compare); find duplicate in `[1..n]` array using index-as-pointer (287).
- **Pitfalls:** assuming `fast.next` / `fast.next.next` exist (null checks); using fast/slow on doubly-linked or arrays without re-thinking what "next" means.
- **Complexity:** O(n) time, O(1) space.
- **LeetCode problems:**
  - [Easy] Linked List Cycle (141), Middle of the Linked List (876), Palindrome Linked List (234)
  - [Medium] Linked List Cycle II (142), Find the Duplicate Number (287), Happy Number (202 — slow/fast on a function-iteration graph)
  - [Hard] (rare; the pattern's full complexity sits at medium)
- **Related patterns:** `two-pointers.md`, `../graphs/dfs.md` (cycle detection in directed graphs uses different mechanics — note the contrast).
- **Interviewer follow-ups:**
  - "Why does slow=head, both step 1 reach the cycle entry?" (Walk through the distance math.)
  - "Generalize to a function: `f(x) = ...` — does it eventually cycle?" (Yes if the codomain is finite — Happy Number / 287.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/two-pointers-sliding-window/fast-slow-pointers.md`
- `<TOPIC_TITLE>` = `Fast/Slow Pointers`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `fast-slow-pointers`

---

### Task 9: `topics/two-pointers-sliding-window/sliding-window.md`

**Files:** Create `topics/two-pointers-sliding-window/sliding-window.md` and `templates/sliding-window.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "longest/shortest substring/subarray with property X," "max sum of size-k window," "minimum window containing X."
- **Key insight:** maintain a window `[l, r]` with O(1) (or O(k)) state; advance `r`; while a constraint is violated, advance `l`. Each pointer moves O(n) times → O(n) total.
- **Walkthrough:** trace longest substring without repeats on `s = "abcabcbb"`. Show how the window contracts on the duplicate. Then a fixed-size window: max sum of size 3 on `nums = [1, 4, 2, 9, 3]`.
- **Variants to cover:** **fixed-size** (max sum of size k, anagram detection); **variable-size on a constraint** (longest substring with at-most-k distinct, min window substring); **count problems** (number of subarrays with sum = k via prefix sum, contrast with sliding window which doesn't work for negatives).
- **Pitfalls:** sliding window only works for non-negative weights / monotone constraints — confirm before reaching for it; mistakenly maintaining the window with `set`/`Counter` and forgetting to decrement on contract; off-by-one in the answer (`r - l + 1` vs `r - l`).
- **Complexity:** O(n) time, O(k) or O(charset) space.
- **LeetCode problems:**
  - [Easy] Maximum Average Subarray I (643 — fixed), Best Time to Buy and Sell Stock (121 — variant of sliding state)
  - [Medium] Longest Substring Without Repeating Characters (3), Permutation in String (567), Longest Repeating Character Replacement (424), Max Consecutive Ones III (1004), Fruit Into Baskets (904), Minimum Size Subarray Sum (209)
  - [Hard] Minimum Window Substring (76), Sliding Window Maximum (239 — monotonic deque variant), Substring with Concatenation of All Words (30)
- **Related patterns:** `two-pointers.md` (degenerate sliding window — width can be ≥ 0); `../strings/rabin-karp.md` (rolling hash is sliding window over a hash); `../trees/segment-tree-fenwick.md` (range queries, alternative when window doesn't apply).
- **Interviewer follow-ups:**
  - "What if values can be negative?" (Sliding window may not apply; consider prefix sum + hashmap.)
  - "Sliding window maximum?" (Monotonic deque, not a heap.)

**`templates/sliding-window.py`:** `longest_substring_no_repeat(s)`, `min_window(s, t)`, `max_sum_fixed_window(nums, k)`, `monotonic_deque_max(nums, k)`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/two-pointers-sliding-window/sliding-window.md`
- `<TOPIC_TITLE>` = `Sliding Window`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `sliding-window.py`
- `<TOPIC_SLUG>` (for commit) = `sliding-window`

---

### Task 10: `topics/graphs/bfs.md`

**Files:** Create `topics/graphs/bfs.md` and `templates/bfs.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "shortest path in unweighted graph," "level-order," "minimum steps to reach state," grid problems where each step is one move, "minimum mutations" / "word ladder."
- **Key insight:** processing nodes in FIFO order ensures the first time you reach a node, you reach it via the shortest (in edge count) path.
- **Walkthrough:** small graph `0—1, 0—2, 1—3, 2—3, 3—4`. BFS from 0: queue evolution shown. Then a grid BFS: `01 matrix` style.
- **Variants to cover:** graph BFS (adjacency list) vs grid BFS (4 or 8 directions); multi-source BFS (start with multiple nodes in the queue — rotting oranges, walls and gates); 0-1 BFS using a deque for graphs with weights ∈ {0, 1}; bidirectional BFS for shortest path between two specific nodes.
- **Pitfalls:** marking visited at dequeue time vs enqueue time (correct: enqueue time, otherwise duplicates blow up); forgetting to add the start to the visited set; using BFS on weighted graphs (it doesn't give shortest weighted path — use Dijkstra).
- **Complexity:** O(V + E) time, O(V) space.
- **LeetCode problems:**
  - [Easy] Binary Tree Level Order Traversal (102)
  - [Medium] Number of Islands (200 — BFS variant), 01 Matrix (542), Rotting Oranges (994), Walls and Gates (286), Open the Lock (752), Shortest Path in Binary Matrix (1091)
  - [Hard] Word Ladder (127), Word Ladder II (126), Bus Routes (815), Shortest Path Visiting All Nodes (847 — BFS + bitmask)
- **Related patterns:** `dfs.md` (contrast — when to pick which); `topological-sort.md` (Kahn's is a specialization); `shortest-paths.md` (Dijkstra = weighted BFS); `../dp/bitmask-dp.md` (BFS over bitmask states).
- **Interviewer follow-ups:**
  - "BFS or DFS for this problem — and why?" (BFS for shortest unweighted, DFS for connectivity / explicit tree structure.)
  - "What if the graph is infinite (e.g., word ladder with unbounded vocab)?" (Bidirectional BFS to halve the frontier explosion.)

**`templates/bfs.py`:** `bfs_shortest_path(graph, src, dst)`, `bfs_grid(grid, sources)`, `bidirectional_bfs(graph, src, dst)`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/graphs/bfs.md`
- `<TOPIC_TITLE>` = `BFS`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `bfs.py`
- `<TOPIC_SLUG>` (for commit) = `bfs`

---

### Task 11: `topics/graphs/dfs.md`

**Files:** Create `topics/graphs/dfs.md` and `templates/dfs.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "connected components," "find all paths," "cycle detection," "explore everything," tree-shaped recursion, problems that decompose into independent subproblems on a graph.
- **Key insight:** stack-based exploration goes as deep as possible before backtracking — natural fit for recursive subproblems and discovery-time/finish-time invariants.
- **Walkthrough:** the same small graph from BFS, but DFS pre-order. Then iterative DFS using an explicit stack. Then DFS for cycle detection in a directed graph using three-color (white/gray/black).
- **Variants to cover:** recursive vs iterative; pre-order vs post-order discovery (post-order gives reverse topo); cycle detection (undirected: visited + parent; directed: 3-color); SCC name-drop (Tarjan/Kosaraju, see nice-to-have).
- **Pitfalls:** Python recursion limit (~1000 default — `sys.setrecursionlimit` for ~10k node graphs, or convert to iterative); shared-state bugs in recursive backtracking on grids (mutate-restore pattern); forgetting that "visited" semantics differ between paths-counting and reachability problems.
- **Complexity:** O(V + E) time, O(V) space (recursion stack).
- **LeetCode problems:**
  - [Easy] Flood Fill (733)
  - [Medium] Number of Islands (200), Max Area of Island (695), Surrounded Regions (130), Pacific Atlantic Water Flow (417), Course Schedule (207 — cycle detection in directed graph), Number of Provinces (547), Clone Graph (133), Keys and Rooms (841)
  - [Hard] Longest Increasing Path in a Matrix (329 — DFS + memo), Reconstruct Itinerary (332 — Hierholzer / DFS post-order), Critical Connections (1192 — Tarjan)
- **Related patterns:** `bfs.md`, `topological-sort.md`, `union-find.md` (alternative for components), `../backtracking/grid-search.md` (DFS with mutate-restore).
- **Interviewer follow-ups:**
  - "Convert this recursive DFS to iterative." (Show explicit stack with frame state.)
  - "How do you detect a cycle in a directed graph during DFS?" (Three-color or recursion-stack set.)
  - "What if the graph might have 10^7 nodes?" (Iterative; mind memory.)

**`templates/dfs.py`:** `dfs_recursive(graph, start, visited)`, `dfs_iterative(graph, start)`, `has_cycle_directed(graph)` (3-color), `connected_components(graph)`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/graphs/dfs.md`
- `<TOPIC_TITLE>` = `DFS`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `dfs.py`
- `<TOPIC_SLUG>` (for commit) = `dfs`

---

### Task 12: `topics/graphs/topological-sort.md`

**Files:** Create `topics/graphs/topological-sort.md` and `templates/topological-sort.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** dependencies, "build order," "course prerequisites," "task scheduling with constraints," "compile order"; any DAG ordering problem.
- **Key insight:** in a DAG, there exists at least one node with in-degree 0; remove it and recurse on the rest. Two equivalent algorithms: Kahn's (BFS-based, peel off in-degree-0 nodes) and DFS-based (post-order is reverse-topological).
- **Walkthrough:** courses graph `[1, 0], [2, 0], [3, 1], [3, 2]` (course 3 needs 1 and 2; both need 0). Run Kahn's: in-degree array, queue evolves. Then DFS variant: DFS from each unvisited, push to result on finish, reverse at end.
- **Variants to cover:** Kahn's (great when you also want cycle detection — leftover nodes = cycle); DFS-based (cleaner code if you already have a recursive DFS); lexicographically smallest topo order (use a heap instead of a queue in Kahn's); detect cycle vs return ordering (LeetCode 207 vs 210).
- **Pitfalls:** mistakenly using DFS pre-order; forgetting the reverse on DFS-based; treating undirected graphs as DAGs (they're not — every edge looks like a cycle); not handling disconnected DAGs (loop over all nodes).
- **Complexity:** O(V + E) time, O(V) space.
- **LeetCode problems:**
  - [Easy] (rare at easy — pattern is medium)
  - [Medium] Course Schedule (207), Course Schedule II (210), Minimum Height Trees (310 — peel leaves variant), Find Eventual Safe States (802), Sort Items by Groups Respecting Dependencies (1203 — two-level topo)
  - [Hard] Alien Dictionary (269), Parallel Courses III (2050 — DAG longest path)
- **Related patterns:** `bfs.md` (Kahn's is BFS), `dfs.md` (DFS-based variant), `../dp/tree-dp.md` (DAG DP often follows topo order).
- **Interviewer follow-ups:**
  - "What if there's a cycle?" (Detect via leftover in-degree > 0 in Kahn's, or 3-color in DFS.)
  - "Lexicographically smallest topo order?" (Min-heap in Kahn's.)
  - "Topo sort on weighted DAG for longest path?" (Topo + DP.)

**`templates/topological-sort.py`:** `kahn(graph, n)` returning `Optional[List[int]]`, `dfs_topo(graph, n)`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/graphs/topological-sort.md`
- `<TOPIC_TITLE>` = `Topological Sort`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `topological-sort.py`
- `<TOPIC_SLUG>` (for commit) = `topological-sort`

---

### Task 13: `topics/graphs/union-find.md`

**Files:** Create `topics/graphs/union-find.md` and `templates/union-find.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Spec note:** spec section 1 calls out union-find as one of three highest-leverage topics. Give this file extra polish — clear walkthrough of the merge-and-find dance, both optimizations explained.

**Topic content brief:**
- **Signal:** "connected components" with online/offline edges; "are A and B in the same group?"; equivalence classes; Kruskal's MST; "remove edge / add edge and query connectivity"; **incremental** connectivity (offline tricks for decremental — name-drop).
- **Key insight:** represent each set by a tree; the root is the set's canonical id. `find` walks up to root; `union` links one root under the other. Path compression flattens during `find`; union by rank (or size) keeps trees shallow. Together: amortized O(α(n)) ≈ constant.
- **Walkthrough:** elements `0..5`. Sequence of operations: `union(0,1), union(2,3), union(0,2), find(3), union(4,5), find(1)`. Show the parent array after each step, with path compression on the `find(3)` call collapsing the path.
- **Variants to cover:** path compression alone vs union-by-rank alone vs both (both is the standard); tracking component size (useful for problems like "largest island"); weighted union-find for offset relationships (e.g., evaluate division 399); rollback union-find (name-drop, advanced).
- **Pitfalls:** comparing parents directly instead of calling `find` (latent bug when paths haven't been compressed); forgetting to update rank on tied unions; using union-find on graphs with frequent edge removal (it doesn't support that — use offline trick).
- **Complexity:** O(α(n)) amortized per op (≈ 4 for any practical n), O(n) space.
- **LeetCode problems:**
  - [Easy] (rare at easy)
  - [Medium] Number of Provinces (547), Redundant Connection (684), Accounts Merge (721), Number of Operations to Make Network Connected (1319), Most Stones Removed with Same Row or Column (947), Satisfiability of Equality Equations (990), Find Latest Group of Size M (1562)
  - [Hard] Swim in Rising Water (778 — UF on sorted edges), Number of Islands II (305), Bricks Falling When Hit (803 — reverse-time UF), Evaluate Division (399 — weighted UF)
- **Related patterns:** `dfs.md` (alternative for components on static graph), `../nice-to-have/mst.md` (Kruskal uses union-find), `topological-sort.md` (different DAG problem class).
- **Interviewer follow-ups:**
  - "Why amortized α(n)?" (Tarjan's analysis name-drop; intuition: every op flattens a chunk.)
  - "Track component sizes." (Side array updated during union.)
  - "Online edge removal?" (UF doesn't support deletion; offline reverse-time trick or LCT — out of scope.)

**`templates/union-find.py`:** `class UnionFind` with `find`, `union`, `connected`, `size`, both optimizations.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/graphs/union-find.md`
- `<TOPIC_TITLE>` = `Union-Find`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `union-find.py`
- `<TOPIC_SLUG>` (for commit) = `union-find`

---

### Task 14: `topics/graphs/shortest-paths.md`

**Files:** Create `topics/graphs/shortest-paths.md` and `templates/dijkstra.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "shortest path with weights," "minimum cost to traverse," any weighted graph distance question (no negatives). Bellman-Ford / Floyd-Warshall: name-drop only.
- **Key insight (Dijkstra):** with non-negative weights, the closest unsettled node's distance is final. A min-heap gives the next-closest in O(log n); each edge is relaxed at most once.
- **Walkthrough:** small weighted graph `0—1 (4), 0—2 (1), 2—1 (2), 1—3 (1), 2—3 (5)`. Show the heap and `dist[]` array evolving from source 0.
- **Variants to cover:**
  - **Dijkstra** with adjacency list + heap (the workhorse).
  - **Bellman-Ford** (name-drop): O(VE), handles negative edges, detects negative cycles.
  - **Floyd-Warshall** (name-drop): O(V³), all-pairs shortest path, simple to code, dense small-graphs only.
  - **A\*** (forward-link to nice-to-have): Dijkstra + admissible heuristic.
  - K-shortest paths via priority queue without `visited`-set short-circuit (Cheapest Flights with K stops uses a related modification).
- **Pitfalls:** running Dijkstra with negative edges (incorrect); pushing the same node multiple times to heap and forgetting the staleness check (`if d > dist[node]: continue`); using `dist` updates as the visited mechanism instead of a separate set when paths can be re-relaxed via an alternate constraint.
- **Complexity:** Dijkstra O((V + E) log V) with binary heap; O(V² + E) with Fibonacci heap (name-drop); Bellman-Ford O(VE); Floyd-Warshall O(V³).
- **LeetCode problems:**
  - [Medium] Network Delay Time (743), Path with Minimum Effort (1631), Cheapest Flights Within K Stops (787 — modified Dijkstra/BF), Path with Maximum Probability (1514 — max-Dijkstra), Number of Ways to Arrive at Destination (1976)
  - [Hard] Swim in Rising Water (778 — Dijkstra over grid), The Maze II (505), Minimum Cost to Make at Least One Valid Path in a Grid (1368 — 0-1 BFS)
- **Related patterns:** `bfs.md` (Dijkstra = BFS with heap; 0-1 BFS for {0,1} weights); `union-find.md` (different connectivity question); `../nice-to-have/a-star.md` (heuristic Dijkstra).
- **Interviewer follow-ups:**
  - "What if some weights are negative?" (Bellman-Ford.)
  - "All-pairs?" (Floyd-Warshall, or run Dijkstra from each node.)
  - "Tightest bound on a Fibonacci-heap Dijkstra?" (Name-drop O(E + V log V).)

**`templates/dijkstra.py`:** `dijkstra(graph, src)` returning dist dict; `dijkstra_with_path(graph, src, dst)` reconstructing path via predecessor map.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/graphs/shortest-paths.md`
- `<TOPIC_TITLE>` = `Shortest Paths (Dijkstra)`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = `dijkstra.py`
- `<TOPIC_SLUG>` (for commit) = `shortest-paths`

---

### Task 15: `topics/dp/1d-dp.md`

**Files:** Create `topics/dp/1d-dp.md`. Modify `RECALL.md`, `README.md`. (No template — DP boilerplate is too problem-specific.)

**Topic content brief:**
- **Signal:** "ways to reach state n," "max/min value ending at index i," "decode/parse with overlapping subproblems," "fewest steps," classical DP recurrences with one moving index.
- **Key insight:** define `dp[i]` as a single scalar that summarizes everything you need to know about the first `i` elements (or about state at position `i`). Each `dp[i]` is a function of a small constant number of earlier states.
- **Walkthrough:** trace House Robber on `[2, 7, 9, 3, 1]`: `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`. Show the table fill and the rolling-window optimization down to two variables.
- **Variants to cover:**
  - **Constant-state recurrence** (House Robber, Climbing Stairs): roll to O(1) space.
  - **String DP** (Decode Ways): index over characters; transitions inspect one or two characters back.
  - **Subsequence DP** (LIS): `dp[i] = 1 + max(dp[j] for j < i if nums[j] < nums[i])` — O(n²); patience-sorting variant gives O(n log n) with binary search.
  - **Coin Change**: `dp[amount]` is a 1D array indexed by amount, not by input position — same family but the dimension is the value space.
- **Pitfalls:** initializing `dp[0]` correctly when the recurrence references `dp[i-2]`; mistakenly applying the rolling-window optimization when transitions look back further; word-break-style problems where `dp[i]` is "is the prefix of length i breakable" not a count.
- **Complexity:** typically O(n) time and space; O(1) space after rolling.
- **LeetCode problems:**
  - [Easy] Climbing Stairs (70), House Robber (198), Min Cost Climbing Stairs (746), Fibonacci Number (509)
  - [Medium] House Robber II (213 — circular), Decode Ways (91), Coin Change (322), Word Break (139), Longest Increasing Subsequence (300), Maximum Subarray (53 — Kadane), Best Time to Buy and Sell Stock with Cooldown (309)
  - [Hard] Longest Valid Parentheses (32), Coin Change II (518 — order-irrelevant counting variant)
- **Related patterns:** `2d-dp.md` (when the recurrence needs two indices), `../greedy/interval-scheduling.md` (sometimes greedy beats DP — when?), `tree-dp.md`.
- **Interviewer follow-ups:**
  - "Reduce space to O(1)." (Show rolling.)
  - "What if the DP table is sparse?" (Memoize a hash map instead of an array.)
  - "Reconstruct the actual choice sequence, not just the value." (Maintain a parent array; back-trace at the end.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/dp/1d-dp.md`
- `<TOPIC_TITLE>` = `1D DP`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `1d-dp`

---

### Task 16: `topics/dp/2d-dp.md`

**Files:** Create `topics/dp/2d-dp.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** problems involving two strings, two arrays, or a grid; "edit distance," "LCS," "knapsack," "unique paths," "interleaving."
- **Key insight:** `dp[i][j]` summarizes the answer for the prefix of length `i` of one input and prefix `j` of the other (or position `(i, j)` in a grid). Transitions look at neighbors `(i-1, j)`, `(i, j-1)`, `(i-1, j-1)`.
- **Walkthrough:** Edit Distance from `"horse"` to `"ros"`. Show the full 6×4 table, point out the three transitions per cell.
- **Variants to cover:**
  - **Grid DP** (Unique Paths, Minimum Path Sum): the table mirrors the grid.
  - **String DP** (Edit Distance, LCS): table indexed by prefix lengths.
  - **0/1 Knapsack**: `dp[i][w]` "best value using first i items with capacity w." Two transitions: take or skip. Roll to 1D, iterate weight backwards.
  - **Unbounded Knapsack** (Coin Change variants): same but iterate weight forwards.
  - **Subset Sum / Partition Equal Subset Sum** (416): boolean knapsack.
- **Pitfalls:** mixing up loop directions when rolling 2D → 1D for knapsack (forwards = unbounded; backwards = 0/1); off-by-one when `dp[i][j]` means "first i" vs "ending at i"; forgetting base row/column initialization.
- **Complexity:** typically O(n·m) time and space; many problems roll to O(min(n, m)) space.
- **LeetCode problems:**
  - [Medium] Unique Paths (62), Minimum Path Sum (64), Longest Common Subsequence (1143), Edit Distance (72), Partition Equal Subset Sum (416), Target Sum (494), Last Stone Weight II (1049), Coin Change II (518), Maximal Square (221), Unique Paths II (63)
  - [Hard] Distinct Subsequences (115), Interleaving String (97), Regular Expression Matching (10), Wildcard Matching (44)
- **Related patterns:** `1d-dp.md`, `interval-dp.md`, `bitmask-dp.md`.
- **Interviewer follow-ups:**
  - "Reduce space to O(min(n, m))." (Roll along the smaller dimension.)
  - "Reconstruct the alignment / item set." (Backtrace from `dp[n][m]`.)
  - "Edit Distance with custom op costs." (Generalize the three transitions.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/dp/2d-dp.md`
- `<TOPIC_TITLE>` = `2D DP`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `2d-dp`

---

### Task 17: `topics/dp/interval-dp.md`

**Files:** Create `topics/dp/interval-dp.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "merge piles into one," "burst balloons in best order," "minimum cost to triangulate," "matrix chain multiplication," any problem where the cost of combining ranges depends on the order of combination.
- **Key insight:** `dp[i][j]` is the optimal answer for the subarray `[i..j]`. Transition picks a split point or last-action: `dp[i][j] = best over k of dp[i][k-1] + dp[k+1][j] + cost(i, k, j)`. Iterate by interval length, not by `i` or `j` directly.
- **Walkthrough:** Burst Balloons on `[3, 1, 5, 8]`. Pad with virtual 1s. Show length-2, length-3, length-4 fills.
- **Variants to cover:** matrix chain (305 — name-drop, classic textbook); burst balloons; minimum cost to cut a stick; remove boxes (715-style — adds a third dimension); palindromic subsequence/substring DP (interval over a single string).
- **Pitfalls:** iterating in wrong order (must iterate by length to ensure subintervals are computed first); off-by-one in the split point loop; forgetting that "last-action" framing (what was the last balloon to burst?) is often clearer than "first-action."
- **Complexity:** O(n³) time, O(n²) space — usually.
- **LeetCode problems:**
  - [Medium] Longest Palindromic Subsequence (516), Stone Game (877 — game variant), Minimum Cost to Cut a Stick (1547)
  - [Hard] Burst Balloons (312), Strange Printer (664), Remove Boxes (546), Predict the Winner (486 — minimax variant)
- **Related patterns:** `1d-dp.md` (when interval reduces to a single moving index), `2d-dp.md`, `../trees/segment-tree-fenwick.md` (for range queries — different, often confused).
- **Interviewer follow-ups:**
  - "Why O(n³)?" (n² intervals × n splits.)
  - "When does last-action framing beat first-action?" (Burst Balloons — picking 'first to burst' is hard because dependencies remain; 'last to burst' clean-splits the range.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/dp/interval-dp.md`
- `<TOPIC_TITLE>` = `Interval DP`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `interval-dp`

---

### Task 18: `topics/dp/tree-dp.md`

**Files:** Create `topics/dp/tree-dp.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** problems on a tree where the answer at a node depends on its children (or sometimes on its ancestor + children); "max path through tree," "minimum cameras to cover," "rob a tree of houses."
- **Key insight:** post-order DFS naturally computes child subproblems before the parent. State is often a small tuple per node, e.g., `(took_node, did_not_take_node)`.
- **Walkthrough:** House Robber III on a small tree. Each node returns `(rob, no_rob)`; parent combines.
- **Variants to cover:**
  - State-tuple recurrence (House Robber III, Tree Cameras).
  - Diameter / longest path (track best two from each subtree).
  - Re-rooting DP (sum of distances to all nodes — name-drop, advanced).
  - Tree DP on a rooted DAG (from topological sort).
- **Pitfalls:** Python recursion limit for deep trees (raise `sys.setrecursionlimit`); confusing "longest path through node" (sum of two best paths into it) vs "longest path in subtree" (single best path).
- **Complexity:** O(n) time and space (recursion stack).
- **LeetCode problems:**
  - [Medium] House Robber III (337), Diameter of Binary Tree (543), Path Sum III (437)
  - [Hard] Binary Tree Maximum Path Sum (124), Binary Tree Cameras (968), Distribute Coins in Binary Tree (979), Sum of Distances in Tree (834 — re-rooting)
- **Related patterns:** `../trees/traversals.md` (post-order is the engine), `topological-sort.md` (DAG DP analog), `1d-dp.md`.
- **Interviewer follow-ups:**
  - "Iterative version?" (Explicit stack with frame state — typically not asked.)
  - "Re-rooting trick?" (Two-pass DFS — explain at high level.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/dp/tree-dp.md`
- `<TOPIC_TITLE>` = `Tree DP`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `tree-dp`

---

### Task 19: `topics/dp/bitmask-dp.md`

**Files:** Create `topics/dp/bitmask-dp.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** small N (≤ ~20), "visit all," "TSP-like," subset enumeration, "minimum cost to cover all jobs/people," constraints that scream "bitmask" because the state size is 2^N.
- **Key insight:** the state of "which subset has been processed/used" can be encoded in an integer of N bits. `dp[mask]` (or `dp[mask][i]`) gives the answer when those elements have been chosen so far.
- **Walkthrough:** TSP from city 0 with distance matrix `[[0,10,15,20],[10,0,35,25],[15,35,0,30],[20,25,30,0]]`. `dp[mask][i]` = minimum cost to start at 0, visit set `mask`, end at city `i`. Show two transitions for `mask = 0b0111`.
- **Variants to cover:**
  - **Held-Karp TSP** (`dp[mask][i]`).
  - **Assignment problem** (`dp[mask]` = best assignment of first `popcount(mask)` people to the items in `mask`).
  - **Subset-sum / partitioning** (`dp[mask]` boolean).
  - **Bitmask + BFS** (Shortest Path Visiting All Nodes — state = (node, mask)).
- **Pitfalls:** N ≤ 20 (otherwise 2^N explodes); subset enumeration `for sub in submasks(mask)` (the classic `sub = (sub - 1) & mask`); forgetting that subset DP is O(3^N) in worst case (enumeration over all submasks of all masks).
- **Complexity:** typically O(2^N · N) for TSP-like; O(3^N) for submask DP.
- **LeetCode problems:**
  - [Medium] Beautiful Arrangement (526), Partition to K Equal Sum Subsets (698)
  - [Hard] Shortest Path Visiting All Nodes (847), Smallest Sufficient Team (1125), Minimum Cost to Make at Least One Valid Path in a Grid (1368 — variant), Find Minimum Time to Finish All Jobs (1723), Number of Ways to Wear Different Hats to Each Other (1434), Maximum Students Taking Exam (1349), Minimum Number of Work Sessions to Finish the Tasks (1986)
- **Related patterns:** `bfs.md` (state-space BFS), `2d-dp.md`, `topological-sort.md`, `tree-dp.md`.
- **Interviewer follow-ups:**
  - "Why does N ≤ 20 matter?" (2^20 ≈ 10^6, fits in memory and time; 2^25 doesn't.)
  - "Submask iteration trick?" (Show `sub = (sub - 1) & mask`.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/dp/bitmask-dp.md`
- `<TOPIC_TITLE>` = `Bitmask DP`
- `<TIER_STARS>` = `★★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `bitmask-dp`

---

## Phase 4: Strongly-Recommended Tier (15 topics)

Same per-topic workflow.

### Task 20: `topics/strings/kmp.md`

**Files:** `topics/strings/kmp.md`, `templates/kmp.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "find pattern in text," substring search where naive O(nm) is too slow, problems involving longest proper prefix that is also a suffix.
- **Key insight:** the failure-function (LPS array) tells you, on a mismatch, where in the pattern to resume — never re-scan the text. Total work O(n + m).
- **Walkthrough:** build LPS for `pattern = "ABABCABAB"`. Then trace search of pattern in `text = "ABABCABABABABCABAB"`.
- **Variants to cover:** classic substring search; LPS for "find longest prefix of `s` that is also a suffix" (= longest happy prefix); checking if `s = a + a + a` (repeat substring) via `len(s) % (len(s) - lps[-1]) == 0`.
- **Pitfalls:** off-by-one in LPS construction; conflating LPS index with length; using KMP when a hashmap or Z-function would be simpler.
- **Complexity:** O(n + m) time, O(m) space.
- **LeetCode problems:**
  - [Medium] Find the Index of the First Occurrence in a String (28), Repeated Substring Pattern (459), Longest Happy Prefix (1392)
  - [Hard] Shortest Palindrome (214), Sum of Scores of Built Strings (2223 — Z-function alternative)
- **Related patterns:** `rabin-karp.md` (hash-based alternative), `../nice-to-have/z-algorithm.md` (often simpler), `trie.md` (multi-pattern via Aho-Corasick — name-drop).
- **Interviewer follow-ups:**
  - "Multiple patterns at once?" (Aho-Corasick — KMP + trie. Name-drop.)
  - "Find all occurrences, not just the first." (Continue past the match using the LPS.)

**`templates/kmp.py`:** `compute_lps(pattern)`, `kmp_search(text, pattern) -> List[int]`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/strings/kmp.md`
- `<TOPIC_TITLE>` = `KMP`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = `kmp.py`
- `<TOPIC_SLUG>` (for commit) = `kmp`

---

### Task 21: `topics/strings/rabin-karp.md`

**Files:** `topics/strings/rabin-karp.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** find substring or k-length window with hash equality; plagiarism / repeated-substring detection; rolling-hash sliding window.
- **Key insight:** treat a string window as a base-B number mod a large prime. Sliding by one character is O(1): drop the high digit, multiply by B, add the new low digit.
- **Walkthrough:** roll a hash on `text = "ababcd", k = 3` showing each step. Discuss hash collisions and the verify-on-match practice.
- **Variants to cover:** single pattern (rare beats KMP unless you're hashing for set lookups); set of length-k patterns (hash all into a set, slide once over text); 2D rolling hash for matrix substring; double hashing to avoid adversarial collisions.
- **Pitfalls:** hash collisions — always verify; modular inverse for "remove the high digit" pattern; choice of base and prime (use two primes for double hashing).
- **Complexity:** O(n + m) average; O(nm) worst with collisions.
- **LeetCode problems:**
  - [Medium] Repeated DNA Sequences (187), Find All Anagrams in a String (438 — sliding-window alternative)
  - [Hard] Longest Duplicate Substring (1044 — binary search on length + Rabin-Karp), Distinct Echo Substrings (1316), Longest Common Subpath (1923)
- **Related patterns:** `kmp.md`, `../two-pointers-sliding-window/sliding-window.md`, `../nice-to-have/z-algorithm.md`.
- **Interviewer follow-ups:**
  - "Why double hashing?" (Adversarial inputs can find collisions for a single mod prime.)
  - "Find longest repeated substring efficiently." (Binary search on length + Rabin-Karp; or suffix array — name-drop.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/strings/rabin-karp.md`
- `<TOPIC_TITLE>` = `Rabin-Karp`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `rabin-karp`

---

### Task 22: `topics/strings/trie.md`

**Files:** `topics/strings/trie.md`, `templates/trie.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Spec note:** spec section 1 calls out trie as one of three highest-leverage topics. Polish accordingly.

**Topic content brief:**
- **Signal:** prefix matching, autocomplete, "word search II," dictionary lookups with wildcards, multi-pattern search, longest common prefix queries.
- **Key insight:** a tree where each node represents a character and root-to-node paths are prefixes. Lookup, insert, and prefix-existence are all O(L) where L is the word length.
- **Walkthrough:** insert `["cat", "car", "card", "dog"]`. Draw the tree. Show how `startsWith("ca")` traverses two nodes.
- **Variants to cover:**
  - Dict-of-dicts vs class-based trie node.
  - End-of-word marker.
  - Trie + DFS (Word Search II combines a board DFS with a trie of patterns to prune early).
  - Trie of bits for max-XOR problems (bitwise trie).
  - Compressed trie (radix tree) — name-drop.
- **Pitfalls:** memory: a trie can be huge; consider arrays-as-children only when alphabet is small (e.g., lowercase: 26-array). Forgetting the end-of-word marker → false positives. Using a trie when a hashset suffices (always benchmark; trie's win is prefix queries, not exact lookups).
- **Complexity:** insert/lookup O(L); space O(N · L) worst case.
- **LeetCode problems:**
  - [Easy] Longest Common Prefix (14 — alternative)
  - [Medium] Implement Trie (208), Design Add and Search Words (211 — wildcards), Map Sum Pairs (677), Replace Words (648), Longest Word in Dictionary (720)
  - [Hard] Word Search II (212), Maximum XOR of Two Numbers in an Array (421 — bitwise trie), Stream of Characters (1032), Word Squares (425), Concatenated Words (472), Palindrome Pairs (336)
- **Related patterns:** `kmp.md` (Aho-Corasick is multi-pattern KMP via trie), `../backtracking/grid-search.md` (Word Search II uses both), `../graphs/dfs.md`.
- **Interviewer follow-ups:**
  - "Wildcard search (`.`)?" (DFS over the trie, branching on `.`.)
  - "Memory-tight implementation?" (Class-based with `__slots__` or fixed-size children array for limited alphabets.)
  - "Auto-complete top-3 by frequency?" (Each node stores top-k via heap or sorted list; or compute on demand via DFS.)

**`templates/trie.py`:** `class Trie` (insert / search / startsWith) with both children-dict and children-array variants noted in comments.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/strings/trie.md`
- `<TOPIC_TITLE>` = `Trie`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = `trie.py`
- `<TOPIC_SLUG>` (for commit) = `trie`

---

### Task 23: `topics/trees/traversals.md`

**Files:** `topics/trees/traversals.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** anything binary-tree shaped where you need to visit every node; serialize/deserialize; tree-to-list; check structural property.
- **Key insight:** four canonical orders — pre, in, post, level. Each has a recursive one-liner and a tractable iterative counterpart using a stack (or queue for level-order).
- **Walkthrough:** tree `[1, 2, 3, 4, 5, 6, 7]`. List output for all four orders. Then iterative inorder with a stack — show the stack contents step by step.
- **Variants to cover:** Morris traversal (O(1) space — name-drop, hard); reconstruction from two traversals (preorder + inorder; postorder + inorder); right-side view / vertical order (BFS variants); serialization formats.
- **Pitfalls:** confusing recursive depth with stack space; iterative postorder is the trickiest — two stacks or "last-visited" tracking; reconstruction needs unique values.
- **Complexity:** O(n) time, O(h) space (recursion or stack).
- **LeetCode problems:**
  - [Easy] Binary Tree Inorder Traversal (94), Preorder (144), Postorder (145), Same Tree (100), Maximum Depth (104)
  - [Medium] Binary Tree Level Order Traversal (102), Binary Tree Zigzag Level Order Traversal (103), Construct Binary Tree from Preorder and Inorder Traversal (105), Binary Tree Right Side View (199), Serialize and Deserialize Binary Tree (297)
  - [Hard] Binary Tree Maximum Path Sum (124 — covered in tree-dp), Recover Binary Search Tree (99 — Morris)
- **Related patterns:** `bst.md`, `../dp/tree-dp.md`, `lca.md`, `../graphs/bfs.md`, `../graphs/dfs.md`.
- **Interviewer follow-ups:**
  - "Iterative postorder?" (Two-stack trick or last-visited.)
  - "Reconstruct from preorder + inorder." (Recursive with index map.)
  - "Morris traversal?" (Name-drop O(1) space, threaded via right-most-of-left subtree.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/trees/traversals.md`
- `<TOPIC_TITLE>` = `Tree Traversals`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `tree-traversals`

---

### Task 24: `topics/trees/bst.md`

**Files:** `topics/trees/bst.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "binary search tree" stated; "k-th smallest in a tree"; insert/delete/validate problems; sorted-property queries on a tree.
- **Key insight:** BST invariant — left subtree all less, right subtree all greater. Inorder traversal is sorted ascending. Search/insert/delete all O(h); h = log n if balanced.
- **Walkthrough:** validate `[2, 1, 3]` and `[5, 1, 4, null, null, 3, 6]`. Inorder of the second produces `[1, 5, 3, 4, 6]` — not sorted, so invalid. Then trace BST insert of 4 into a small tree.
- **Variants to cover:** validation (range method beats inorder for negative values / duplicates); insert (return new root); delete (three cases — leaf / one child / two children with inorder successor); kth smallest (inorder count); LCA in BST (compare with both, descend).
- **Pitfalls:** validation with `< prev` instead of `≤ prev` when duplicates allowed; deleting a node with two children (use inorder successor's value, then delete the successor); pathological insertion order → unbalanced tree.
- **Complexity:** O(h) per op; balanced BSTs (Red-Black, AVL) maintain O(log n) — name-drop, almost never coded in interviews.
- **LeetCode problems:**
  - [Easy] Search in a Binary Search Tree (700), LCA of BST (235), Convert Sorted Array to BST (108), Range Sum of BST (938)
  - [Medium] Validate BST (98), Insert into a BST (701), Delete Node in a BST (450), Kth Smallest Element in a BST (230), Trim a BST (669), BST Iterator (173 — iterative inorder)
  - [Hard] Recover Binary Search Tree (99), Closest Binary Search Tree Value II (272), Merge BSTs to Create Single BST (1932)
- **Related patterns:** `traversals.md`, `lca.md`, `../graphs/dfs.md`, `binary-search.md` (BST search ↔ binary search on a sorted view).
- **Interviewer follow-ups:**
  - "What if the tree might be unbalanced and have 10^6 nodes?" (Iterative for stack safety; or treap/AVL — but those are out of scope.)
  - "Persistent BST?" (Functional structure — name-drop only.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/trees/bst.md`
- `<TOPIC_TITLE>` = `Binary Search Tree`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `bst`

---

### Task 25: `topics/trees/lca.md`

**Files:** `topics/trees/lca.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "lowest common ancestor of two nodes," distance between two nodes in a tree, "shortest path between two nodes in an undirected tree."
- **Key insight:** in a tree, the LCA is the deepest node that is an ancestor of both. Recursive DFS: if both targets sit in different subtrees → current is LCA; else recurse into the side that has at least one.
- **Walkthrough:** tree `[3, 5, 1, 6, 2, 0, 8, null, null, 7, 4]`. LCA(5, 1) = 3. LCA(5, 4) = 5. Trace the recursion tree for the second.
- **Variants to cover:** recursive (the workhorse); BST-specific (compare against both); with parent pointers (set-based ancestor walk); iterative parent-pointers two-pointer balance walk; **Euler tour + RMQ** (the fancy O(n log n) preprocessing / O(1) query version — explain at high level, code is heavy); binary lifting (O(n log n) prep / O(log n) query — name-drop).
- **Pitfalls:** assuming both nodes exist (1644 variant); treating the "any common ancestor" or "deepest descendant" instead of LCA proper; for BST, forgetting the comparison-only shortcut.
- **Complexity:** Naive recursion O(n) per query; binary lifting O(log n) per query after O(n log n) prep; Euler+RMQ O(1) per query after O(n log n) prep.
- **LeetCode problems:**
  - [Easy] LCA of a Binary Search Tree (235)
  - [Medium] LCA of a Binary Tree (236), LCA of a Binary Tree II (1644 — handle missing), LCA of a Binary Tree III (1650 — parent pointers), Smallest Subtree with All the Deepest Nodes (865)
  - [Hard] LCA of Deepest Leaves (1123), LCA of a Binary Tree IV (1676 — multiple nodes)
- **Related patterns:** `traversals.md`, `bst.md`, `segment-tree-fenwick.md` (RMQ underlies fancy LCA), `../graphs/dfs.md`.
- **Interviewer follow-ups:**
  - "What if you have q ≈ 10^5 queries?" (Binary lifting; sketch the parent-table doubling.)
  - "Distance between two nodes?" (`depth(u) + depth(v) - 2 * depth(LCA)`.)
  - "How would you handle a forest?" (Run LCA per tree component; if u and v in different components, undefined.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/trees/lca.md`
- `<TOPIC_TITLE>` = `Lowest Common Ancestor`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `lca`

---

### Task 26: `topics/trees/segment-tree-fenwick.md`

**Files:** `topics/trees/segment-tree-fenwick.md`, `templates/segment-tree.py`, `templates/fenwick-tree.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** range queries with point updates (or vice versa); "sum/min/max over [l, r] with mutations"; counting inversions; offline range problems.
- **Key insight:** Fenwick (BIT) is a compact O(log n) structure for point-update + prefix-sum (and combinations). Segment tree is the more general data structure: any associative operation on ranges, plus lazy propagation for range updates.
- **Walkthrough:** Build a Fenwick tree on `[1, 2, 3, 4, 5]`. Show `update(2, +3)` and `prefix_sum(4)`. Then a segment tree on the same array — show the recursive build, point update, range sum query.
- **Variants to cover:**
  - Fenwick: prefix sum, min/max via dual-trick (less general); range update + point query via difference array.
  - Segment tree: classical (sum/min/max); lazy propagation for range update + range query; persistent (name-drop); 2D segment tree (name-drop).
- **Pitfalls:** Fenwick is 1-indexed in the standard formulation — index translation is the most common bug; segment tree size needs to be 4n in the safe array form; lazy propagation: forget to push before query.
- **Complexity:** Fenwick build O(n), op O(log n); segment tree build O(n), op O(log n).
- **LeetCode problems:**
  - [Medium] Range Sum Query — Mutable (307)
  - [Hard] Count of Smaller Numbers After Self (315), Reverse Pairs (493), Count of Range Sum (327), Range Sum Query 2D — Mutable (308), The Skyline Problem (218 — segment tree variant), Falling Squares (699), Range Module (715), Number of Longest Increasing Subsequence (673 — alternative)
- **Related patterns:** `lca.md` (Euler+RMQ uses segment tree); `../dp/interval-dp.md` (different, not a substitute); `../searching-sorting/quicksort-mergesort.md` (mergesort solves some inversion-count problems without these structures).
- **Interviewer follow-ups:**
  - "Range update + point query?" (Difference array on Fenwick.)
  - "Range update + range query?" (Lazy segment tree.)
  - "When pick segment tree over Fenwick?" (Non-sum operations, lazy updates, more complex queries.)

**`templates/segment-tree.py`:** classic `SegmentTree` with `update_point`, `query_range`. Skeleton stub for lazy version.
**`templates/fenwick-tree.py`:** `class BIT` with `update` and `prefix_sum`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/trees/segment-tree-fenwick.md`
- `<TOPIC_TITLE>` = `Segment Tree & Fenwick`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = `segment-tree.py`, `fenwick-tree.py` (create both)
- `<TOPIC_SLUG>` (for commit) = `segment-tree-fenwick`

---

### Task 27: `topics/greedy/interval-scheduling.md`

**Files:** `topics/greedy/interval-scheduling.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** intervals on a line, "merge / insert / count overlaps," "minimum rooms," "max non-overlapping" subset.
- **Key insight:** sort by some endpoint (start vs end depends on the problem). Then sweep: most interval problems collapse to a linear scan.
- **Walkthrough:** Merge Intervals on `[[1,3],[2,6],[8,10],[15,18]]`. Sort by start; iterate; merge if `cur.start <= last.end`.
- **Variants to cover:**
  - **Merge / insert** (sort by start, sweep).
  - **Min rooms / max overlaps** (event-based sweep, +1 on start, −1 on end, track running max; or sort starts and ends separately and two-pointer).
  - **Max non-overlapping subset** (sort by **end**, greedy take-earliest-end).
  - **Min arrows / min taps** (greedy on intervals + reach extension).
- **Pitfalls:** picking the wrong sort key (sort by end for "max non-overlapping," start for "merge"); inclusive vs exclusive endpoints; ties.
- **Complexity:** O(n log n) sort dominates.
- **LeetCode problems:**
  - [Easy] Meeting Rooms (252)
  - [Medium] Merge Intervals (56), Insert Interval (57), Non-overlapping Intervals (435), Meeting Rooms II (253), Minimum Number of Arrows to Burst Balloons (452), Car Pooling (1094), Minimum Number of Taps to Open to Water a Garden (1326), Maximum Profit in Job Scheduling (1235 — greedy + DP)
  - [Hard] Employee Free Time (759), Data Stream as Disjoint Intervals (352)
- **Related patterns:** `activity-selection.md` (overlap), `../trees/segment-tree-fenwick.md` (alternative for some interval-add problems).
- **Interviewer follow-ups:**
  - "Same problem but starts/ends are streamed?" (Sorted multiset / two heaps.)
  - "Find a busy schedule with minimum machines?" (Same as min rooms.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/greedy/interval-scheduling.md`
- `<TOPIC_TITLE>` = `Interval Scheduling`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `interval-scheduling`

---

### Task 28: `topics/greedy/activity-selection.md`

**Files:** `topics/greedy/activity-selection.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "select max number of compatible activities," "minimize cost merging things," classical greedy proof patterns; Huffman coding (name-drop).
- **Key insight:** when a local greedy choice is provably optimal — typically by an exchange argument — you can build the global solution by always taking the locally best move. Activity selection: sort by finish time, take earliest-finishing compatible.
- **Walkthrough:** activities with `(start, finish)` pairs `[(1,4),(3,5),(0,6),(5,7),(3,8),(5,9),(6,10),(8,11),(8,12),(2,13),(12,14)]`. Sort by finish; greedily pick.
- **Variants to cover:**
  - Activity selection (= max non-overlapping intervals — links to interval-scheduling.md, slightly different framing).
  - **Huffman coding** (build optimal prefix code by repeatedly merging two smallest-frequency nodes via a min-heap). Name-drop with sketch — interviewers rarely make you code it.
  - Fractional knapsack (sort by value/weight density). Note: 0/1 knapsack is **not** greedy — it's DP.
  - Job scheduling with deadlines and penalties.
- **Pitfalls:** assuming a greedy works without an exchange-argument check; mixing up fractional vs 0/1 knapsack; thinking Huffman applies without a frequency-distribution.
- **Complexity:** O(n log n) sort; Huffman O(n log n) heap.
- **LeetCode problems:**
  - [Medium] Non-overlapping Intervals (435), Minimum Number of Arrows to Burst Balloons (452), Minimum Number of Taps to Open to Water a Garden (1326), Boats to Save People (881), Minimum Cost to Connect Sticks (1167 — Huffman-flavored heap merge), Reorganize String (767)
  - [Hard] Task Scheduler (621 — name-greedy + math), IPO (502)
- **Related patterns:** `interval-scheduling.md`, `../searching-sorting/heapsort.md` (Huffman uses a heap), `../dp/2d-dp.md` (0/1 knapsack contrast).
- **Interviewer follow-ups:**
  - "How do you prove the greedy is optimal?" (Exchange argument template: assume an optimal solution differs from greedy; swap; show no worse.)
  - "Sketch Huffman." (Min-heap of frequencies; pop two; push their sum; repeat.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/greedy/activity-selection.md`
- `<TOPIC_TITLE>` = `Activity Selection (and Huffman name-drop)`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `activity-selection`

---

### Task 29: `topics/backtracking/backtracking-template.md`

**Files:** `topics/backtracking/backtracking-template.md`, `templates/backtracking.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "all permutations / combinations / subsets," "find all valid configurations," small input where exponential exploration is acceptable; "build a solution element by element with constraints."
- **Key insight:** systematically explore the decision tree; when a partial solution can't extend to a valid full solution, prune. The skeleton: try each candidate, recurse, undo. The "undo" — restoring the state — is the move that distinguishes backtracking from naive recursion.
- **Walkthrough:** generate all subsets of `[1, 2, 3]`. Show the recursion tree. Then permutations of `[1, 2, 3]` with the in-place swap variant (no extra memory) and the visited-set variant.
- **Variants to cover:**
  - Subsets (each element: take or skip).
  - Permutations (with and without duplicates).
  - Combinations (ordered selection without repetition).
  - Combination sum (with reuse vs without).
  - Pruning: handle duplicates by sorting + skipping equal siblings.
- **Pitfalls:** mutating shared state without restoring; appending the working list directly instead of a copy (later mutations clobber the result); failing to prune.
- **Complexity:** O(2^n · n) for subsets, O(n!) for permutations, etc. — exponential. Inputs are small for a reason.
- **LeetCode problems:**
  - [Medium] Subsets (78), Subsets II (90), Permutations (46), Permutations II (47), Combinations (77), Combination Sum (39), Combination Sum II (40), Combination Sum III (216), Letter Combinations of a Phone Number (17), Generate Parentheses (22), Palindrome Partitioning (131), Restore IP Addresses (93)
  - [Hard] Word Break II (140)
- **Related patterns:** `n-queens-sudoku.md`, `grid-search.md`, `../dp/bitmask-dp.md` (state-compressed alternative when subsets are the universe).
- **Interviewer follow-ups:**
  - "Avoid duplicates in the result." (Sort first; skip equal siblings at the same recursion depth.)
  - "Iterative version?" (Sometimes possible — bitmask enumeration for subsets; rarely cleaner.)
  - "Memory: prune the recursion stack." (Iterative deepening — name-drop.)

**`templates/backtracking.py`:** `subsets(nums)`, `permutations(nums)`, `combinations(n, k)`, `combination_sum(candidates, target)`. All as bare bodies.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/backtracking/backtracking-template.md`
- `<TOPIC_TITLE>` = `Backtracking Template`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = `backtracking.py`
- `<TOPIC_SLUG>` (for commit) = `backtracking-template`

---

### Task 30: `topics/backtracking/n-queens-sudoku.md`

**Files:** `topics/backtracking/n-queens-sudoku.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** constraint satisfaction problems with explicit row/column/diagonal/region constraints; "place queens such that...," "fill the Sudoku board."
- **Key insight:** N-Queens and Sudoku Solver are the same template as backtracking-template, with row-by-row (or empty-cell-by-empty-cell) iteration and bitmask-or-set conflict tracking.
- **Walkthrough:** N-Queens for n=4. Show the recursion: place row 0 in col 0; conflicts in row 1; backtrack; etc. Use sets `cols`, `pos_diag` (`r + c`), `neg_diag` (`r - c`).
- **Variants to cover:**
  - N-Queens (count solutions vs print solutions).
  - Sudoku solver (find a valid filling) vs Sudoku validator (check current state).
  - General CSP framing: variables, domains, constraints.
  - MRV heuristic (pick the most-constrained variable first) — name-drop.
- **Pitfalls:** diagonal index sign; missing one of the three constraint sets; using deep copies of the board where in-place mutate-and-restore would do.
- **Complexity:** O(n!) for N-Queens; Sudoku is technically NP-hard but tiny n=9 makes it instant.
- **LeetCode problems:**
  - [Medium] Valid Sudoku (36)
  - [Hard] N-Queens (51), N-Queens II (52), Sudoku Solver (37)
- **Related patterns:** `backtracking-template.md`, `../dp/bitmask-dp.md`.
- **Interviewer follow-ups:**
  - "Bitmask the conflict sets." (Three integers, each bit = a column / diagonal.)
  - "Print all solutions vs count?" (Same recursion, different aggregator.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/backtracking/n-queens-sudoku.md`
- `<TOPIC_TITLE>` = `N-Queens & Sudoku`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `n-queens-sudoku`

---

### Task 31: `topics/backtracking/grid-search.md`

**Files:** `topics/backtracking/grid-search.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "find a word in a grid" / "all paths in a grid with constraints" / "explore connected region with reversal" — when DFS isn't enough because you need to revisit cells across different paths.
- **Key insight:** DFS over the grid with mutate-restore: temporarily mark cell as visited, recurse to neighbors, unmark on the way out. This shares structure with backtracking-template; pair with a trie when patterns are many (Word Search II).
- **Walkthrough:** Word Search on a 3×3 board for `word = "ABCCED"`. Show the recursion tracing path through cells, with the "mark `#`, recurse, restore original" pattern.
- **Variants to cover:**
  - Single word search (mutate-restore).
  - Word Search II (trie + DFS — prune heavily).
  - Counting paths through every cell (Unique Paths III).
  - Snakes and ladders (BFS instead — contrast).
- **Pitfalls:** off-by-one on grid bounds; failing to restore the cell on the recursion's way out; recursing into the same cell within a single path; not pruning early enough (Word Search II without trie pruning blows up).
- **Complexity:** O(M · N · 4^L) for Word Search (L = word length).
- **LeetCode problems:**
  - [Medium] Word Search (79), Robot Room Cleaner (489 — DFS with rotation state)
  - [Hard] Word Search II (212 — trie + backtracking), Unique Paths III (980)
- **Related patterns:** `../graphs/dfs.md`, `../strings/trie.md`, `backtracking-template.md`, `n-queens-sudoku.md`.
- **Interviewer follow-ups:**
  - "Many words at once." (Trie + DFS; share traversal cost across patterns.)
  - "Forbid revisits across paths." (DP / memo; topology may force this.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/backtracking/grid-search.md`
- `<TOPIC_TITLE>` = `Grid Backtracking`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `grid-backtracking`

---

### Task 32: `topics/math/gcd.md`

**Files:** `topics/math/gcd.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "common factor," "fraction in lowest terms," "lattice problems on integers," "LCM," modular inverse via extended Euclidean.
- **Key insight:** `gcd(a, b) = gcd(b, a mod b)`. Terminates in O(log(min(a, b))) steps. Extended Euclidean additionally returns coefficients `x, y` with `ax + by = gcd(a, b)` — basis for modular inverses.
- **Walkthrough:** trace `gcd(48, 18)`: 48,18 → 18,12 → 12,6 → 6,0 → 6. Then extended on the same.
- **Variants to cover:** classical Euclidean; extended Euclidean; LCM via `a * b // gcd(a, b)`; gcd of arrays (reduce); modular inverse for prime modulus via Fermat (`pow(a, p-2, p)`) or extended Euclidean for general modulus.
- **Pitfalls:** integer overflow in other languages; `gcd(0, 0) = 0` convention; stripping signs.
- **Complexity:** O(log(min(a, b))).
- **LeetCode problems:**
  - [Easy] GCD of Strings (1071), Fraction Addition and Subtraction (592), X of a Kind in a Deck of Cards (914)
  - [Medium] Find Greatest Common Divisor of Array (1979), Smallest Integer Divisible by K (1015), Divisor Game (1025 — math)
  - [Hard] Largest Component Size by Common Factor (952 — UF + factoring), Maximum Number of Tasks You Can Assign (2071 — uses sieve+UF; gcd-adjacent)
- **Related patterns:** `sieve.md`, `fast-exponentiation.md`, `../graphs/union-find.md`.
- **Interviewer follow-ups:**
  - "Modular inverse of 7 mod 13?" (Extended Euclidean or `pow(7, 11, 13)`.)
  - "Why does it terminate?" (Each step at least halves the smaller in the worst case; Fibonacci is the bad case.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/math/gcd.md`
- `<TOPIC_TITLE>` = `GCD`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `gcd`

---

### Task 33: `topics/math/sieve.md`

**Files:** `topics/math/sieve.md`, `templates/sieve.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** "primes up to N," "count primes," prime factorization queries with N up to ~10^7.
- **Key insight:** mark composites by walking multiples of each prime starting from p². Total work is `Σ N/p over primes p ≤ √N` ≈ O(N log log N).
- **Walkthrough:** sieve up to 30. Show the boolean array after processing 2, 3, 5.
- **Variants to cover:** classical sieve; **linear sieve** (each composite hit once via smallest-prime-factor table); segmented sieve (for ranges far from 0); SPF (smallest prime factor) table for O(log n) factorization queries.
- **Pitfalls:** starting inner loop at `2*p` instead of `p²` (correct but slower); off-by-one with `N+1` array length; using sieve for very large N (memory blows up — switch to Miller-Rabin probabilistic test for primality, name-drop).
- **Complexity:** O(N log log N) classical; O(N) linear sieve.
- **LeetCode problems:**
  - [Medium] Count Primes (204), Prime Arrangements (1175), Closest Prime Numbers in Range (2523)
  - [Hard] Largest Component Size by Common Factor (952), Distinct Prime Factors of Product of Array (2521 — factorization via SPF), Prime Subtraction Operation (2601)
- **Related patterns:** `gcd.md`, `fast-exponentiation.md`, `../graphs/union-find.md`.
- **Interviewer follow-ups:**
  - "Primality test for a single huge number?" (Miller-Rabin probabilistic — name-drop.)
  - "Factorize many numbers ≤ 10^6 quickly?" (SPF table from linear sieve.)

**`templates/sieve.py`:** `sieve(n) -> List[int]` (primes up to n), `smallest_prime_factor(n) -> List[int]`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/math/sieve.md`
- `<TOPIC_TITLE>` = `Sieve of Eratosthenes`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = `sieve.py`
- `<TOPIC_SLUG>` (for commit) = `sieve`

---

### Task 34: `topics/math/fast-exponentiation.md`

**Files:** `topics/math/fast-exponentiation.md`, `templates/fast-exponentiation.py`. Modify `RECALL.md`, `README.md`, `templates/README.md`.

**Topic content brief:**
- **Signal:** `pow(x, n)` with huge n, modular exponentiation, matrix exponentiation for linear-recurrence speedups (Fibonacci in O(log n)).
- **Key insight:** `x^n = (x^(n/2))² if n even else x · (x^((n-1)/2))²`. Halve the exponent each step → O(log n) multiplications.
- **Walkthrough:** `2^10` step by step using bottom-up bit decomposition (`10 = 0b1010 → 2^2 · 2^8`).
- **Variants to cover:** integer pow; modular pow (`pow(x, n, mod)` is built into Python); matrix exponentiation for `M^n` to compute linear recurrences in O(k³ log n); fractional exponent — name-drop, not interview material.
- **Pitfalls:** negative exponents (use reciprocal in float; in modular, use modular inverse); overflow in non-modular variants in lower-level languages.
- **Complexity:** O(log n) multiplications.
- **LeetCode problems:**
  - [Medium] Pow(x, n) (50), Super Pow (372), Count Good Numbers (1922)
  - [Hard] Knight Dialer (935 — matrix exp variant; DP also works), N-th Tribonacci Number (1137 — small enough that linear DP suffices, matrix exp pads the lecture)
- **Related patterns:** `gcd.md`, `sieve.md`, `../dp/1d-dp.md` (linear recurrences are also DP).
- **Interviewer follow-ups:**
  - "Matrix exponentiation for Fibonacci." (`[[1,1],[1,0]]^n`.)
  - "Modular exponentiation under a non-prime mod?" (Same algorithm; caveat for inverses.)

**`templates/fast-exponentiation.py`:** `pow_int(x, n)`, `pow_mod(x, n, mod)`, `mat_pow(M, n, mod=None)`.

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/math/fast-exponentiation.md`
- `<TOPIC_TITLE>` = `Fast Exponentiation`
- `<TIER_STARS>` = `★★`
- `<TEMPLATE_FILE>` = `fast-exponentiation.py`
- `<TOPIC_SLUG>` (for commit) = `fast-exponentiation`

---

## Phase 5: Nice-to-Have Tier (8 topics)

Same per-topic workflow. Files in `topics/nice-to-have/`. Tier mark `★` in README. Coverage is full 9-section but can be terser than higher tiers.

### Task 35: `topics/nice-to-have/a-star.md`

**Files:** `topics/nice-to-have/a-star.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** large state-space shortest path where Dijkstra is too slow but a good heuristic exists; pathfinding in grids; sliding puzzles.
- **Key insight:** Dijkstra prioritizes nodes by `g(n)` (cost so far). A* prioritizes by `g(n) + h(n)` where `h` is an admissible (never-overestimates) heuristic. With a consistent heuristic, A* expands nodes in order of true distance — provably optimal and usually much faster.
- **Walkthrough:** 8-puzzle with Manhattan-distance heuristic — sketch why it dominates BFS.
- **Variants:** uniform-cost search (= Dijkstra, h ≡ 0); IDA* (memory-bounded, name-drop).
- **Pitfalls:** inadmissible heuristic → suboptimal answer; inconsistent (admissible but not monotonic) heuristic + closed-set short-circuit → suboptimal.
- **Complexity:** depends on heuristic quality; pathologically O((V + E) log V) like Dijkstra.
- **LeetCode problems:**
  - [Medium] Shortest Path in Binary Matrix (1091 — A* with diagonal Chebyshev gives a small win)
  - [Hard] Sliding Puzzle (773 — A* shines), Race Car (818)
- **Related patterns:** `../graphs/shortest-paths.md`, `../graphs/bfs.md`.
- **Interviewer follow-ups:**
  - "What's an admissible heuristic for grid Manhattan distance?" (Manhattan distance itself.)
  - "Why does consistency matter?" (Closed-set short-circuiting becomes correct.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/a-star.md`
- `<TOPIC_TITLE>` = `A* Search`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `a-star`

---

### Task 36: `topics/nice-to-have/mst.md`

**Files:** `topics/nice-to-have/mst.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "minimum cost to connect all," weighted graph spanning tree; "connect all cities."
- **Key insight:** two textbook algorithms.
  - **Kruskal**: sort edges by weight; add if it doesn't create a cycle (union-find detects). O(E log E).
  - **Prim**: grow a tree from a root; at each step, add the minimum-weight edge crossing the cut. O((V + E) log V) with a heap.
- **Walkthrough:** small graph, both algorithms side-by-side.
- **Variants:** Borůvka (parallel-friendly — name-drop); MST with one mandatory edge.
- **Pitfalls:** Kruskal needs sorted edges; Prim needs a way to track current min edge per non-tree node.
- **Complexity:** as above; both are essentially O(E log V).
- **LeetCode problems:**
  - [Medium] Connecting Cities With Minimum Cost (1135), Min Cost to Connect All Points (1584)
  - [Hard] Optimize Water Distribution in a Village (1168), Minimum Cost to Make at Least One Valid Path in a Grid (1368)
- **Related patterns:** `../graphs/union-find.md` (Kruskal uses it), `../graphs/shortest-paths.md` (different problem — single-source shortest path).
- **Interviewer follow-ups:**
  - "Pick Kruskal or Prim for a dense graph?" (Prim with adjacency matrix is O(V²), often beats Kruskal's `E log E ≈ V² log V`.)
  - "Multiple connected components?" (Kruskal yields a min spanning forest.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/mst.md`
- `<TOPIC_TITLE>` = `Minimum Spanning Tree`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `mst`

---

### Task 37: `topics/nice-to-have/max-flow.md`

**Files:** `topics/nice-to-have/max-flow.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "maximum bipartite matching," "maximum throughput in a network," min-cut equivalence problems. Rare in interviews.
- **Key insight:** Ford-Fulkerson — repeatedly find augmenting paths (BFS for the polynomial Edmonds-Karp variant) and push flow. Max-flow = min-cut by duality.
- **Walkthrough:** small bipartite graph; reduction to flow (super-source, super-sink); one or two augmenting paths.
- **Variants:** Edmonds-Karp (O(VE²)); Dinic's (O(V²E), level-graph + blocking flow); push-relabel — name-drop only.
- **Pitfalls:** forgetting reverse edges in residual graph; non-integer capacities (rational only).
- **Complexity:** Edmonds-Karp O(VE²).
- **LeetCode problems:**
  - [Hard] Maximum Students Taking Exam (1349 — bipartite matching dressed up; bitmask DP also works), Swim in Rising Water (778 — alternative)
- **Related patterns:** `../graphs/bfs.md`, `../graphs/shortest-paths.md`.
- **Interviewer follow-ups:**
  - "Reduce bipartite matching to max-flow." (Source → left nodes (cap 1), left → right (cap 1), right → sink (cap 1).)
  - "Min-cut from max-flow." (BFS in residual graph from source; cut between reachable and unreachable.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/max-flow.md`
- `<TOPIC_TITLE>` = `Max Flow / Min Cut`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `max-flow`

---

### Task 38: `topics/nice-to-have/reservoir-sampling.md`

**Files:** `topics/nice-to-have/reservoir-sampling.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "uniform random sample from a stream of unknown size"; "pick k random items without storing all."
- **Key insight:** for k=1: keep first element; on the i-th element (1-indexed), replace with probability `1/i`. Probability each element ends up chosen = `1/n`. For general k: keep first k; on i-th (i > k), replace a random reservoir slot with probability `k/i`.
- **Walkthrough:** prove by induction for k=1; show that probability after n elements is exactly `1/n`.
- **Variants:** weighted reservoir sampling (Algorithm A-Res, exponential keys); distributed reservoirs.
- **Pitfalls:** off-by-one (1-indexed assumption); calling a non-uniform RNG.
- **Complexity:** O(n) time, O(k) space.
- **LeetCode problems:**
  - [Medium] Linked List Random Node (382), Random Pick Index (398), Insert Delete GetRandom O(1) — Duplicates allowed (381)
  - [Hard] (rare)
- **Related patterns:** `../two-pointers-sliding-window/sliding-window.md` (different streaming pattern).
- **Interviewer follow-ups:**
  - "Prove correctness." (Induction.)
  - "Weighted version." (Sketch A-Res.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/reservoir-sampling.md`
- `<TOPIC_TITLE>` = `Reservoir Sampling`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `reservoir-sampling`

---

### Task 39: `topics/nice-to-have/manacher.md`

**Files:** `topics/nice-to-have/manacher.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** longest palindromic substring in O(n); count palindromic substrings; tighter bounds than expand-around-center.
- **Key insight:** maintain a "current rightmost palindrome" with center `c` and right boundary `r`. The palindrome radius at position `i` can be initialized using mirror position `2c - i` if `i < r` — saves redundant character comparisons. Total work O(n).
- **Walkthrough:** trace on `s = "abacabad"`. Insert separators (`#a#b#a#c#a#b#a#d#`) to unify even/odd lengths.
- **Variants:** classic Manacher; expand-around-center (O(n²) but simpler — usually accepted in interviews).
- **Pitfalls:** the separator trick; off-by-one when extracting the substring at the end.
- **Complexity:** O(n) Manacher; O(n²) expand-around-center.
- **LeetCode problems:**
  - [Medium] Longest Palindromic Substring (5 — usually expand-around-center suffices), Palindromic Substrings (647)
  - [Hard] Shortest Palindrome (214 — KMP or Manacher), Palindrome Pairs (336)
- **Related patterns:** `../strings/kmp.md`, `../dp/interval-dp.md`.
- **Interviewer follow-ups:**
  - "Why does Manacher beat expand-around-center?" (Reuses overlapping work; O(n) vs O(n²).)
  - "If Manacher is asked, can you sketch it?" (At minimum the separator trick + center/right bookkeeping.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/manacher.md`
- `<TOPIC_TITLE>` = `Manacher's Algorithm`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `manacher`

---

### Task 40: `topics/nice-to-have/z-algorithm.md`

**Files:** `topics/nice-to-have/z-algorithm.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** longest match between a prefix of `s` and a substring at each position; alternative to KMP for string matching.
- **Key insight:** the Z-array `Z[i]` is the length of the longest substring starting at `i` that matches a prefix of `s`. Build it in O(n) using a sliding `(l, r)` window of the rightmost match.
- **Walkthrough:** build Z-array for `s = "aabaab"`. Use Z to search pattern in text via `pattern + '$' + text`.
- **Variants:** Z-array for matching; suffix array (alternative, more powerful — name-drop).
- **Pitfalls:** the sentinel character `$` must not appear in either string; off-by-one in window updates.
- **Complexity:** O(n) build.
- **LeetCode problems:**
  - [Medium] Find the Index of the First Occurrence in a String (28 — KMP/Z alternatives)
  - [Hard] Longest Happy Prefix (1392), Sum of Scores of Built Strings (2223)
- **Related patterns:** `../strings/kmp.md`, `../strings/rabin-karp.md`.
- **Interviewer follow-ups:**
  - "Z vs KMP — when use which?" (Z is often easier to think about; KMP uses less auxiliary string. Either works for matching.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/z-algorithm.md`
- `<TOPIC_TITLE>` = `Z-Algorithm`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `z-algorithm`

---

### Task 41: `topics/nice-to-have/tarjan-kosaraju.md`

**Files:** `topics/nice-to-have/tarjan-kosaraju.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** strongly connected components in a directed graph; bridges and articulation points; "find critical connections."
- **Key insight:**
  - **Kosaraju**: two DFS passes — first on original graph push to stack on finish; second on transposed graph in reverse-finish order. Each DFS tree in the second pass = one SCC.
  - **Tarjan**: single DFS using `disc[v]` and `low[v]` (lowest disc reachable via tree + at-most-one back edge); SCC = stack frames between the moment a node is pushed and the moment its low-link equals its own disc.
  - **Bridges**: same low-link machinery, predicate `low[child] > disc[node]`.
- **Walkthrough:** small graph with 2 SCCs. Trace Kosaraju.
- **Pitfalls:** Tarjan's stack invariant easy to break; iterative versions are gnarly (Python recursion limits matter).
- **Complexity:** O(V + E).
- **LeetCode problems:**
  - [Hard] Critical Connections in a Network (1192 — Tarjan bridges), Critical and Pseudo-Critical Edges in MST (1489 — different but graph theory adjacent), Course Schedule IV (1462 — transitive closure on DAG; SCC-related)
- **Related patterns:** `../graphs/dfs.md`, `../graphs/topological-sort.md`.
- **Interviewer follow-ups:**
  - "Why does Kosaraju's reverse-finish-order trick work?" (The first DFS finish order forms a topological order on the SCC-DAG; transposed second pass peels SCCs from the top.)
  - "Articulation points vs bridges?" (Both via low-link; different predicates.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/tarjan-kosaraju.md`
- `<TOPIC_TITLE>` = `Tarjan's & Kosaraju's (SCC)`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `tarjan-kosaraju`

---

### Task 42: `topics/nice-to-have/boyer-moore.md`

**Files:** `topics/nice-to-have/boyer-moore.md`. Modify `RECALL.md`, `README.md`.

**Topic content brief:**
- **Signal:** "majority element appears > n/2 (or > n/3) times" with O(1) extra space; voting-style aggregation.
- **Key insight:** maintain a candidate and a counter. On each element: if counter is 0, replace candidate; if equal, increment; else decrement. After one pass, candidate is the only viable majority. (For > n/3, two candidates are tracked.)
- **Walkthrough:** majority on `[2, 2, 1, 1, 1, 2, 2]`. Trace the candidate/count evolution.
- **Variants:** classic majority (>n/2); generalized to >n/k with k-1 candidates; Boyer-Moore string search (different! — note the clash and that the *string* version is rarely asked because KMP/Z-function dominate. Discuss bad-character heuristic only briefly.).
- **Pitfalls:** the generalized version requires a final verification pass — without it, you can produce false positives when no element actually exceeds n/k.
- **Complexity:** O(n) time, O(1) space.
- **LeetCode problems:**
  - [Easy] Majority Element (169)
  - [Medium] Majority Element II (229)
- **Related patterns:** `../strings/kmp.md`, `../two-pointers-sliding-window/two-pointers.md`.
- **Interviewer follow-ups:**
  - "Why does the majority-vote algorithm work?" (Pair off votes — every disagreement cancels one of each; majority survives.)
  - "Generalize to >n/k." (Track k-1 candidates; verify at the end.)

**Apply checklist with:**

- `<TOPIC_FILE>` = `topics/nice-to-have/boyer-moore.md`
- `<TOPIC_TITLE>` = `Boyer-Moore Majority Vote`
- `<TIER_STARS>` = `★`
- `<TEMPLATE_FILE>` = (none — skip Step 6)
- `<TOPIC_SLUG>` (for commit) = `boyer-moore`

---

## Phase 6: Polish

### Task 43: Cross-link audit

**Files:** every topic file (read-only first), then targeted edits.

**Goal:** every "Related patterns" section has working links. Where a topic A links to topic B as related, B should usually link back to A — verify and add if missing.

- [ ] **Step 1: Run the verifier on the whole repo**

```bash
python scripts/verify.py
```

Expected: `OK (39 file(s) verified)`. If anything fails (broken link, missing section, bad python block), fix it and re-run.

- [ ] **Step 2: Build the cross-link graph**

```bash
python -c "
import re, pathlib
ROOT = pathlib.Path('topics')
graph = {}
for p in ROOT.rglob('*.md'):
    if p.name.startswith('_'): continue
    text = p.read_text()
    section = re.search(r'## 8\. Related patterns(.*?)(\n## |\Z)', text, re.DOTALL)
    body = section.group(1) if section else ''
    targets = re.findall(r'\]\(([^)]+\.md)[^)]*\)', body)
    graph[p] = targets
for p, ts in graph.items():
    print(f'{p}:')
    for t in ts:
        target = (p.parent / t).resolve()
        marker = 'OK' if target.exists() else 'BROKEN'
        print(f'  -> {target.relative_to(pathlib.Path.cwd())} [{marker}]')
"
```

Expected: every line shows `[OK]`. If `[BROKEN]` appears, fix the path in the source file.

- [ ] **Step 3: Find one-way links and decide which need to be made bidirectional**

```bash
python -c "
import re, pathlib
ROOT = pathlib.Path('topics')
links = {}
for p in ROOT.rglob('*.md'):
    if p.name.startswith('_'): continue
    text = p.read_text()
    section = re.search(r'## 8\. Related patterns(.*?)(\n## |\Z)', text, re.DOTALL)
    body = section.group(1) if section else ''
    links[p.resolve()] = {(p.parent / t).resolve() for t in re.findall(r'\]\(([^)]+\.md)[^)]*\)', body)}
for src, targets in links.items():
    for tgt in targets:
        if src not in links.get(tgt, set()):
            print(f'one-way: {src.relative_to(pathlib.Path.cwd())}  ->  {tgt.relative_to(pathlib.Path.cwd())}')
"
```

Review the output. Add reciprocal links wherever the relationship is genuinely bidirectional (most are). Skip one-way links where the relationship is hierarchical (e.g., a nice-to-have pointing back at its must-know foundation; the must-know doesn't need to point at every nice-to-have descendant).

- [ ] **Step 4: Final verify**

```bash
python scripts/verify.py
```

Expected: `OK (39 file(s) verified)`.

- [ ] **Step 5: Commit**

```bash
git add topics/
git commit -m "docs: cross-link audit and reciprocal-link fixes"
```

---

### Task 44: Final README pass and study order finalization

**Files:** `README.md`, possibly `RECALL.md` (renumbering).

**Goal:** the README's `Study order` section is the canonical learning path. Order topics by tier (★★★ → ★★ → ★) and within tier, by the prerequisite-aware order from spec section 9.

- [ ] **Step 1: Replace the appended-as-you-go study order with the canonical order**

In `README.md`, replace the contents under `## Study order` with this exact list:

```markdown
**★★★ Must-know cold**

1. [Binary Search](topics/searching-sorting/binary-search.md)
2. [Quicksort & Mergesort](topics/searching-sorting/quicksort-mergesort.md)
3. [Heapsort & Heaps](topics/searching-sorting/heapsort.md)
4. [Two Pointers](topics/two-pointers-sliding-window/two-pointers.md)
5. [Fast/Slow Pointers](topics/two-pointers-sliding-window/fast-slow-pointers.md)
6. [Sliding Window](topics/two-pointers-sliding-window/sliding-window.md)
7. [BFS](topics/graphs/bfs.md)
8. [DFS](topics/graphs/dfs.md)
9. [Topological Sort](topics/graphs/topological-sort.md)
10. [Union-Find](topics/graphs/union-find.md)
11. [Shortest Paths (Dijkstra)](topics/graphs/shortest-paths.md)
12. [1D DP](topics/dp/1d-dp.md)
13. [2D DP](topics/dp/2d-dp.md)
14. [Interval DP](topics/dp/interval-dp.md)
15. [Tree DP](topics/dp/tree-dp.md)
16. [Bitmask DP](topics/dp/bitmask-dp.md)

**★★ Strongly recommended**

17. [KMP](topics/strings/kmp.md)
18. [Rabin-Karp](topics/strings/rabin-karp.md)
19. [Trie](topics/strings/trie.md)
20. [Tree Traversals](topics/trees/traversals.md)
21. [Binary Search Tree](topics/trees/bst.md)
22. [Lowest Common Ancestor](topics/trees/lca.md)
23. [Segment Tree & Fenwick](topics/trees/segment-tree-fenwick.md)
24. [Interval Scheduling](topics/greedy/interval-scheduling.md)
25. [Activity Selection (and Huffman name-drop)](topics/greedy/activity-selection.md)
26. [Backtracking Template](topics/backtracking/backtracking-template.md)
27. [N-Queens & Sudoku](topics/backtracking/n-queens-sudoku.md)
28. [Grid Backtracking](topics/backtracking/grid-search.md)
29. [GCD](topics/math/gcd.md)
30. [Sieve of Eratosthenes](topics/math/sieve.md)
31. [Fast Exponentiation](topics/math/fast-exponentiation.md)

**★ Nice to have**

32. [A* Search](topics/nice-to-have/a-star.md)
33. [Minimum Spanning Tree](topics/nice-to-have/mst.md)
34. [Max Flow / Min Cut](topics/nice-to-have/max-flow.md)
35. [Reservoir Sampling](topics/nice-to-have/reservoir-sampling.md)
36. [Manacher's Algorithm](topics/nice-to-have/manacher.md)
37. [Z-Algorithm](topics/nice-to-have/z-algorithm.md)
38. [Tarjan's & Kosaraju's (SCC)](topics/nice-to-have/tarjan-kosaraju.md)
39. [Boyer-Moore Majority Vote](topics/nice-to-have/boyer-moore.md)
```

- [ ] **Step 2: Reorder `RECALL.md` sections to match**

Reorder `RECALL.md`'s sections so they appear in the same order as the README study order. The section content is unchanged — only ordering moves.

- [ ] **Step 3: Verify everything**

```bash
python scripts/verify.py
python -m pytest scripts/test_verify.py -v
```

Expected: `OK (39 file(s) verified)` and four passing tests.

- [ ] **Step 4: Open the README and skim**

Manually open `README.md` and confirm:
- Tier legend renders correctly.
- All 39 study-order entries are clickable.
- Links to RECALL.md and templates/README.md work.
- "How to use" section reads well.

- [ ] **Step 5: Commit**

```bash
git add README.md RECALL.md
git commit -m "docs: finalize study order and README"
```

---

## Plan Self-Review (informal — done by author before saving)

**Spec coverage check:**
- Spec §1 Purpose → covered by Phases 2–5 producing the topic files; README/RECALL/templates split addressed.
- Spec §2 Non-goals → respected; no calendar, no CLI, no solutions, no system design.
- Spec §3 Repo structure → Task 1 builds it.
- Spec §4 Per-topic file structure → Task 3 codifies it as `_TEMPLATE.md`; Task 2 enforces it via `verify.py`.
- Spec §5 RECALL.md format → workflow conventions specify "TL;DR + Template only," reinforced in Task 4 step 5.
- Spec §6 README.md format → Task 3 skeleton + Task 44 finalization.
- Spec §7 Coverage → 39 topic-file tasks, exactly matching the per-tier counts.
- Spec §8 Quality bar → enforced by `verify.py` (sections, python parse, links). Concrete walkthroughs and hand-picked LeetCode problems are in every Topic content brief.
- Spec §9 Implementation plan hooks → Phases 2–5 follow the specified build order; Task 43 is the cross-link audit hook.
- Spec §10 Open questions → not in scope, deferred (no tasks).

**Placeholder scan:** every per-topic task has a concrete content brief — signals, walkthroughs, problems, follow-ups all named. No "TBD" / "fill in later" / "similar to Task N." Workflow steps are short because the workflow is shared, but each task lists which files it modifies.

**Type/name consistency:** the verify-script function names match across Tasks 2's tests and Task 2's implementation. The template paths mentioned in per-topic tasks all match the spec §3 list (16 templates).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-27-leetcode-prep.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Good fit because tasks 5–42 are highly parallel and each is self-contained.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
