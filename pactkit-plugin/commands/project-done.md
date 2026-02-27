---
description: "Code cleanup, Board update, Git commit"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Done (v1.3.0 Smart Gatekeeper)
- **Usage**: `/project-done`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block.
1.  **Audit**: Are tests passing? Is the Board updated?
2.  **Semantics**: Determine correct Conventional Commit scope.

## 🎬 Phase 1: Context Loading
1.  **Read Spec**: Read `docs/specs/{ID}.md`.
2.  **Read Board**: Read `docs/product/sprint_board.md`.

## 🎬 Phase 2: Housekeeping (Deep Clean)
1.  **Action**: Remove language-specific temp artifacts (see `LANG_PROFILES` cleanup list; default for Python):
    - `rm -rf __pycache__ .pytest_cache`
    - `rm -f .DS_Store *.tmp *.log`
2.  **Update Reality (Lazy Visualize)**:
    - Check if `docs/architecture/graphs/code_graph.mmd` exists AND `git diff --name-only` includes any files in `LANG_PROFILES[stack].source_dirs`.
    - **If source files changed OR graph missing**: Run all three visualize commands:
        - `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize`
        - `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`
        - `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize --mode call`
    - **If no source files changed AND graph exists**: Skip with log: `"Graph up-to-date — no source changes"`
3.  **HLD Consistency Check**: Read `docs/architecture/graphs/system_design.mmd` and verify component counts match reality:
    - Compare any numeric labels in subgraphs (e.g., "8 commands", "9 skills") against the actual component counts from `config.py` VALID_* registries or the project source.
    - If a mismatch is found, **warn** the user: "⚠️ system_design.mmd is stale: says {old} but actual is {new}. Update the HLD."
    - If the user agrees, update the mismatch in `system_design.mmd`.
    - If `system_design.mmd` does not exist, skip silently.

## 🎬 Phase 2.5: Regression Gate (MANDATORY)
> **CRITICAL**: Do NOT skip this step. This is the safety net before commit.

### Step 1: Impact Analysis
- Run `git diff --name-only HEAD~1` (or vs. branch base) to list all changed files.
- Check if `docs/architecture/graphs/code_graph.mmd` exists.

### Step 1.3: Doc-Only Shortcut
> **PURPOSE**: If no source files were changed, skip or minimize regression — running 1000+ tests for a README edit wastes time.

1. **Classify changed files**: From the `git diff` and `git status` output (Step 1), identify which files are **source files** vs **non-source files**:
   - **Source files**: Files matching `LANG_PROFILES[stack].file_ext` (e.g., `.py`) whose path starts with any directory in `LANG_PROFILES[stack].source_dirs` (e.g., `src/` for Python).
   - **Non-source files**: Everything else — `.md`, `.yml`, `.yaml`, `.json`, `.mmd`, `docs/`, `.github/`, `tests/`, config files, specs, board files.
2. **Decision**:
   - If **zero source files** changed AND **no test files** were added/modified:
     - Log: `"Regression: SKIP — doc-only change, no source files modified"`
     - Skip regression entirely. Proceed directly to Step 2.7 (Lint Gate).
   - If **zero source files** changed BUT **new test files** exist (e.g., `tests/unit/test_story*.py` created in this Story):
     - Log: `"Regression: STORY-ONLY — {N} new test files, no source changes"`
     - Run ONLY those new test files (they were already validated in Act Phase 3 TDD loop, but re-confirm here).
     - Skip the full suite. Proceed to Step 2.7.
   - If **any source files** changed: Continue to Step 1.5 (normal flow).

### Step 1.5: Fast-Suite Shortcut
> If the last test run completed in **< 30 seconds** (check pytest output or prior run time), skip the decision tree and always run **full regression** — the suite is fast enough that optimizing for incremental provides no benefit. Proceed directly to Step 3.

### Step 1.6: Release Gate — Version Bump Override (R5)
> **PURPOSE**: Release commits require a full suite to ensure no regressions are hidden.
1. Run `git diff HEAD~1 pyproject.toml | grep version` (or vs. branch base).
2. If a version change is detected (e.g., `1.4.0` → `1.4.1`):
   - Log: `"Regression: FULL — version bump detected, release requires full test suite"`
   - Skip impact analysis. Proceed directly to Step 3 (full regression).
