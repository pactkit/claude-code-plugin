---
description: "Code cleanup, Board update, Git commit"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Done (v19.8 Smart Gatekeeper)
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
2.  **Update Reality**:
    - Run `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize`
    - Run `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`

## 🎬 Phase 2.5: Regression Gate (MANDATORY)
> **CRITICAL**: Do NOT skip this step. This is the safety net before commit.

### Step 1: Impact Analysis
- Run `git diff --name-only HEAD~1` (or vs. branch base) to list all changed files.
- Check if `docs/architecture/graphs/code_graph.mmd` exists.

### Step 2: Decision Tree (Safe-by-Default)
> **DEFAULT**: Run **full regression** (`pytest tests/`). This is the safe default.

Run **incremental tests** only if ALL of the following conditions are true:
- `code_graph.mmd` exists AND was updated in the current session (not stale)
- Changed source files ≤ 3 (small, isolated change set)
- ALL changed source files have direct test mappings via `test_map_pattern` in `LANG_PROFILES`
- NO changed file is imported by 3+ other modules in `code_graph.mmd`
- NO test infrastructure files were changed (`conftest.py`, `pytest.ini`, `pyproject.toml [tool.pytest]`)
- NO version change in `pactkit.yaml` (version bump implies broader impact)

**Fallback**: If `code_graph.mmd` does not exist (e.g., non-PDCA project or not yet generated), always run full regression.

### Step 2.5: Coverage Verification (Conditional)
IF `pytest-cov` is available, run tests with coverage on changed source files:
- `pytest --cov=<changed_modules> --cov-report=term-missing tests/`
- **≥ 80%** line coverage on changed files: PASS — proceed normally
- **50-79%**: WARN — output: "Changed file `{file}` has {N}% coverage. Consider running `/project-check` to generate missing tests."
- **< 50%**: BLOCK — require user confirmation: "Changed file `{file}` has only {N}% coverage. Proceed anyway?"
- Include coverage data in the output so the user can evaluate test quality.

### Step 3: Gate
- If any test fails, **STOP immediately**. Do NOT proceed to commit.
- **Do NOT attempt to fix** pre-existing test failures or modify code you do not understand.
- The agent MUST NOT assume it understands pre-existing test intent — the project may have adopted PDCA mid-way and there is no Spec for older features.
- Report the failure to the user with: which test failed, what it appears to test, and which change likely caused it.
- Only continue if ALL tests are GREEN.

## 🎬 Phase 3: Hygiene Check & Fix
1.  **Verify**: Are tasks for this Story marked `[x]`?
2.  **Auto-Fix**:
    - If tests are GREEN but tasks are `[ ]`, **Ask the user**: "Tests passed but tasks are unchecked. Mark as done?"
    - If user agrees, update `sprint_board.md` immediately.
3.  **Lessons Auto-append (MANDATORY)**: Append a new row to `docs/architecture/governance/lessons.md`:
    - Format: `| {YYYY-MM-DD} | {one-line summary of what was learned} | {STORY_ID} |`
    - Date: today's date
    - Summary: one sentence describing the key insight, pattern, or pitfall from this Story
    - This is NOT conditional on Memory MCP — always append to lessons.md
4.  **Memory MCP (Conditional)**: IF `mcp__memory__add_observations` tool is available, record lessons learned:
    - Use `mcp__memory__add_observations` on the `{STORY_ID}` entity with: implementation patterns used, pitfalls encountered, key files modified, and any non-obvious decisions made during implementation
    - This builds a cumulative project knowledge base that persists across sessions

## 🎬 Phase 3.5: Archive (Optional)
1.  **Check**: Are all tasks for the current Story marked `[x]`?
2.  **Action**: If yes, run `python3 ~/.claude/skills/pactkit-board/scripts/board.py archive`.
3.  **Result**: Completed stories are moved to `docs/product/archive/archive_YYYYMM.md`.

## 🎬 Phase 3.7: Deploy & Verify (If Applicable)
> **Purpose**: Ensure the committed code works correctly in deployed form.
1.  **Detect Deployer**: Check if the project has a deployer (`pactkit init` or configured in `pactkit.yaml`).
2.  **Deploy**: If a deployer exists, run it (e.g., `python3 pactkit init`).
3.  **Smoke Test**: Spot-check deployed artifacts to verify they contain expected content.
4.  **Skip**: If no deployer is detected, skip this phase and note "No deployer found — skipping deploy verification."
5.  **Gate**: If deployment or verification fails, **STOP**. Do NOT proceed to commit.

## 🎬 Phase 3.8: Release (Conditional) — use pactkit-release skill
> If this Story involves a version bump, invoke the release workflow:
1.  **Detect**: Check if `pyproject.toml` version was changed in this Story.
2.  **If yes**: Run `update_version`, `snapshot`, and `archive` via pactkit-board skill. Tag with `git tag`.
3.  **If no**: Skip to Phase 4.

## 🎬 Phase 4: Git Commit
1.  **Format**: `feat(scope): <title from spec>`
2.  **Execute**: Run the git commit command.

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
