---
description: "Code cleanup, Board update, Git commit"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Done (v1.3.0 Smart Gatekeeper)
- **Usage**: `/project-done`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: The Thinking Process
1.  **Audit**: Are tests passing? Is the Board updated?
2.  **Semantics**: Determine correct Conventional Commit scope.

## 🎬 Phase 1: Context Loading
1.  **Read Spec**: Read `docs/specs/{ID}.md`.
2.  **Read Board**: Read `docs/product/sprint_board.md`.

## 🎬 Phase 2: Housekeeping (Deep Clean)
1.  Run `pactkit clean` to remove language-specific temp artifacts.
2.  Run `pactkit visualize --lazy` to update graphs only if source files changed (file, `--mode class`, `--mode call`). If skipped, log: "Graph up-to-date — no source changes".
3.  **HLD Consistency Check**: Run `pactkit doctor` and check HLD drift. If drift > 3, WARN user: "system_design.mmd is {N} modules behind — consider updating it."

## 🎬 Phase 2.5: Regression Gate (CRITICAL)
> **CRITICAL**: Do NOT skip this step. This is the safety net before commit.

### Step 0: Source Change Pre-Check
- **Act-to-Done Fast Path**: If `context.md` shows the last command was `/project-act` AND the Act commit already passed regression + lint (check context.md Agent Continuation or last-command field), skip the entire Phase 2.5 with log: `"Regression: SKIP — Act already verified, no intervening changes"`. Proceed directly to Phase 3.
- Run `git diff --name-only HEAD~1` (or vs. branch base) to list all changed files.
- Filter for source and test files only (exclude docs, configs, graphs).
- If **no source/test files changed** since the last commit (e.g., only docs, board, graphs, or config changed): log `"Regression: SKIP — no source/test changes since Act"` and proceed directly to Step 2.7 (Smart Lint Gate). This avoids re-running 3000+ tests when Act already verified the code.

### Step 1: Impact Analysis
- Check if `docs/architecture/graphs/code_graph.mmd` exists.

### Step 1.3: Classification Shortcut
Run `pactkit regression` (or `pactkit regression <files>`) to classify changes (doc-only → SKIP):
- **SKIP** → proceed to Step 2.7 (no regression needed).
- **FULL** → skip impact analysis, proceed directly to Step 3 (full regression).
- **IMPACT** → continue to Step 1.6.

### Step 1.6: Release Gate — Version Bump Override
If `pactkit regression` returns FULL (version/dependency change detected), proceed directly to Step 3.
Otherwise continue to Step 1.7.

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

### Step 2.3: Decision Logging (MUST)
After evaluating the decision tree, log the decision with format: `"Regression: {TYPE} — {reason}"` (e.g., SKIP, STORY-ONLY, FULL, IMPACT-BASED, INCREMENTAL).

### Step 2.5: Coverage Verification (Conditional)
Run `pactkit coverage-gate <changed-files>` to verify coverage on changed source files.
- The command auto-detects modules, runs pytest --cov, and applies 3-tier thresholds:
  - **≥ 80%**: PASS — proceed normally
  - **50-79%**: WARN — output: "Changed file `{file}` has {N}% coverage. Consider running `/project-check` to generate missing tests."
  - **< 50%**: BLOCK — require user confirmation: "Changed file `{file}` has only {N}% coverage. Proceed anyway?"
- If `pactkit coverage-gate` is unavailable, fall back to manual: construct `pytest --cov=<changed_modules> --cov-report=term-missing tests/` and parse output.
- Include coverage data in the output so the user can evaluate test quality.

### Step 2.7: Smart Lint Gate (STORY-030)
> **Purpose**: Stack-aware lint check with configurable behavior.

0. **Act-to-Done Fast Path**: If `context.md` shows the last command was `/project-act` AND `git diff HEAD --name-only` shows no source/test file changes since the Act commit, skip lint with log: `"Lint: SKIP — Act already passed lint, no new changes"`. Proceed to Step 3.
1. Run `pactkit lint` to execute the stack-aware lint gate. This auto-detects the project stack, reads `lint_command` from `LANG_PROFILES`, and respects `auto_fix` and `lint_blocking` from `pactkit.yaml`.
   - If `auto_fix: true` in config: `pactkit lint` runs fix pass first, then check pass.
   - If `lint_blocking: true` and lint fails: **STOP** the commit. Report errors and do NOT proceed.
   - If `lint_blocking: false` (default): Lint failures are reported as **warnings**. Print findings but proceed with commit.
2. If `pactkit lint` is unavailable, fall back to manual lint: detect stack, read `lint_command` from LANG_PROFILES, run the command directly.
3. **Skip**: If no lint command found for the stack, skip silently: "No lint command configured — skipping lint gate."

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
3.  **Lessons Auto-append (MUST)**: Run `pactkit lesson-append --story {STORY_ID} --text "lesson text" [--context "file.py:func"]`.
    - The command checks specificity (references concrete file/function?) and dedup (different from last 5 entries?).
    - If both pass: appends row using format `{LESSONS_ROW_FORMAT}` where date=YYYY-MM-DD, context={STORY_ID}
    - If either fails: skip with log from command output.
    - If `pactkit lesson-append` is unavailable, fall back to manual append with the same checks.
4.  **Invariants Refresh (MUST)**: Run `pactkit invariants-refresh --test-count {N}` where {N} is the actual count from the most recent test run.
    - The command updates `docs/architecture/governance/rules.md` invariant "All {N}+ tests must pass".
    - If `pactkit invariants-refresh` is unavailable, fall back to manual: read rules.md, find the pattern, replace the number.
