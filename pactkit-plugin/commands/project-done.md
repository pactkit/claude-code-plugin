---
description: "Code cleanup, Board update, Git commit"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Done (v1.3.0 Smart Gatekeeper)
- **Usage**: `/project-done`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: The Thinking Process (Mandatory)
1.  **Audit**: Are tests passing? Is the Board updated?
2.  **Semantics**: Determine correct Conventional Commit scope.

## 🎬 Phase 1: Context Loading
1.  **Read Spec**: Read `docs/specs/{ID}.md`.
2.  **Read Board**: Read `docs/product/sprint_board.md`.

## 🎬 Phase 2: Housekeeping (Deep Clean)
1.  **Action**: Remove language-specific temp artifacts per `LANG_PROFILES[stack].cleanup`.
2.  **Update Reality (Lazy Visualize)**: Apply the Lazy Visualize Protocol (see Shared Protocols) — run `visualize`, `--mode class`, and `--mode call` if `LANG_PROFILES[stack].source_dirs` files changed. If no source changes and graph exists, skip with log: "Graph up-to-date — no source changes".
3.  **HLD Consistency Check**: Verify `system_design.mmd` component counts match reality. Warn if stale.

## 🎬 Phase 2.5: Regression Gate (MANDATORY)
> **CRITICAL**: Do NOT skip this step. This is the safety net before commit.

### Step 1: Impact Analysis
- Run `git diff --name-only HEAD~1` (or vs. branch base) to list all changed files.
- Check if `docs/architecture/graphs/code_graph.mmd` exists.

### Step 1.3: Doc-Only Shortcut
Classify changed files using `LANG_PROFILES[stack].source_dirs` and `file_ext`:
- **Zero source files** changed, no new tests → SKIP regression, proceed to Step 2.7.
- **Zero source files** but new test files exist → run only those test files, proceed to Step 2.7.
- **Any source files** changed → continue to Step 1.6.

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
   {VISUALIZE_CMD} impact --entry <func_name>
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
> **DEFAULT**: Run **full regression**. Run incremental only if: `code_graph.mmd` recently updated, ≤ 3 source files changed, test mappings exist via `LANG_PROFILES[stack].test_map_pattern`, no high-fan-in files (3+ importers), no test infra changes. For fast/small suites (< 500 tests), skip the decision tree and run full.
> **Fallback**: If `code_graph.mmd` does not exist, always run full regression.

### Step 2.3: Decision Logging (MANDATORY)
After evaluating the decision tree, log the decision with format: `"Regression: {TYPE} — {reason}"` (e.g., SKIP, STORY-ONLY, FULL, IMPACT-BASED, INCREMENTAL).

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
3.  **Lessons Auto-append (MANDATORY)**: Append a lesson to `docs/architecture/governance/lessons.md` if it passes these two checks:
    - **Specific?** Does the lesson reference a concrete file, function, or pattern? (Not just a generic principle)
    - **Non-duplicate?** Is it meaningfully different from the last 5 entries in `lessons.md`?
    - If both yes: append row using format `{LESSONS_ROW_FORMAT}` where date=YYYY-MM-DD, context={STORY_ID}
    - If either no: skip with log: `"Lesson skipped: {reason}"`
4.  **Invariants Refresh (MANDATORY)**: Update the Invariants section in `docs/architecture/governance/rules.md`:
    - Read the current `rules.md` file.
    - Update the test count to match the actual number from the most recent test run (e.g., "All {N}+ tests must pass").
    - Preserve the Architecture Decisions (ADR) table — only update the Invariants section.
    - If `rules.md` does not exist, skip silently.
5.  **Memory MCP (Conditional)**: IF Memory MCP is available, use add_observations to record lessons learned (patterns, pitfalls, key files) on the `{STORY_ID}` entity.

## 🎬 Phase 3.5: Archive (Optional)
1.  **Check**: Are all tasks for the current Story marked `[x]`?
2.  **Action**: If yes, run `{BOARD_CMD} archive`.
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
1.  **Write Context**: Update `docs/product/context.md` with the following required sections (from `schemas.CONTEXT_SECTIONS`):
{CONTEXT_SECTIONS}
    Set "Last updated by" to `/project-done`.
2.  **Commit Context**: `git add docs/product/context.md && git commit --amend --no-edit` to include context.md in the commit.
