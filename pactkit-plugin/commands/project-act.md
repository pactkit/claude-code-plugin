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
    - Do not implement the contradictory requirement. Continue safe investigation and collect the evidence needed to resolve it; do not write source code whose behavior depends on that unresolved requirement.
    - **Report** to the user: (a) quote the exact problematic requirement from the Spec, (b) explain why it is infeasible (technical reasoning), (c) suggest an alternative approach.
    - You MUST NOT modify the Spec unilaterally — only the user (or Architect via a new `/project-plan` cycle) may amend Tier 1.
    - Wait for user guidance before proceeding.
3.  **Locate Target**: Which file/function needs surgery?
4.  **Detect Stack & Select Stack Reference**: Identify the project type from source files (`.py`, `.ts`/`.tsx`, `.go`, `.java`). Apply the corresponding language-specific best practices throughout implementation and testing.
5.  **Memory MCP (Conditional)**: IF Memory MCP is available, use search_nodes to load prior context for {STORY_ID} — retrieve architectural decisions and design rationale from the Plan phase.

## 🛡️ Phase 0.5: Spec Lint Gate (MUST)
<!-- PACTKIT_ACT_OP:spec_lint -->
> **PURPOSE**: Non-AI structural validation — ensures "Spec is Law" has physical enforcement before any code is written.
1.  **Run Linter**: Execute the Spec Linter on the current Story's spec:
    ```bash
    pactkit spec-lint docs/specs/{STORY_ID}.md
    ```
    If `pactkit` is not on `$PATH`, use `python3 -m pactkit spec-lint docs/specs/{STORY_ID}.md` instead.
    Replace `{STORY_ID}` with the actual Story ID from `$ARGUMENTS` (e.g., `STORY-042`).
2.  **If ERRORs found**: Output all ERROR and WARN items and mark phase completion as incomplete. Fix the Spec where authorized, or continue safe read-only investigation; do not create a permanent workflow lock or require a new session.
3.  **If WARNs only**: Output the WARN list, then **continue** to Phase 1.
4.  **If all pass**: Continue silently to Phase 1.

## 📊 Phase 0.6: Consistency Check (Lightweight)
> **PURPOSE**: Quick pre-flight to verify artifacts exist. Full alignment analysis is deferred to `/project-check` (normal workflow).
> **NON-BLOCKING**: This phase NEVER stops Act.
1.  **Spec exists?**: Check if `docs/specs/{STORY_ID}.md` exists. If not: WARN "Spec not found".
2.  **Story record exists?**: Run `pactkit board list` and check `{STORY_ID}`. Treat `sprint_board.md` as a projection only.
3.  **Move to In Progress**: If `{STORY_ID}` is found on the board, run `{BOARD_CMD} move_story "{STORY_ID}" "in_progress"`.
4.  **Continue**: Regardless of findings, proceed to Phase 1.

## 🧾 Phase 0.7: Spec Input Preflight (MUST)
> **PURPOSE**: Deterministically place referenced implementation inputs and constraints in the current context before any source edit.
1. Run `pactkit spec-preflight docs/specs/{STORY_ID}.md` in the current session.
2. Review the emitted file excerpts, CSS custom properties, interfaces, and MUST/NEVER/禁止/必须/对齐 constraints before writing code.
3. If a required input is missing, ambiguous, outside the project root, or exceeds its extraction budget, mark completion incomplete and fix the declaration where authorized. Safe reading, diagnosis and repair remain available.
4. Continue directly to Phase 1 in this session; a new session is never required.

## 🎬 Phase 1: Precision Targeting
0.  **Previous-session context (optional)**: You MAY read the Agent Continuation section of the local `.pactkit/context.md` (if present) for handover notes from an earlier session. It is never an execution gate: a stale, missing, or empty section does not prevent this session from implementing and verifying the current Story.
1.  **Provider-Routed Scan**: Run `pactkit query --explore <module> --json --explain`. Record the complete provider decision in preflight evidence. Do not invoke Codegraph, visualize, SQLite or `rg` directly; `--allow-fallback` must be explicit and auditable.
2.  **Trace Verification** — use pactkit-trace skill:
    - Run `pactkit query --chain <symbol> --json --explain`; confirm the call site and existing callers before editing.
