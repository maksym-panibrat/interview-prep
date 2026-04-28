# LeetCode Interview Prep — Reference Material Design

**Date:** 2026-04-27
**Status:** Approved
**Author:** maksym@panibrat.com (with Claude)

## 1. Purpose

Build a long-term, high-quality Python algorithm reference for LeetCode-style interview preparation. The repository serves two reading modes:

1. **Deep learning** — full topic files with explanations, walkthroughs, and curated problem sets used while initially studying a pattern.
2. **Fast re-skim** — a consolidated `RECALL.md` and a code-only `templates/` folder used in the days/hours before an interview.

Solutions are practiced on LeetCode itself; this repository is the study guide and pattern reference, not a solutions archive.

## 2. Non-Goals

- A dated study calendar or daily plan. The user has no fixed deadline; pacing is self-directed.
- A CLI, quiz tool, or any custom tooling. Plain markdown only.
- Storing user solutions to LeetCode problems. The repo lists problems and links them; the user solves on leetcode.com.
- System design, behavioral interview prep, language tutorials, or any non-algorithm content.

## 3. Top-Level Repository Structure

```
interview-prep/
  README.md                          # index, study-order suggestion, tier legend
  RECALL.md                          # consolidated 30-second cards across all topics
  topics/
    searching-sorting/
      binary-search.md
      quicksort-mergesort.md
      heapsort.md
    two-pointers-sliding-window/
      two-pointers.md
      fast-slow-pointers.md
      sliding-window.md
    graphs/
      bfs.md
      dfs.md
      topological-sort.md
      union-find.md
      shortest-paths.md               # Dijkstra primary; Bellman-Ford / Floyd-Warshall name-drop
    dp/
      1d-dp.md
      2d-dp.md
      interval-dp.md
      tree-dp.md
      bitmask-dp.md
    strings/
      kmp.md
      rabin-karp.md
      trie.md
    trees/
      traversals.md
      bst.md
      lca.md
      segment-tree-fenwick.md
    greedy/
      interval-scheduling.md
      activity-selection.md           # Huffman name-drop included here
    backtracking/
      backtracking-template.md
      n-queens-sudoku.md
      grid-search.md
    math/
      gcd.md
      sieve.md
      fast-exponentiation.md
    nice-to-have/
      a-star.md
      mst.md
      max-flow.md                     # Ford-Fulkerson name-drop
      reservoir-sampling.md
      manacher.md
      z-algorithm.md
      tarjan-kosaraju.md
      boyer-moore.md
  templates/
    README.md                         # snippet library index
    binary-search.py
    union-find.py
    dijkstra.py
    topological-sort.py
    bfs.py
    dfs.py
    sliding-window.py
    two-pointers.py
    backtracking.py
    trie.py
    kmp.py
    segment-tree.py
    fenwick-tree.py
    heap.py
    fast-exponentiation.py
    sieve.py
```

The `templates/` folder is a deliberate duplicate of the implementation snippets from `topics/`, but stripped of all exposition. It's the file you copy-paste from in the last hour before the interview when you don't want to read prose.

## 4. Per-Topic File Structure

Every file under `topics/<category>/` follows this 9-section structure, in this order:

### 1. TL;DR
2–3 sentences: what the algorithm/pattern is, the **signal** that tells you to reach for it in a problem statement, and headline time/space complexity.

### 2. Intuition
Mental model in plain English. Why does this approach work? What's the key insight that makes it correct? Use an analogy where it clarifies (e.g., union-find as "groups of friends merging").

### 3. Walkthrough
A small concrete example with real values, traced step-by-step. Where useful, include ASCII state diagrams showing how the data structure evolves (pointer positions, queue contents, dp-table cells filling in, parent-array updates).

### 4. Implementation
Clean, runnable Python code with comments on the non-obvious lines. At the bottom of this section, a **Template** sub-block: the bare-bones boilerplate you'd reach for in any problem of this shape, no problem-specific logic.

### 5. Variants & pitfalls
Common mutations of the algorithm (e.g., binary search: leftmost vs rightmost insert vs search-on-answer-space; sliding window: fixed vs variable size). Off-by-one traps, boundary conditions, and the classic mistakes interviewers love to probe. Anti-patterns are folded in here — i.e., "people often try X; here's why it fails."

### 6. Complexity
Time and space, each with a one-sentence justification. Note any non-obvious factors (e.g., "amortized α(n) for union-find with path compression + union by rank").

### 7. Problem set
Curated LeetCode problems, ordered easy → medium → hard. Each entry contains:
- Problem name + direct `https://leetcode.com/problems/<slug>/` link
- One-line explanation of **what makes this problem instructive** for the pattern
- Difficulty stamp `[Easy] / [Medium] / [Hard]`

Target ~5–10 problems per topic. Hand-picked, not auto-generated.

