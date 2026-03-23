---
description: "Analyze requirements, create Spec and Story"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Plan (v1.3.0 Integrated Trace)
- **Usage**: `/project-plan "$ARGUMENTS"`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go. Do NOT try to plan the entire Spec in your head before producing output. Start each phase, show your findings, then move to the next.
> **Tool Integration Note**: If the request involves adapting PactKit to a new AI coding tool (new `format` value like `codex`, `cursor`, etc.), **always start** by consulting `docs/guides/tool-integration-checklist.md`. Complete Dimension 0 (capability matrix) before writing any code. See also `docs/guides/codex-integration-preresearch.md` for an example pre-research template.

1.  **Analyze Intent**: New feature (Expansion) or Bugfix/Refactor (Modification)?
2.  **Strategy**:
    - If **New Feature**: Focus on `system_design.mmd` (Architecture).
    - If **Modification**: Focus on pactkit-trace skill (Logic Flow).
3.  **Greenfield Detection**: Check if the request is a greenfield product ideation:
    - **Signals**: Keywords like "from scratch", "new app", "startup", "MVP", "product idea", "创业", "从零开始"; multi-story scope ("multiple features", "full system", "complete app"); empty sprint board; no existing source code files.
    - **If greenfield signals are detected**: Suggest to the user: "This looks like a greenfield product design. Consider using `/project-design` instead, which generates a full PRD and decomposes into multiple stories."
    - Ask the user to confirm the redirect. Do NOT auto-redirect.
    - **If user declines**: Proceed with `/project-plan` normally.
    - **If existing project** (stories on board, source files present): Skip this check — greenfield detection does not apply to established projects.

## 🛡️ Phase 0.5: Init Guard (Auto-detect)
1.  Run `pactkit guard` to check init markers (pactkit.yaml via `{PACTKIT_YAML}`, `docs/product/sprint_board.md`, `docs/architecture/graphs/`).
2.  If exit code 1: project is not initialized — print the missing markers and **STOP**. Suggest running `/project-init`.
3.  If all exist: check config completeness (hooks, ci, issue_tracker sections). If stale, run `pactkit update` and report what was added.
4.  If PASS: proceed to Phase 1.

## 🧠 Phase 0.7: Clarify Gate (Auto-detect Ambiguity)
> **PURPOSE**: Surface and resolve requirement ambiguity before the Spec is written. Better to clarify now than rewrite a Spec.
1.  **Detect Ambiguity**: Analyze the user's input (`$ARGUMENTS`) against these signals:
    - [High] No quantitative metrics ("高并发" without QPS, "fast" without benchmark)
    - [High] No boundary conditions ("user management" without specifying which operations)
    - [Medium] No technical constraints (no auth method, no framework specified)
    - [Low] Single sentence input (< 15 words) — likely under-specified but not blocking
    - [Medium] Vague quantifiers ("some", "many", "a few", "大量", "一些", "简单")
    - [Medium] No target user specified
2.  **Trigger Logic**:
    - 2 High + ≥ 1 Medium signals → **Auto-trigger** Clarify
    - ≥ 2 High signals (no Medium) → **Suggest** Clarify (ask user: "Input may be underspecified. Clarify? yes/skip")
    - 1 High + ≥ 2 Medium signals → **Suggest** Clarify
    - Otherwise → **Silent skip**
3.  **Greenfield Force-Trigger**: If Phase 0 detected a Greenfield project and the user chose to continue with `/project-plan` (not `/project-design`), **always trigger** Clarify regardless of score.
4.  **If triggered**: Generate 3–6 structured questions covering:
    - **Scope**: "What specific operations are included? Please list them."
    - **Users**: "Who is the target user? Are there multiple roles?"
    - **Constraints**: "Any technical constraints? (required framework, compatibility requirements)"
    - **Scale**: "Expected data volume / concurrency / user count?"
    - **Edge Cases**: "What should happen when [failure scenario]?"
    - **Non-Goals**: "What is explicitly NOT in scope?"
    - Ask questions in the user's language (Language Matching rule).
5.  **User Response**:
    - User answers all/some → merge into `enriched_input`; proceed to Phase 1 with `enriched_input`
    - User inputs "skip" or declines → proceed with original input (Clarify MUST NOT block Plan)
6.  **Output**: The enriched_input (original + answers) is used as context for Phase 1 onwards.

## 🎬 Phase 1: Archaeology (The "Know Before You Change" Step)
> **Subagent Scope Rule**: When delegating research to an Explore subagent, always provide a **bounded** prompt: target function/class, directory scope, file limit, and expected output. Never delegate open-ended "trace the whole codebase" tasks.