3. If no version change: continue to Step 1.7.

### Step 1.7: Impact-Based Analysis (STORY-053)
> **PURPOSE**: Use `call_graph.mmd` to target only tests affected by changed functions.

1. **Preconditions**: All of the following must be true to attempt impact analysis:
   - `docs/architecture/graphs/call_graph.mmd` exists.
   - `regression.strategy` is `impact` (read from `pactkit.yaml`; default: `impact`).
2. **Identify changed functions**: Use `git diff HEAD~1 --unified=0` on changed source files to extract modified function names (look for `def ` in the diff).
3. **Run impact command** for each changed function:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py impact --entry <func_name>
   ```
   Collect all returned test file paths (space-separated).
4. **Deduplicate** the collected test paths.
5. **Decision** (threshold from `regression.max_impact_tests`, default 50):
   - If total impacted files < threshold: run only impacted test files.
     - Log: `"Regression: IMPACT-BASED — {N} test files based on call graph analysis"`
     - Run: `pytest {space-separated test paths}`
     - Skip Step 2. Proceed to Step 2.3 for logging.
   - If impacted files ≥ threshold or impact command fails: fall through to Step 2 (Decision Tree).
   - If no changed functions found in diff: fall through to Step 2.

### Step 2: Decision Tree (Safe-by-Default)
> **DEFAULT**: Run **full regression** (`pytest tests/`). This is the safe default.

Run **incremental tests** only if ALL of the following conditions are true:
- `code_graph.mmd` exists AND appears in `git diff HEAD~1 --name-only` or `git status --short` (i.e., the graph was recently updated, not stale)
- Changed source files ≤ 3 (small, isolated change set)
- At least ONE changed source file has a direct test mapping via `test_map_pattern` in `LANG_PROFILES`, OR total test count < 500 (fast enough for full suite as fallback)
- NO changed file is imported by 3+ other modules in `code_graph.mmd`
- NO test infrastructure files were changed (`conftest.py`, `pytest.ini`, `pyproject.toml [tool.pytest]`)
- NO version change in `pactkit.yaml` (version bump implies broader impact)

**Fallback**: If `code_graph.mmd` does not exist (e.g., non-PDCA project or not yet generated), always run full regression.

### Step 2.3: Decision Logging (MANDATORY)
After evaluating the decision tree, output the decision and the reason:
- If skip: `"Regression: SKIP — doc-only change, no source files modified"`
- If story-only: `"Regression: STORY-ONLY — {N} new test files, no source changes"`
- If full (version bump): `"Regression: FULL — version bump detected, release requires full test suite"`
- If full (other): `"Regression: FULL — {reason}"` (e.g., "Regression: FULL — config.py imported by 5 modules")
- If impact-based: `"Regression: IMPACT-BASED — {N} test files based on call graph analysis"`
- If incremental: `"Regression: INCREMENTAL — {N} mapped test files, {conditions summary}"`
- This log helps the user understand why full regression was chosen and builds trust in the decision tree.

### Step 2.5: Coverage Verification (Conditional)
IF `pytest-cov` is available, run tests with coverage on changed source files:
- `pytest --cov=<changed_modules> --cov-report=term-missing tests/`
- **≥ 80%** line coverage on changed files: PASS — proceed normally
- **50-79%**: WARN — output: "Changed file `{file}` has {N}% coverage. Consider running `/project-check` to generate missing tests."
- **< 50%**: BLOCK — require user confirmation: "Changed file `{file}` has only {N}% coverage. Proceed anyway?"
- Include coverage data in the output so the user can evaluate test quality.

### Step 2.7: Smart Lint Gate (STORY-030)
> **Purpose**: Stack-aware lint check with configurable behavior.

1. **Detect Stack**: Read `lint_command` from `LANG_PROFILES` for the detected project stack.
   - Example (Python): `ruff check src/ tests/`
   - Example (Node): `npx eslint .`
2. **Auto-Fix (Conditional)**: Read `auto_fix` from `pactkit.yaml`.
   - If `auto_fix: true`: Run lint with fix flag first (e.g., `ruff check --fix src/ tests/`), then re-run lint to verify.
   - If `auto_fix: false` (default): Skip auto-fix, run lint in check-only mode.
3. **Run Lint**: Execute the lint command for the detected stack.
4. **Blocking Behavior**: Read `lint_blocking` from `pactkit.yaml`.
   - If `lint_blocking: true`: Lint failures **STOP** the commit. Report errors and do NOT proceed.
   - If `lint_blocking: false` (default): Lint failures are reported as **warnings**. Print findings but proceed with commit.
5. **Skip**: If no lint command found for the stack, skip silently: "No lint command configured — skipping lint gate."

### Step 3: Gate
- If any test fails, **STOP immediately**. Do NOT proceed to commit.
- **Do NOT attempt to fix** pre-existing test failures or modify code you do not understand.
- The agent MUST NOT assume it understands pre-existing test intent — the project may have adopted PDCA mid-way and there is no Spec for older features.
- Report the failure to the user with: which test failed, what it appears to test, and which change likely caused it.
- Only continue if ALL tests and lint checks are GREEN.

## 🎬 Phase 3: Hygiene Check & Fix
1.  **Verify**: Are tasks for this Story marked `[x]`?
2.  **Auto-Fix**:
    - If tests are GREEN but tasks are `[ ]`, **Ask the user**: "Tests passed but tasks are unchecked. Mark as done?"
    - If user agrees, update `sprint_board.md` immediately.
3.  **Lessons Auto-append with Quality Gate (MANDATORY)**: Evaluate the lesson before appending to `docs/architecture/governance/lessons.md`:
    - **Step 1 — Score** the lesson on 5 dimensions (1=Low, 3=Medium, 5=High):
      | Dimension | 1 (Low) | 3 (Medium) | 5 (High) |
      |-----------|---------|------------|----------|
      | Specificity | Abstract principles only | Has code example | Covers all usage patterns |
      | Actionability | Unclear what to do | Main steps understandable | Immediately actionable |
      | Scope Fit | Too broad or narrow | Mostly appropriate | Name and content aligned |
      | Non-redundancy | Nearly identical to existing | Some unique perspective | Completely unique value |
      | Coverage | Partial coverage | Main cases covered | Includes edge cases |
    - **Step 2 — Bonus**: If Check Phase produced any P0 or P1 findings that inspired this lesson, add **+3** to the total.
    - **Step 3 — Gate**: Read `done.lesson_quality_threshold` from `pactkit.yaml` (default: **15**).
      - If total score < threshold: **do NOT append**. Log: `"Lesson skipped (score {N}/25 < threshold {T})"`
      - If total score >= threshold: append row with format: `| {YYYY-MM-DD} | {summary} (score: {N}/25) | {STORY_ID} |`
    - This is NOT conditional on Memory MCP — always evaluate and either append or log skip.
4.  **Invariants Refresh (MANDATORY)**: Update the Invariants section in `docs/architecture/governance/rules.md`:
    - Read the current `rules.md` file.
    - Update the test count to match the actual number from the most recent test run (e.g., "All {N}+ tests must pass").
    - Preserve the Architecture Decisions (ADR) table — only update the Invariants section.
    - If `rules.md` does not exist, skip silently.
5.  **Memory MCP (Conditional)**: IF `mcp__memory__add_observations` tool is available, record lessons learned:
    - Use `mcp__memory__add_observations` on the `{STORY_ID}` entity with: implementation patterns used, pitfalls encountered, key files modified, and any non-obvious decisions made during implementation
    - This builds a cumulative project knowledge base that persists across sessions

## 🎬 Phase 3.5: Archive (Optional)
1.  **Check**: Are all tasks for the current Story marked `[x]`?
2.  **Action**: If yes, run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py archive`.
3.  **Result**: Completed stories are moved to `docs/product/archive/archive_YYYYMM.md`.

