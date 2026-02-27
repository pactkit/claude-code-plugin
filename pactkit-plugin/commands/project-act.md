---
description: "Implement code per Spec, strict TDD"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Act (v1.3.0 Stack-Aware)
- **Usage**: `/project-act $ARGUMENTS`
- **Agent**: Senior Developer

## 🧠 Phase 0: The Thinking Process (Mandatory)
1.  **Read Law**: Read the Spec (`docs/specs/`) carefully.
2.  **RFC Gate (Feasibility Check)**: If you identify a requirement in the Spec that is technically infeasible, contradictory, or would require violating a security/architectural constraint, invoke the **RFC Protocol**:
    - **STOP** implementation immediately. Do NOT write any code.
    - **Report** to the user: (a) quote the exact problematic requirement from the Spec, (b) explain why it is infeasible (technical reasoning), (c) suggest an alternative approach.
    - You MUST NOT modify the Spec unilaterally — only the user (or Architect via a new `/project-plan` cycle) may amend Tier 1.
    - Wait for user guidance before proceeding.
3.  **Locate Target**: Which file/function needs surgery?
4.  **Detect Stack & Select References**: Identify the project type from source files:
    - `.py` files → Python stack → Consult `DEV_REF_BACKEND` + `TEST_REF_PYTHON`
    - `.ts`/`.tsx`/`.vue`/`.svelte` files → Frontend stack → Consult `DEV_REF_FRONTEND` + `TEST_REF_NODE`
    - `.go` files → Go stack → Consult `DEV_REF_BACKEND` + `TEST_REF_GO`
    - `.java` files → Java stack → Consult `DEV_REF_BACKEND` + `TEST_REF_JAVA`
    - Mixed (frontend + backend) → Consult both `DEV_REF_FRONTEND` and `DEV_REF_BACKEND`
    - Use the Stack Reference guidelines throughout implementation and testing phases.
5.  **Memory MCP (Conditional)**: IF `mcp__memory__search_nodes` tool is available, load prior context:
    - Use `mcp__memory__search_nodes` with the STORY_ID to retrieve any stored architectural decisions or design rationale from the Plan phase
    - Use `mcp__memory__search_nodes` with relevant module/feature keywords to find related past decisions from other stories

## 🛡️ Phase 0.5: Spec Lint Gate (Mandatory)
> **PURPOSE**: Non-AI structural validation — ensures "Spec is Law" has physical enforcement before any code is written.
1.  **Run Linter**: Execute the Spec Linter on the current Story's spec:
    ```bash
    python3 src/pactkit/skills/spec_linter.py docs/specs/{STORY_ID}.md
    ```
    Replace `{STORY_ID}` with the actual Story ID from `$ARGUMENTS` (e.g., `STORY-042`).
2.  **If ERRORs found**: **STOP**. Output all ERROR and WARN items. Instruct the user:
    > "Spec Lint failed. Fix the issues above in `docs/specs/{STORY_ID}.md`, then re-run `/project-act`."
    Do NOT proceed to Phase 1.
3.  **If WARNs only**: Output the WARN list, then **continue** to Phase 1.
4.  **If all pass**: Continue silently to Phase 1.

## 📊 Phase 0.6: Consistency Check (Advisory)
> **PURPOSE**: Left-shift quality — catch Spec ↔ Board ↔ Test Case misalignment at the cheapest point (pure text, before any code).
> **NON-BLOCKING**: All findings are WARN or INFO. This phase NEVER stops Act.
1.  **Spec ↔ Board Alignment**:
    - Parse all `### R{N}:` subsections from `docs/specs/{STORY_ID}.md` → list of requirements
    - Parse the Story's task list from `docs/product/sprint_board.md` (the `- [ ]` items under this Story)
    - Cross-reference: for each requirement, find a matching task (exact `R{N}` ID OR ≥50% keyword overlap)
    - Output alignment matrix:
      ```
      | Spec Requirement | Board Task | Status |
      | R1: xxx          | Task: xxx  | ✅ Aligned |
      | R2: xxx          | —          | ⚠️ Missing Task |
      | —                | Task: yyy  | ⚠️ No matching Requirement |
      ```
2.  **Spec AC ↔ Test Case Coverage**:
    - Parse all `### AC{N}:` subsections from the Spec
    - Check if `docs/test_cases/{STORY_ID}_case.md` exists
    - If exists: cross-reference AC items with Scenario entries; report uncovered ACs
    - If not exists: output `ℹ️ Test Case not yet created (normal — generated during Check phase)`