5.  **Document Validators (Non-blocking)**: Run document structure checks as warnings:
    - `pactkit lint-context` — validates `docs/product/context.md` structure
    - `pactkit lint-lessons` — validates `docs/architecture/governance/lessons.md` structure
    - These are non-blocking: report warnings but do not stop the Done flow.
6.  **Spec Status Update (MUST)**: Run `pactkit spec-status docs/specs/{STORY_ID}.md Done` to update `| Status | Draft |` to `| Status | Done |` in the spec file. If `pactkit spec-status` is unavailable, manually edit the spec file.
7.  **Memory MCP (Conditional)**: IF Memory MCP is available, use add_observations to record lessons learned (patterns, pitfalls, key files) on the `{STORY_ID}` entity.
8.  **Harness Audit Refresh (Conditional)**: Run `pactkit audit --append --if-needed {STORY_ID}`. Only refreshes when `harness_audit.json` exists AND its `story_id` matches `{STORY_ID}` (this story owns the audit). Silently skips if no audit was ever run or if the audit belongs to a different story. If it runs and `ready` changed from `true` to `false`, WARN the user.

## 🎬 Phase 3.5: Archive (Optional)
1.  **Check**: Are all tasks for the current Story marked `[x]`?
2.  **Action**: If yes, run `{BOARD_CMD} archive`.
3.  **Result**: Completed stories are moved to `docs/product/archive/archive_YYYYMM.md`.

## 🎬 Phase 3.5.5: Issue Tracker Verification (BUG/HOTFIX Only)
> **Purpose**: Verify GitHub Issue exists for BUG/HOTFIX items; STORY items are NOT synced to protect IP.
1.  Run `pactkit issue-sync {ITEM_ID}` to handle the full issue lifecycle:
    - STORY items: skipped automatically (IP protection).
    - BUG/HOTFIX items: searches for existing issue, backfill-creates if missing, returns issue URL.
2.  If `pactkit issue-sync` returns a URL, update the Sprint Board entry to include `[#{number}]({url})`.
3.  If `pactkit issue-sync` is unavailable, fall back to manual `gh` CLI commands:
    a. **CLI Check**: Run `gh --version`. If unavailable, print warning and proceed to Phase 3.6.
    b. **Search**: Run `gh issue list --search "{ITEM_ID}" --state all --json number,title,url`.
    c. **If not found**: Create issue via `gh issue create`.
    d. **If any gh command fails**: Print warning, continue to Phase 3.6.

## 🎬 Phase 3.6: Issue Tracker Closure (BUG/HOTFIX Only)
> **Purpose**: Close linked external issues when BUG/HOTFIX is done. STORY items are skipped.
1.  **Check Item Type**: If current item is `STORY-*`, skip this phase silently.
2.  **Check Config**: Read `pactkit.yaml` for `issue_tracker.provider`.
3.  **If `provider: github`**:
    - Parse the Sprint Board entry for a linked issue URL (e.g., `[#123](https://github.com/...)`)
    - If found: run `gh issue close <number> --comment "Completed in $(git rev-parse --short HEAD)"`
    - If `gh` CLI unavailable or closure fails: print warning, continue
4.  **If `provider: none` or section missing**: Skip silently.

## 🎬 Phase 4: Git Commit
0.  **Enterprise Check**: If `enterprise.no_git: true` in `pactkit.yaml`, skip ALL git operations in this phase. Print: "ℹ️ Git operations disabled (enterprise.no_git)". Skip to the Session Context Update phase.
0.5.  **Deployment Verification (self-dev only)**: Only when developing PactKit itself (`pyproject.toml` name == "pactkit"):
    - Run `pactkit update` to redeploy all prompts, agents, commands, skills, and rules.
    - Smoke-check: for each AC that references prompt/deployed file content, `grep` 1-2 key assertions on deployed files (e.g., `{GLOBAL_CONFIG_DIR}/commands/*.md`).
    - Report: `Deploy verification: PASS ({N} assertions checked)` or `FAIL (details)`.
    - If FAIL, fix the deployment issue before committing.
    - **If NOT self-dev**: Skip this step silently.
1.  **Format**: `feat(scope): <title from spec>`
2.  **Execute**: Run the git commit command.
3.  **Post-Commit Prompts**:
    - **Version bump?** If `pyproject.toml` version was changed in this Story: "ℹ️ Version bump detected. Run `/project-release` to create snapshot and git tag."
    - **Feature branch?** If current branch is not `main`/`master`: "ℹ️ Working on a feature branch. Run `/project-pr` to push and create a pull request."
    - **CI Status Check (Conditional)**: If `ci.provider` is `github` in `pactkit.yaml` and `gh` CLI is available:
      1. After push, run `gh run list --limit 1 --json status,name,databaseId` to check the latest workflow run.
      2. Report: `CI: [pass/fail/pending] — {workflow_name} #{run_id}`
      3. If CI fails, print a warning but do NOT block the Done flow.
      4. If `gh` CLI is unavailable or command fails, skip silently.

## 🎬 Phase 4.5: Session Context Update
1.  Run `pactkit context` to generate `docs/product/context.md` (sections: {CONTEXT_SECTIONS}). Set "Last updated by" to `/project-done`. This also clears the Agent Continuation section to `No active work session.` since no `--continuation` flag is passed.
2.  **Commit Context**: `git add docs/product/context.md && git commit --amend --no-edit` to include context.md in the commit.