3.  **Interface Summary (Code Enforce)** — for non-target modules discovered by trace:
    - Run `pactkit interface-summary <file>` for each related module you do NOT plan to modify.
    - This outputs signatures + types + docstrings only (function bodies excluded by code).
    - Only escalate to full `Read <file>` when you confirm the module needs modification.
    - If `pactkit` is not on `$PATH`, use `python3 -m pactkit interface-summary <file>`.
4.  **Topology-Aware Trace (Conditional)** — if `detect_topology(root)` includes `api_call` or `agent`:
    - For **api_call**: Run `api_convention_summary(root)` to check API path prefixes and fetch function conventions. Use these conventions when writing new API calls to maintain consistency.
    - For **agent**: Check AgentParser output for orchestration edges so new code doesn't break agent flow.
5.  **Solution Design Protocol (Conditional)** — if the implementation involves frameworks already used by the project:
    - Execute the **Capability Design** module from `{SKILLS_ROOT}/_rules/design/capability-design.md` to evaluate capability delta before writing code.
    - Output brief capability assessment before proceeding to Phase 1.5.

## 🔧 Phase 1.5: Engineering Concerns Loading (Conditional)
> **PURPOSE**: Load only the NFR guides relevant to this Story — keeps context minimal while ensuring engineering rigor.
1.  **Read Spec Technical Design**: Check if the Spec contains engineering concern decisions (from Plan Phase 2).
2.  **Identify concerns**: Extract the concern keywords mentioned (e.g., database, api-integration, resilience). Reference `{SKILLS_ROOT}/_rules/engineering/index.md` for the keyword→guide mapping table.
3.  **Load guides**: For each identified concern, read the corresponding guide file from `{GUIDES_PATH}/`:
    - MUST load only 1-3 relevant guides (those matching the Spec's concerns).
    - NEVER load all 13 guides.
    - If Spec has no engineering concerns section, skip this phase silently.
4.  **Apply decisions**: Use the loaded guides as risk-driven decision support. Their hard-safety notes are non-negotiable; defaults may be changed with project evidence.
5.  **Output checkpoint**: `"Engineering guides loaded: {list}. Applying as implementation constraints."`

## 🎬 Phase 2: Test Scaffolding (TDD)
<!-- PACTKIT_ACT_OP:tdd_red_green -->
1.  **Constraint**: NEVER write source code in this phase — doing so breaks TDD causality: tests must exist before the code they verify.
2.  **Action**: Create a reproduction test case in `tests/unit/`.
    - Use the knowledge from Phase 1 to mock/stub dependencies correctly.
3.  **Optional handover note**: After confirming RED, you may record a local handover note via `pactkit context --continuation` (see Phase 4 step 3). It must never be required to continue the TDD loop.

## 🎬 Phase 3: Implementation
1.  **Write Code**: Implement logic in the appropriate source directory.
    - **Context7 (Conditional)**: IF implementing with an unfamiliar library API, use Context7 MCP to fetch up-to-date documentation before writing code.
2.  **TDD Loop (Safe Iteration)**: Run ONLY the tests created in Phase 2. Loop until GREEN.
    - Do NOT include pre-existing tests in this loop.
    - Reassess the approach after several unsuccessful iterations, but keep investigating and repairing in the current session while progress is possible.
    - **Environment Failure Bailout**: For environment errors (`ModuleNotFoundError`, `ImportError`, `ConnectionError`, `ConnectionRefusedError`, `PermissionError`, timeout):
      - **Project-internal check first**: If the missing module is project-internal (part of your codebase): NOT a bailout — do not modify source code for env issues, go back and implement it.
      - If third-party: inspect the dependency and attempt a safe resolution (for example, `pip install` only when it is the project's approved dependency-install command). If it remains unavailable, clearly report the environmental limitation and continue any work that can be verified locally.
    - After GREEN, optionally record a local handover note (`pactkit context --continuation`).
3.  **Regression Check (Read-Only Gate)**: After the TDD loop is GREEN, run the project's test suite as a broader regression check.
    <!-- PACTKIT_ACT_OP:regression_classification -->
    - Run `pactkit regression` (uses `git diff` + `LANG_PROFILES` to classify: SKIP/FULL/IMPACT). Doc-only changes are auto-skipped.
    - If IMPACT: run `pactkit test-map <changed-files>` for incremental test selection. Query importers through `pactkit query --callers <file> --json --explain`; if any changed file has 3+ importers, run full suite. Fallback is allowed only through router policy.
    - **Pre-existing test failure protocol**: Do not casually modify an unrelated failing test. Diagnose whether the Story caused it; fix it when the causal path is understood, otherwise report it as a QA gap while continuing all safe, relevant Story work.
4.  **Lint Gate**: Run `pactkit lint` to check code style. If lint errors are found, fix them before proceeding. If `pactkit lint` is unavailable, run the stack's lint command directly.
    <!-- PACTKIT_ACT_OP:lint -->
    - After regression and lint pass, optionally record a local handover note (`pactkit context --continuation`).
5.  **Hardcode Self-Check (STORY-slim-105)**: Review the code you just wrote for hardcoded values:
    - URLs (`http://`, `https://`) that should be config
    - Magic numbers (non-obvious integers like `30000`, `8080`) that should be named constants
    - Environment-specific paths that should be parameterized
    - If found, extract to config/constants before proceeding.

## 🎬 Phase 4: Sync & Document
1.  Run `pactkit clean` and `pactkit visualize --lazy` (runs file, `--mode class`, `--mode call` if source changed; codegraph sync is handled automatically).
    <!-- PACTKIT_ACT_OP:graph_sync -->
1b. **Journey Sync (Conditional)**:
    - **Skip if**: `docs/e2e/journey.md` does not exist in the project.
    - **Skip if**: Current Story's Spec has no `## Journey Segment` section.
    - **If triggered**:
      1. Read `docs/e2e/journey.md`
      2. Locate the journey step(s) referenced in the Spec's `## Journey Segment` (format: `- Journey: {Name}` / `- Steps: {N}` / `- Impact: {desc}`)
      3. Review: do the step assertions still hold after this Story's code changes?
      4. If outdated: Edit the affected step(s) in journey.md — update assertions, add new structure assertions, or adjust step description. MUST use Edit (incremental), MUST NOT use Write (full replace).
      5. If still accurate: skip with log "Journey steps verified — no update needed"
2.  **Update Board (CRITICAL)**: Run `{BOARD_CMD} update_task {STORY_ID} "Task Name"` for each completed task to mark it as `[x]`.
    Mid-story additions use `{BOARD_CMD} add_task {STORY_ID} "Task Name"` (subcommands: add_story, add_task, update_task, snapshot, move_story, archive, list_stories, fix_board, render).
    <!-- PACTKIT_ACT_OP:board_update -->
3.  **Update local context (optional)**: You may run `pactkit context --continuation --last-command "/project-act {STORY_ID}" --phase "Phase 4: complete"` for a later handoff.
    <!-- PACTKIT_ACT_OP:continuation_update -->
4.  **Coverage Table Output (STORY-slim-105)**: Output a coverage table listing each R{N} from the Spec:
    <!-- PACTKIT_ACT_OP:requirement_coverage -->

    | Spec 条目 | 类型 | 状态 | 位置 |
    |-----------|------|------|------|
    | R1 xxx | MUST | ✓ | file.py:line |
    | R2 xxx | SHOULD | DEFERRED | — reason |

    - For implemented items: show file:line location
    - For skipped SHOULD items: show DEFERRED with reason (must match comment in code)
    - User verifies this table — do not claim "done" without it
5.  **Honest completion report**: Only claim completed items after the coverage table, Story tests, regression, lint, and Board tasks have been verified. A local handover note is optional evidence and must not block a later session.
