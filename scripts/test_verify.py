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
    assert "OK" in result.stdout


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


SYSTEM_DESIGN_VALID_MD = textwrap.dedent("""\
    # Title
    ## 1. TL;DR
    x
    ## 2. How it works
    x
    ## 3. When to use
    x
    ## 4. Trade-offs and failure modes
    x
    ## 5. Real-world and interviewer probes
    x
    """)


def _run_path(path):
    result = subprocess.run(
        [sys.executable, "scripts/verify.py", str(path)],
        capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1],
    )
    return result


def test_system_design_passes_with_5_sections(tmp_path):
    sd_dir = tmp_path / "topics" / "system-design"
    sd_dir.mkdir(parents=True)
    f = sd_dir / "sample.md"
    f.write_text(SYSTEM_DESIGN_VALID_MD)
    result = _run_path(f)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_system_design_fails_when_section_missing(tmp_path):
    sd_dir = tmp_path / "topics" / "system-design"
    sd_dir.mkdir(parents=True)
    f = sd_dir / "sample.md"
    f.write_text("# Title\n## 1. TL;DR\nx\n")
    result = _run_path(f)
    assert result.returncode != 0
    assert "How it works" in result.stdout


def test_algorithm_schema_fails_for_system_design_sections(tmp_path):
    """A file outside topics/system-design/ must still need 9-section schema."""
    other_dir = tmp_path / "topics" / "graphs"
    other_dir.mkdir(parents=True)
    f = other_dir / "sample.md"
    f.write_text(SYSTEM_DESIGN_VALID_MD)
    result = _run_path(f)
    assert result.returncode != 0
    assert "Intuition" in result.stdout