### 8. Related patterns
Markdown links to neighbor topic files. E.g., `bfs.md` links to `topological-sort.md`, `shortest-paths.md`, and `dfs.md`.

### 9. Interviewer follow-ups
Typical "now what if..." questions an interviewer asks after you solve the base problem, and how to handle each. E.g., for binary search: "what if the array has duplicates?", "what if it's rotated?", "what if you can't load it into memory?". Each follow-up gets a short answer (a few sentences or a code sketch).

## 5. RECALL.md Format

Single file. One section per topic, in study order (must-know → strongly-recommended → nice-to-have, mirroring the README index).

Each section contains exactly:
- Topic name as an `H2` heading, linked to its full topic file.
- The topic's TL;DR (copied verbatim from section 1 of the topic file).
- The **Template** code block (copied verbatim from section 4 of the topic file).

No walkthroughs, no problem lists, no prose. RECALL.md is the "30 minutes before the interview" file: signals + templates + nothing else.

## 6. README.md Format

The repository index. Contains:
- One-paragraph repo purpose.
- A **legend** explaining the three tiers (must-know cold / strongly recommended / nice-to-have).
- A **suggested study order**: a flat numbered list of all topic files in the order to read them, with each entry tagged by tier.
- A pointer to `RECALL.md` and `templates/`.
- A short "How to use this repo" section (study a topic file → solve its problem set on LeetCode → re-read RECALL.md before interviews).

## 7. Coverage

Full coverage of every category in the source list, no skips:

| Tier | Categories | Count |
| --- | --- | --- |
| Must-know cold | Searching/sorting (3), Two-pointers/sliding-window (3), Graph traversal (5), DP patterns (5) | 16 files |
| Strongly recommended | Strings (3), Trees (4), Greedy (2), Backtracking (3), Math (3) | 15 files |
| Nice to have | A*, MST, Max flow, Reservoir sampling, Manacher, Z-algorithm, Tarjan/Kosaraju, Boyer-Moore | 8 files |

Total: 39 topic files plus README, RECALL, and the templates folder.

Items the source list flags as "name-drop only" (Bellman-Ford, Floyd-Warshall, Huffman, Ford-Fulkerson) get a short subsection inside the relevant primary file rather than their own file. They are mentioned, complexity stated, when-to-use noted, but not given the full 9-section treatment.

## 8. Quality Bar

Every file in this repository must satisfy:

- **Runnable code.** Every implementation snippet is valid Python 3 and runs as-is. Where useful, files include an `if __name__ == "__main__":` smoke test demonstrating the function on a small input.
- **Concrete walkthroughs.** Walkthroughs use real values (e.g., `nums = [1, 3, 5, 6]`, `target = 5`), not abstract `i`/`j`/`k` only.
- **Real LeetCode links.** Every problem in a problem set is hand-picked, has a working `https://leetcode.com/problems/<slug>/` link, and a non-trivial reason it was chosen.
- **No broken cross-links.** Every markdown link to another topic file resolves. RECALL.md links back to topic files; topic files link to siblings via "Related patterns."
- **Consistent voice.** Reference-style prose: direct, terse, no filler. Reads the same across all files.

## 9. Implementation Plan Hooks

The implementation plan (next document, produced by `superpowers:writing-plans`) should treat this as the build order:

1. **Scaffolding** — directory structure, README skeleton, RECALL.md skeleton, templates/ folder with empty README, a per-topic file template (the 9-section skeleton) for reuse.
2. **Must-know tier first** — fill in topic files in the order: binary search → quicksort/mergesort → heapsort → two pointers → fast/slow pointers → sliding window → BFS → DFS → topological sort → union-find → shortest paths (Dijkstra primary) → 1D DP → 2D DP → interval DP → tree DP → bitmask DP. RECALL.md and `templates/` updated incrementally as each topic completes.
3. **Strongly-recommended tier second** — KMP, Rabin-Karp, trie, tree traversals, BST, LCA, segment/Fenwick tree, interval scheduling, activity selection, backtracking template, N-Queens/Sudoku, grid search, GCD, sieve, fast exponentiation.
4. **Nice-to-have tier last** — the 8 nice-to-have files, kept shorter than the other tiers but still 9-section.
5. **Cross-link audit** — final pass over every "Related patterns" section to verify links resolve and are bidirectional where it makes sense.

Each topic file is independently sized — the implementation plan can parallelize topic files across agents/sessions if desired.

## 10. Open Questions / Future Work

- Whether to add a per-problem "expected difficulty for me" tag (would require user calibration; defer until repo is in active use).
- Whether to add a "common interviewer companies" tag per problem (Google / Meta / Amazon historical frequency) — useful but data sources go stale fast; defer.
- Whether to add a `solutions/` folder later if the user changes their mind about committing personal solutions. Currently out of scope per Section 2.
