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
2.  **Read Story Facts**: Run `pactkit board list`; never use the Board projection for completion decisions.

## 🎬 Phase 2: Housekeeping (Deep Clean)
1.  Run `pactkit clean` to remove language-specific temp artifacts.
2.  Run `pactkit visualize --lazy` when `LANG_PROFILES.source_dirs` changed; it updates file, `--mode class`, then `--mode call` graphs and Codegraph. Otherwise log: "Graph up-to-date — no source changes".
3.  **HLD Consistency Check**: Run `pactkit doctor` and check HLD drift. If drift > 3, WARN user: "system_design.mmd is {N} modules behind — consider updating it."

## 🎬 Phase 2.5: Regression Gate (CRITICAL)
> **CRITICAL**: Do NOT skip this step. This is the safety net before commit.

### Step 0: Source Change Pre-Check
- If context records a verified `/project-act` and no source/test changed since it, log `"Regression: SKIP — Act already verified, no intervening changes"` and continue at Phase 3.
- Otherwise classify changed files with `git diff --name-only HEAD~1`; doc/config/graph-only changes log `"Regression: SKIP — no source/test changes since Act"` and continue at Smart Lint Gate.

### Step 1: Impact Analysis
- Check graph availability through `pactkit query --impact <target> --json --explain`; do not select providers manually.

### Step 1.3: Classification Shortcut
Run `pactkit regression` (or `pactkit regression <files>`) to classify changes (doc-only → SKIP):
- **SKIP** → proceed to Step 2.7 (no regression needed).
- **FULL** → skip impact analysis, proceed directly to Step 3 (full regression).
- **IMPACT** → continue to Step 1.6.

### Step 1.6: Release Gate — Version Bump Override
If `pactkit regression` returns FULL (version/dependency change detected), proceed directly to Step 3.
Otherwise continue to Step 1.7.

### Step 1.7: Impact-Based Analysis (STORY-053)
With `regression.strategy=impact`, extract changed `def` names from `git diff HEAD~1 --unified=0`; run `{VISUALIZE_CMD} impact --entry <func_name>`, deduplicate mapped tests, and run them when below `regression.max_impact_tests` (default 50). Log `"Regression: IMPACT-BASED — {N} test files based on call graph analysis"`; missing functions, failures, or threshold overflow fall through to Decision Tree.

### Step 2: Decision Tree (Safe-by-Default)
Run full regression by default. Incremental requires a fresh `code_graph.mmd`, ≤3 source files, mappings from `LANG_PROFILES[stack].test_map_pattern`, no test-infra changes, and no file with 3+ importers; missing graph or fast suite (<500 tests) means full.

### Step 2.3: Decision Logging (MUST)
After evaluating the decision tree, log the decision with format: `"Regression: {TYPE} — {reason}"` (e.g., SKIP, STORY-ONLY, FULL, IMPACT-BASED, INCREMENTAL).

### Step 2.5: Coverage Verification (Conditional)
Run `pactkit coverage-gate <changed-files>` to verify coverage on changed source files.
- ≥80% PASS; 50–79% WARN with file/coverage; <50% BLOCK for confirmation. If unavailable, run equivalent `pytest --cov`; report results.

### Step 2.7: Smart Lint Gate (STORY-030)
If Act already verified lint with no later source/test change, log `"Lint: SKIP — Act already passed lint, no new changes"`. Otherwise run `pactkit lint` (or `LANG_PROFILES[stack].lint_command`); honor `auto_fix` and `lint_blocking`, and report non-blocking warnings. No configured command means skip.

### Step 3: Gate
- If any test fails, do not commit or archive. Classify the failure and report the evidence.
- Do not guess at a pre-existing test's intent. A user-authorized repair may continue after reading its governing Spec/Test Case; otherwise leave that failure unchanged and disclose it.
- The agent MUST NOT assume it understands pre-existing test intent — the project may have adopted PDCA mid-way and there is no Spec for older features.
- Report the failure to the user with: which test failed, what it appears to test, and which change likely caused it.
- Proceed to commit/archive only if all required tests and blocking lint checks are green. Safe diagnosis and repair remain available.

## 🎬 Phase 3: Hygiene Check & Fix
1.  **Verify**: Are tasks for this Story marked `[x]`?
2.  **Auto-Fix**:
    - If tests are GREEN but tasks are `[ ]`, **Ask the user**: "Tests passed but tasks are unchecked. Mark as done?"
    - If user agrees, run `pactkit board complete-task {STORY_ID} "<exact task>"` for each task.
3.  **Lessons Auto-append (MUST)**: Run `pactkit lesson-append --story {STORY_ID} --text "lesson text" [--context "file.py:func"]`.
    - The command checks specificity (references concrete file/function?) and dedup (different from last 5 entries?).
    - If both pass: appends row using format `{LESSONS_ROW_FORMAT}` where date=YYYY-MM-DD, context={STORY_ID}
    - If either fails: skip with log from command output.
    - If `pactkit lesson-append` is unavailable, stop and request a Core upgrade; never write a shared Lesson projection manually.
4.  **Invariants Refresh (MUST)**: Run `pactkit invariants-refresh --test-count {N}` where {N} is the actual count from the most recent test run.
    - The command updates `docs/architecture/governance/rules.md` invariant "All {N}+ tests must pass".
    - If `pactkit invariants-refresh` is unavailable, fall back to manual: read rules.md, find the pattern, replace the number.
5.  **Document Validators (Non-blocking)**: Run document structure checks as warnings:
    - `pactkit context --stdout` — validates generation from Story/Lesson facts without writing tracked files
    - `pactkit board render --check` — validates the optional Board projection
    - These are non-blocking: report warnings but do not stop the Done flow.
6.  **Spec Status Update (MUST)**: Run `pactkit spec-status docs/specs/{STORY_ID}.md Done` to update `| Status | Draft |` to `| Status | Done |` in the spec file (accepted values: Draft, In Progress, Done). If `pactkit spec-status` is unavailable, manually edit the spec file.
7.  **Archive Honesty Gate (CRITICAL — STORY-slim-136)**: Run `pactkit done-verify {STORY_ID}` — it mechanically verifies requirement→test evidence, checkbox↔case honesty, and status consistency (Spec Done + Board `[x]` + archive).
    - **Any FAIL (exit ≠ 0)**: Print the evidence lines and do not archive or commit. Continue safe diagnosis or repair when it is within the user's request. WARN-only: print and proceed. CLI too old: warn that the gate was skipped, then proceed.
8.  **Memory MCP (Conditional)**: IF Memory MCP is available, use add_observations to record lessons learned (patterns, pitfalls, key files) on the `{STORY_ID}` entity.
9.  **Harness Audit Refresh (Conditional)**: Run `pactkit audit --append --if-needed {STORY_ID}`. Only refreshes when `harness_audit.json` exists AND its `story_id` matches `{STORY_ID}` (this story owns the audit). Silently skips if no audit was ever run or if the audit belongs to a different story. If it runs and `ready` changed from `true` to `false`, WARN the user.

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
    - First perform the deployment smoke-check in a temporary target directory; do not write a real host configuration as part of Done.
    - If validating the installed host is needed, describe the exact update and ask for explicit authorization before running `pactkit update`.
    - Smoke-check: for each AC that references prompt/deployed file content, inspect 1-2 key assertions in the temporary generated files.
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
1.  Run `pactkit context` to refresh ignored local `.pactkit/context.md`. This clears its Agent Continuation section because no `--continuation` flag is passed.
2.  **Never Commit Context**: `.pactkit/context.md` is a local cache; do not stage, commit, or amend it.