1.  **Visual Scan**: Run `visualize --focus <module> --depth 2` to see the targeted dependency graph. Only expand to `--mode class` or `--mode call` if the focused scan is insufficient.
2.  **Logic Trace (CRITICAL)** — use pactkit-trace skill:
    - If modifying existing logic, trace the current implementation.
    - *Goal*: Identify the exact function/class responsible for the logic.
    - **Delegation Template**: When using an Explore subagent for trace, formulate the prompt with:
      - **Target**: specific function or class name to trace
      - **Scope**: specific directory (e.g., `src/pactkit/generators/`)
      - **Limit**: read at most 8-10 files
      - **Output**: what to return (entry file, call chain, key data transformations)
      - Example: `Agent(subagent_type="Explore", prompt="Find the deploy() entry point in src/pactkit/generators/deployer.py. Trace the call chain to file writes. Read at most 8 files. Return: entry function, call chain list, key data transformations.")`

## 🎬 Phase 2: Design & Impact
1.  **Diff**: Compare User Request vs Current Reality (from Phase 1).
2.  **Update HLD**: Modify `docs/architecture/graphs/system_design.mmd`.
    - *Rule*: Keep the `code_graph.mmd` as is (it updates automatically).

## 🎬 Phase 3.1: Story ID Generation
1.  Run `pactkit next-id` to get the next Story ID (reads developer prefix from pactkit.yaml, scans `docs/specs/`).
2.  **Output checkpoint**: Print "Story ID determined: {ID}. Writing Spec now."

## 🎬 Phase 3.2a: Spec Skeleton (Metadata + Requirements)
1.  **Create file**: Create `docs/specs/{ID}.md` with the following sections:
    - **MUST — Metadata Table**: Include a metadata table at the top using this EXACT format:
      ```markdown
      | Field | Value |
      |-------|-------|
      | ID | {ID} |
      | Status | Draft |
      | Priority | P2 |
      | Release | {version} |
      ```
      Field names MUST be exact case (ID, Status, Priority, Release) — not bold, not different names.
    - **MUST**: Fill in the `Release` metadata field by reading the `version` field from `{PACTKIT_YAML}` or `pyproject.toml`. Use that EXACT value — do NOT increment or predict a future version. If the file cannot be read, use `TBD`.
    - **MUST**: Include `## Background` and `## Target Call Chain` sections based on your Trace findings.
    - **MUST**: Fill in the `## Requirements` section using RFC 2119 keywords (MUST/SHOULD/MAY).
2.  **Output checkpoint**: Print "Spec skeleton written. Adding acceptance criteria."

## 🎬 Phase 3.2b: Acceptance Criteria & Implementation Steps
1.  **MUST**: Add `## Acceptance Criteria` section with Given/When/Then scenarios.
    - Each Scenario SHOULD map to a verifiable test case in `docs/test_cases/`.
2.  **OPTIONAL — Implementation Steps**: If Phase 1 Trace identifies 2+ files to modify, add `## Implementation Steps` section with table format:
    ```
    | Step | File | Action | Dependencies | Risk |
    |------|------|--------|--------------|------|
    | 1 | `src/foo.py` | Description | None | Low |
    ```
    The `Dependencies` column accepts `None`, `Step N`, or comma-separated step references. The `Risk` column accepts `Low`, `Medium`, `High`.
3.  **Output checkpoint**: Print "Acceptance criteria written. Running security scope."

## 🎬 Phase 3.2c: Security Scope
1.  **MUST**: Run `pactkit sec-scope <changed-files>` to auto-detect SEC-1~SEC-8 applicability. Append the output to `## Security Scope` in the Spec.
2.  **Fallback**: If `pactkit sec-scope` is unavailable, manually assess each SEC-1 through SEC-8 check based on changed file paths and code patterns. Apply docs/tests-only shortcut if applicable (mark ALL N/A with Reason "docs/tests only").
3.  **Output format** (the table must include a Reason column):
    ```markdown
    ## Security Scope
    | Check | Applicable | Reason |
    |-------|------------|--------|
    | SEC-1 | Yes | Source code modified |
    | SEC-2 | N/A | No user input handling |
    ```
4.  **Output checkpoint**: Print "Security scope appended. Running lint."

## 🎬 Phase 3.2d: Spec Lint Self-Check
1.  Run `pactkit spec-lint docs/specs/{ID}.md`.
2.  If ERROR rules fail, self-correct the Spec immediately (you wrote it — you have authority to fix it). Re-run until clean.
3.  This prevents the Spec from being rejected at Act Phase 0.5.
4.  **Output checkpoint**: Print "Spec lint passed."

## 🎬 Phase 3.3: Board, Memory & Handover
1.  **Board**: Add Story using `add_story`.
2.  **Memory MCP (Conditional)**: IF Memory MCP is available, use create_entities to store design context (decisions, target files, rationale) under entity `{STORY_ID}`. Record story dependencies if applicable.
3.  **Session Context Update**: Run `pactkit context` to generate `docs/product/context.md`. Set "Last updated by" to `/project-plan`.
4.  **Handover**: "Trace complete. Spec created. Ready for Act."
