---
description: "Hotfix fast track: lightweight fix path that bypasses PDCA"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Hotfix (v1.3.0 Traceable Fast Track)
- **Usage**: `/project-hotfix "$ARGUMENTS"`
- **Agent**: Senior Developer

> **PRINCIPLE**: This command is a lightweight fast-fix channel with traceability.
> Lightweight Spec + Board entry are auto-created. No TDD workflow required.
> Suitable for typos, configuration changes, style adjustments, obvious bugs, and other minor fixes.
> **Spec Lint Gate exemption**: This path SKIPS the Spec Lint Gate (Phase 0.5 in `/project-act`). Hotfix Specs use a lightweight format and are not subject to full structural validation.

## ⚠️ Scope of Application
- ✅ Fix typos / spelling errors
- ✅ Modify configuration files
- ✅ Adjust style / formatting
- ✅ Fix obvious small bugs (single file, clear logic)
- ❌ New feature development → use `/project-plan` + `/project-act`
- ❌ Multi-module refactoring → use `/project-plan` + `/project-act`

## 🧠 Phase 0: Locate & Register
1.  **Parse**: Understand what needs to be fixed from `$ARGUMENTS`.
2.  **Locate**: Use `Grep` or `Glob` to quickly locate the target file and code line.
3.  **Assess**: Confirm this is a minor fix (suitable for Hotfix), not a change requiring full PDCA.
    - If the assessment reveals a complex change, **proactively suggest the user switch to** `/project-plan`.
4.  **Assign HOTFIX-ID**: Run `pactkit next-id` to get the next STORY number, then use HOTFIX-{developer}-{NNN} pattern (e.g., HOTFIX-slim-001). The numeric part should match the next-id output.
5.  **Create Spec**: Create a lightweight Spec at `docs/specs/HOTFIX-{NNN}.md` with:
    - Title, Background (one sentence), Target file/line, and what was fixed.
6.  **Add Board Entry**: Add the hotfix to the Board:
    - `{BOARD_CMD} add_story HOTFIX-{NNN} "Short title" "Fix description"`

## 🔍 Phase 0.5: Impact Check (Lightweight)
> **PURPOSE**: Data-driven side-effect awareness — read existing call graphs to surface upstream callers before modifying code. This is advisory (L3 SHOULD), non-blocking.
1.  **Check Graph Availability**: Look for `docs/architecture/graphs/call_graph.mmd` or `docs/architecture/graphs/reverse_call_graph.mmd` or `docs/architecture/graphs/code_graph.mmd`.
    - If none exist: log "No call graph available — skipping impact check" and proceed to Phase 1.
2.  **Identify Callers**: Search the available `.mmd` file for the target function/file identified in Phase 0. Count how many other nodes reference it (callers/importers).
3.  **High-Fan-In Warning**: If the target has **3+ callers**, SHOULD warn the user:
    > "⚠️ Target has {N} callers in the call graph. Changes may affect upstream consumers. Consider `/project-act` for full impact analysis."
    - This warning is advisory — the user can acknowledge and proceed.
4.  **Proceed**: Continue to Phase 1 regardless of findings.

## 🔧 Phase 1: Fix
1.  **Fix**: Use `Edit` or `Write` to directly fix the target code.
2.  **Scope**: Keep the modification scope as small as possible — only change what must be changed, no extra optimization or refactoring.
3.  **No Side Effects**: Ensure the modification does not introduce new dependencies or change interface signatures.

## ✅ Phase 2: Verify
1.  **Run Tests (Incremental)**: Run `pactkit test-map <changed-files>` to find related test files, then run only those tests (e.g., `pytest tests/unit/test_foo.py -q`). Fallback to full suite if no mapping.
2.  **Run Lint**: Run `pactkit lint` to verify no lint errors in changed files. If `pactkit lint` is unavailable, fall back to the stack's lint command directly.
3.  **On Failure**: If tests or lint fail:
    - Output the failing test name and error message
    - **Do not auto-rollback** — let the user decide whether to continue
    - Suggestion: check whether the fix is correct, or switch to `/project-act` for the full workflow

## 📦 Phase 3: Commit
1.  **Conventional Commit**: Generate a standardized commit message:
    - Format: `fix(scope): short description for HOTFIX-{NNN}`
    - Infer scope from the modified file path (e.g. `config`, `auth`, `ui`)
2.  **Confirm**: **Must ask the user for confirmation** before executing `git commit`.
    - Output: "Suggested commit: `fix(scope): description`. Confirm commit?"
3.  **Execute**: After user confirmation, execute git add + git commit.
4.  **Update Board**: Run `{BOARD_CMD} update_task HOTFIX-{NNN} "Task Name"` for each task to mark it done.

## 📋 Phase 3.5: Session Context Update
1.  **Update Context**: Run `pactkit context` to regenerate `docs/product/context.md`. Set "Last updated by" to `/project-hotfix`.

## 🚫 What This Command Does NOT Do
- Does not require writing tests before code (no TDD)
- Does not run `visualize` to update architecture graphs
