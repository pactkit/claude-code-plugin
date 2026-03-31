---
description: "Implement code per Spec, strict TDD"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Act (v1.3.0 Stack-Aware)
- **Usage**: `/project-act $ARGUMENTS`
- **Agent**: Senior Developer

## 🧠 Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go. Do NOT try to plan all implementation steps in your head before producing output.
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
    pactkit spec-lint docs/specs/{STORY_ID}.md
    ```
    Replace `{STORY_ID}` with the actual Story ID from `$ARGUMENTS` (e.g., `STORY-042`).
2.  **If ERRORs found**: **STOP**. Output all ERROR and WARN items. Instruct the user:
    > "Spec Lint failed. Fix the issues above in `docs/specs/{STORY_ID}.md`, then re-run `/project-act`."
    Do NOT proceed to Phase 1.
3.  **If WARNs only**: Output the WARN list, then **continue** to Phase 1.
4.  **If all pass**: Continue silently to Phase 1.

## 📊 Phase 0.6: Consistency Check (Lightweight)
> **PURPOSE**: Quick pre-flight to verify artifacts exist. Full alignment analysis is deferred to `/project-check` (normal workflow).
> **NON-BLOCKING**: This phase NEVER stops Act.
1.  **Spec exists?**: Check if `docs/specs/{STORY_ID}.md` exists. If not: WARN "Spec not found".
2.  **Board entry exists?**: Check if `{STORY_ID}` appears in `docs/product/sprint_board.md`. If not: WARN "Board entry not found".
3.  **Move to In Progress**: If `{STORY_ID}` is found on the board, move it to In Progress section.
4.  **Continue**: Regardless of findings, proceed to Phase 1.

## 🎬 Phase 1: Precision Targeting
1.  **Targeted Visual Scan**: Run `visualize --focus <module>` only (single targeted mode). For large codebases, add `--depth 2`. Do NOT run full 3-mode visualize here — that is handled by Phase 4 Lazy Visualize after implementation.
2.  **Trace Verification** — use pactkit-trace skill:
    - Before touching any code, confirm the call site and ensure you don't break existing callers.
3.  **Topology-Aware Trace (Conditional)** — if `detect_topology(root)` includes `api_call` or `agent`:
    - For **api_call**: Run `api_convention_summary(root)` to check API path prefixes and fetch function conventions. Use these conventions when writing new API calls to maintain consistency.
    - For **agent**: Check AgentParser output for orchestration edges so new code doesn't break agent flow.

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
3.  **Regression Check (Read-Only Gate)**: After the TDD loop is GREEN, run the project's test suite as a broader regression check.
    - Run `pactkit regression` (uses `git diff` + `LANG_PROFILES` to classify: SKIP/FULL/IMPACT). Doc-only changes are auto-skipped.
    - If IMPACT: run `pactkit test-map <changed-files>` for incremental test selection. If any changed file has 3+ importers in `code_graph.mmd`, run full suite. Fallback: full suite.
    - **CRITICAL — Pre-existing test failure protocol**: If a pre-existing test fails, **DO NOT modify** it. **STOP** and report to the user. This is a one-shot check, not an iterative loop.
4.  **Lint Gate**: Run `pactkit lint` to check code style. If lint errors are found, fix them before proceeding. If `pactkit lint` is unavailable, run the stack's lint command directly.

## 🎬 Phase 4: Sync & Document
1.  Run `pactkit clean` and `pactkit visualize --lazy` (runs file, `--mode class`, `--mode call` if source changed).
2.  **Update Board (CRITICAL)**: Run `{BOARD_CMD} update_task {STORY_ID} "Task Name"` for each completed task to mark it as `[x]`.
3.  **Update Continuation State**: Run `pactkit context --continuation --last-command "/project-act {STORY_ID}" --phase "Phase 4: complete"` to record the agent's stopping point for session handoff.
