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
4.  **Detect Stack & Select Stack Reference**: Identify the project type from source files (`.py`, `.ts`/`.tsx`, `.go`, `.java`). Apply the corresponding language-specific best practices throughout implementation and testing.
5.  **Memory MCP (Conditional)**: IF Memory MCP is available, use search_nodes to load prior context for {STORY_ID} — retrieve architectural decisions and design rationale from the Plan phase.

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
1.  **Visual Scan**: Run `visualize --focus <module>` to see neighbors. For large codebases, add `--depth 2`.
2.  **Trace Verification** — use pactkit-trace skill:
    - Before touching any code, confirm the call site and ensure you don't break existing callers.

## 🎬 Phase 2: Test Scaffolding (TDD)
1.  **Constraint**: DO NOT write source code yet.
2.  **Action**: Create a reproduction test case in `tests/unit/`.
    - Use the knowledge from Phase 1 to mock/stub dependencies correctly.

## 🎬 Phase 3: Implementation
1.  **Write Code**: Implement logic in the appropriate source directory.
    - **Context7 (Conditional)**: IF implementing with an unfamiliar library API, use Context7 MCP to fetch up-to-date documentation before writing code.
2.  **TDD Loop (Safe Iteration)**: Run ONLY the tests created in Phase 2. Loop until GREEN.
    - Do NOT include pre-existing tests in this loop.
    - **Iteration Cap**: Maximum **5 iterations**. If exceeded, **STOP** and report.
    - **Environment Failure Bailout**: For environment errors (`ModuleNotFoundError`, `ImportError`, `ConnectionError`, `ConnectionRefusedError`, `PermissionError`, timeout):
      - **Project-internal check first**: If the missing module is project-internal (part of your codebase): NOT a bailout — do not modify source code for env issues, go back and implement it.
      - If third-party: attempt to resolve the dependency (e.g., `pip install`), then STOP and report if unresolvable.
3.  **Regression Check (Read-Only Gate)**: After the TDD loop is GREEN, run a broader regression check.
    - **Identify changed modules**: `git diff --name-only HEAD` to list modified source files.
    - **Doc-Only detection**: Classify changed files using `LANG_PROFILES[stack].source_dirs`. If zero source files changed, skip regression. Log: `"Regression: SKIP — doc-only change"`.
    - **Map to related tests**: Use Test Mapping Protocol (see Shared Protocols) for incremental test selection.
    - **Scope decision**: If any changed file has 3+ importers in `code_graph.mmd`, run full suite. Otherwise, run only mapped tests.
    - **Fallback**: If no test mapping can be determined, fall back to the full test suite.
    - **CRITICAL — Pre-existing test failure protocol**: If a pre-existing test fails, **DO NOT modify** it. **STOP** and report to the user. This is a one-shot check, not an iterative loop.

## 🎬 Phase 4: Sync & Document
1.  **Hygiene**: Delete temp files.
2.  **Update Reality (Lazy Visualize)**: Apply the Lazy Visualize Protocol (see Shared Protocols) — run `visualize`, `--mode class`, and `--mode call` if source files changed.
3.  **Update Board (CRITICAL)**: Mark the tasks in `docs/product/sprint_board.md` as `[x]`.