## 🎬 Phase 3.5.5: Issue Tracker Verification (Backfill Safety Net)
> **Purpose**: Verify GitHub Issue exists for the Story; create backfill if Plan phase was skipped.
1.  **Check Config**: Read `pactkit.yaml` for `issue_tracker.provider`.
2.  **If `provider: none` or section missing**: Skip silently, proceed to Phase 3.6.
3.  **If `provider: github`**:
    a. **CLI Check**: Run `gh --version`. If unavailable, print warning "Issue tracker verification skipped: gh CLI unavailable" and proceed to Phase 3.6.
    b. **Search**: Run `gh issue list --search "{STORY_ID}" --state all --json number,title,url` to find existing issue.
    c. **If issue found**:
       - Check if Sprint Board entry has issue link (e.g., `[#N](url)`)
       - If no link: update Sprint Board entry to include `[#{number}]({url})`
       - Proceed to Phase 3.6 for closure
    d. **If issue NOT found (Backfill)**:
       - Create issue: `gh issue create --title "{STORY_ID}: {Story Title}" --body "Spec: docs/specs/{STORY_ID}.md

**Status**: Backfilled during Done phase"`
       - Parse the returned issue URL
       - Update Sprint Board entry to include `[#{number}]({url})`
       - Proceed to Phase 3.6 for closure
    e. **If any gh command fails**: Print warning with error message, continue to Phase 3.6.

