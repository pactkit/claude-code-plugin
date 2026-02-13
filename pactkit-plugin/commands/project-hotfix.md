---
description: "Hotfix fast track: lightweight fix path that bypasses PDCA"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Hotfix (v22.0 Traceable Fast Track)
- **Usage**: `/project-hotfix "$ARGUMENTS"`
- **Agent**: Senior Developer

> **PRINCIPLE**: This command is a lightweight fast-fix channel with traceability.
> Lightweight Spec + Board entry are auto-created. No TDD workflow required.
> Suitable for typos, configuration changes, style adjustments, obvious bugs, and other minor fixes.

## ⚠️ Scope of Application
- ✅ Fix typos / spelling errors
- ✅ Modify configuration files
- ✅ Adjust style / formatting
- ✅ Fix obvious small bugs (single file, clear logic)
- ❌ New feature development → use `/project-plan` + `/project-act`
- ❌ Multi-module refactoring → use `/project-plan` + `/project-act`

## 🧠 Phase 0: Locate & Register (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block.
1.  **Parse**: Understand what needs to be fixed from `$ARGUMENTS`.
2.  **Locate**: Use `Grep` or `Glob` to quickly locate the target file and code line.
3.  **Assess**: Confirm this is a minor fix (suitable for Hotfix), not a change requiring full PDCA.
    - If the assessment reveals a complex change, **proactively suggest the user switch to** `/project-plan`.
4.  **Assign HOTFIX- ID**: Scan `docs/specs/` for existing `HOTFIX-*.md` files, determine the next available number (e.g., `HOTFIX-001`, `HOTFIX-002`).
5.  **Create Spec**: Create a lightweight Spec at `docs/specs/HOTFIX-{NNN}.md` with:
    - Title, Background (one sentence), Target file/line, and what was fixed.
6.  **Add Board Entry**: Add the hotfix to the Board:
    - `python3 ~/.claude/skills/pactkit-board/scripts/board.py add_story HOTFIX-{NNN} "Short title" "Fix description"`

## 🔧 Phase 1: Fix
1.  **Fix**: Use `Edit` or `Write` to directly fix the target code.
2.  **Scope**: Keep the modification scope as small as possible — only change what must be changed, no extra optimization or refactoring.
3.  **No Side Effects**: Ensure the modification does not introduce new dependencies or change interface signatures.

## ✅ Phase 2: Verify
1.  **Run Tests (Incremental)**: Run only tests related to changed modules to confirm no existing functionality is broken.
    - **Identify changed modules**: `git diff --name-only HEAD` to list modified source files.
    - **Map to related tests**: Use `test_map_pattern` in `LANG_PROFILES` to find corresponding test files.
    - **Run incremental**: Execute only the mapped test files (e.g., `pytest tests/unit/test_foo.py -q`).
    - **Fallback**: If no mapping can be determined, fall back to the full test suite (`pytest tests/ -q`).
2.  **On Failure**: If tests fail:
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
4.  **Update Board**: Mark the hotfix task as done on the Board.

## 🚫 What This Command Does NOT Do
- Does not require writing tests before code (no TDD)
- Does not run `visualize` to update architecture graphs
