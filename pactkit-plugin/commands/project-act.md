---
description: "Implement code per Spec, strict TDD"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Act (v22.0 Stack-Aware)
- **Usage**: `/project-act $ARGUMENTS`
- **Agent**: Senior Developer

## 🧠 Phase 0: The Thinking Process (Mandatory)
1.  **Read Law**: Read the Spec (`docs/specs/`) carefully.
2.  **Locate Target**: Which file/function needs surgery?
3.  **Detect Stack & Select References**: Identify the project type from source files:
    - `.py` files → Python stack → Consult `DEV_REF_BACKEND` + `TEST_REF_PYTHON`
    - `.ts`/`.tsx`/`.vue`/`.svelte` files → Frontend stack → Consult `DEV_REF_FRONTEND` + `TEST_REF_NODE`
    - `.go` files → Go stack → Consult `DEV_REF_BACKEND` + `TEST_REF_GO`
    - `.java` files → Java stack → Consult `DEV_REF_BACKEND` + `TEST_REF_JAVA`
    - Mixed (frontend + backend) → Consult both `DEV_REF_FRONTEND` and `DEV_REF_BACKEND`
    - Use the Stack Reference guidelines throughout implementation and testing phases.
4.  **Memory MCP (Conditional)**: IF `mcp__memory__search_nodes` tool is available, load prior context:
    - Use `mcp__memory__search_nodes` with the STORY_ID to retrieve any stored architectural decisions or design rationale from the Plan phase
    - Use `mcp__memory__search_nodes` with relevant module/feature keywords to find related past decisions from other stories

## 🎬 Phase 1: Precision Targeting
1.  **Visual Scan**: Run `visualize --focus <module>` to see neighbors.
2.  **Call Chain**: Run `visualize --mode call --entry <function>` to trace call dependencies.
3.  **Trace Verification** — use pactkit-trace skill:
    - Before touching any code, confirm the call site.
    - Use `Grep` to find all callers, then `visualize --mode call --entry <func>` to trace dependencies.
    - *Goal*: Ensure you don't break existing callers.

## 🎬 Phase 2: Test Scaffolding (TDD)
1.  **Constraint**: DO NOT write source code yet.
2.  **Action**: Create a reproduction test case in `tests/unit/`.
    - Use the knowledge from Phase 1 to mock/stub dependencies correctly.

## 🎬 Phase 3: Implementation
1.  **Write Code**: Implement logic in the appropriate source directory.
    - **Context7 (Conditional)**: IF you are implementing with an unfamiliar library API, use `mcp__context7__resolve-library-id` followed by `mcp__context7__get-library-docs` to fetch up-to-date documentation before writing code. This ensures correct API usage and avoids deprecated patterns.
2.  **TDD Loop (Safe Iteration)**: Run ONLY the tests created in Phase 2 (the new test file for this Story). Loop until GREEN.
    - This loop is safe because you wrote these tests and understand their intent.
    - Do NOT include pre-existing tests in this loop.
3.  **Regression Check (Read-Only Gate)**: After the TDD loop is GREEN, run a broader regression check.
    - **Identify changed modules**: `git diff --name-only HEAD` to list modified source files.
    - **Map to related tests**: For each changed file, find its corresponding test file using the `test_map_pattern` in `LANG_PROFILES`.
    - **Run regression**: Execute the mapped test files plus the full test suite if unsure about change scope.
    - **Fallback**: If no test mapping can be determined or you are unsure about dependency impact, fall back to the full test suite.
    - **CRITICAL — Pre-existing test failure protocol**:
      - If a pre-existing test (one you did NOT create in Phase 2) fails, **DO NOT modify** the failing test or the code it tests.
      - **DO NOT loop** — this is a one-shot check, not an iterative loop.
      - **STOP** and report to the user: which test failed, what it appears to test, and which of your changes likely caused the failure.
      - Suggest options: (a) you revert your change that caused the regression, or (b) the user reviews and provides guidance.
      - You MUST NOT assume you understand the design intent behind pre-existing tests — the project may have adopted PDCA mid-way and there is no Spec for older features.
4.  **Lint Check (Conditional)**: IF a CI config exists (`.github/workflows/*.yml` or similar) or `lint_command` is set in `LANG_PROFILES`:
    - Run the `lint_command` for the detected stack (e.g., `ruff check src/ tests/` for Python).
    - If lint fails, fix the lint errors in your own new/modified files only, then re-run.
    - Do NOT modify pre-existing files to fix lint unless the lint error is in a file you changed in this Story.

## 🎬 Phase 4: Sync & Document
1.  **Hygiene**: Delete temp files.
2.  **Update Reality**:
    - Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize`
    - Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`
3.  **Update Board (CRITICAL)**:
    - Mark the tasks in `docs/product/sprint_board.md` as `[x]`.
    - Use `update_task` or manual edit.