## 🎬 Phase 3.6: Issue Tracker Closure (Conditional)
> **Purpose**: Close linked external issues when the Story is done.
1.  **Check Config**: Read `pactkit.yaml` for `issue_tracker.provider`.
2.  **If `provider: github`**:
    - Parse the Sprint Board entry for a linked issue URL (e.g., `[#123](https://github.com/...)`)
    - If found: run `gh issue close <number> --comment "Completed in $(git rev-parse --short HEAD)"`
    - If `gh` CLI unavailable or closure fails: print warning, continue
3.  **If `provider: none` or section missing**: Skip silently.

## 🎬 Phase 4: Git Commit
0.  **Enterprise Check**: If `enterprise.no_git: true` in `pactkit.yaml`, skip ALL git operations in this phase. Print: "ℹ️ Git operations disabled (enterprise.no_git)". Skip to the Session Context Update phase.
1.  **Format**: `feat(scope): <title from spec>`
2.  **Execute**: Run the git commit command.
3.  **Post-Commit Prompts**:
    - **Version bump?** If `pyproject.toml` version was changed in this Story: "ℹ️ Version bump detected. Run `/project-release` to create snapshot and git tag."
    - **Feature branch?** If current branch is not `main`/`master`: "ℹ️ Working on a feature branch. Run `/project-pr` to push and create a pull request."

## 🎬 Phase 4.5: Session Context Update
> **Purpose**: Generate `docs/product/context.md` so the next session auto-loads project state.
1.  **Read Board**: Read `docs/product/sprint_board.md` and extract:
    - Stories in 🔄 In Progress (with IDs and titles)
    - Stories in 📋 Backlog (count)
    - Stories in ✅ Done (most recent 3, with IDs and titles)
2.  **Read Lessons**: Read `docs/architecture/governance/lessons.md` and extract the last 5 entries.
3.  **Active Branches**: Run `git branch --list 'feature/*' 'fix/*'` to list active branches.
4.  **Write Context**: Write `docs/product/context.md` with this format:
    ```markdown
    # Project Context (Auto-generated)
    > Last updated: {ISO timestamp} by /project-done

    ## Sprint Status
    {In Progress stories with IDs | Backlog count | Done count}

    ## Recent Completions
    {Last 3 completed stories, one line each}

    ## Active Branches
    {git branch output, or "None" if no feature/fix branches}

    ## Key Decisions
    {Last 5 lessons from lessons.md}

    ## Next Recommended Action
    {If In Progress stories exist: `/project-act STORY-XXX` | If only Backlog: `/project-plan` | If board empty: `/project-design`}
    ```
5.  **Commit Context**: `git add docs/product/context.md && git commit --amend --no-edit` to include context.md in the commit.