3.  **Summary**:
    - Output counts: `Alignment: {N}/{total} requirements matched | Coverage: {N}/{total} ACs covered`
    - If WARNs found: "Consider updating the Board tasks to match Spec requirements before proceeding."
4.  **Continue**: Regardless of findings, proceed to Phase 1.

## 🎬 Phase 1: Precision Targeting
1.  **Visual Scan**: Run `visualize --focus <module>` to see neighbors.
    - For projects with 50+ source files, add `--depth 2` to limit the graph to 2 levels of dependencies.
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
    - **Iteration Cap**: Maximum **5 iterations**. If the loop does not reach GREEN after 5 iterations, **STOP** and report: "TDD loop exceeded 5 iterations. Likely cause: [error summary]. Please review."
    - **Environment Failure Bailout**: If a test fails with an environment-class error — `ModuleNotFoundError`, `ImportError`, `ConnectionError`, `ConnectionRefusedError`, `FileNotFoundError` (for config/env files), `PermissionError`, or timeout from an external service — apply the following **decision tree** before stopping:
      1. **Project-internal check**: Is the missing module/name under the project root directory (i.e., part of your codebase, not a third-party package)? Check if the module path maps to a file you are building in this Story.
         - **If YES (project-internal)**: This is NOT an environment error — it is incomplete implementation. Return to Phase 3 Step 1 and create or update the missing module. Do not trigger the bailout.
         - **If NO (third-party or external)**: Proceed to step 2.
      2. Attempt to resolve the third-party dependency (e.g., `pip install <package>`, update `requirements.txt`, check `.env` file).
      3. If the dependency cannot be resolved after one attempt, **STOP** and report to the user: "Test requires external service or missing dependency. Please ensure [service/package] is available."
    - **Normal TDD failures** (`AssertionError`, `TypeError`, `ValueError`, etc.) proceed normally — modify your source code and iterate.
3.  **Regression Check (Read-Only Gate)**: After the TDD loop is GREEN, run a broader regression check.
    - **Identify changed modules**: `git diff --name-only HEAD` to list modified source files.
    - **Doc-Only detection**: Classify changed files using `LANG_PROFILES[stack].source_dirs` and `file_ext`. If zero source files were changed (only `.md`, `.yml`, `docs/`, `.github/`, etc.), skip the broader regression — the TDD loop already validated the new tests. Log: `"Regression: SKIP — doc-only change, no source files modified"`. Proceed to Phase 4.
    - **Map to related tests**: For each changed file, find its corresponding test file using the `test_map_pattern` in `LANG_PROFILES`.
    - **Scope decision**: Check if any changed file is imported by 3+ other modules in `code_graph.mmd`. If yes, run the **full test suite**. If no (low fan-in, isolated change), run only the **mapped test files**.
    - **Fallback**: If no test mapping can be determined, or `code_graph.mmd` does not exist, fall back to the full test suite.
    - **CRITICAL — Pre-existing test failure protocol**:
      - If a pre-existing test (one you did NOT create in Phase 2) fails, **DO NOT modify** the failing test or the code it tests.
      - **DO NOT loop** — this is a one-shot check, not an iterative loop.
      - **STOP** and report to the user: which test failed, what it appears to test, and which of your changes likely caused the failure.
      - Suggest options: (a) you revert your change that caused the regression, or (b) the user reviews and provides guidance.
      - You MUST NOT assume you understand the design intent behind pre-existing tests — the project may have adopted PDCA mid-way and there is no Spec for older features.

## 🎬 Phase 4: Sync & Document
1.  **Hygiene**: Delete temp files.
2.  **Update Reality (Lazy Visualize)**:
    - Check if `git diff --name-only HEAD` includes any files in `LANG_PROFILES[stack].source_dirs` OR if `code_graph.mmd` does not exist.
    - **If source files changed OR graph missing**: Run all three visualize commands:
        - `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize`
        - `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`
        - `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize --mode call`
    - **If no source files changed AND graph exists**: Skip with log: `"Graph up-to-date — no source changes"`
3.  **Update Board (CRITICAL)**:
    - Mark the tasks in `docs/product/sprint_board.md` as `[x]`.
    - Use `update_task` or manual edit.
