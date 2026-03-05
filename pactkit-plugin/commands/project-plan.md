---
description: "Analyze requirements, create Spec and Story"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Plan (v1.3.0 Integrated Trace)
- **Usage**: `/project-plan "$ARGUMENTS"`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process (Mandatory)
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
> **INSTRUCTION**: Check if the project has been initialized before proceeding.
1.  **Check Markers**: Verify the existence of ALL three:
    - `.claude/pactkit.yaml` (project-level config)
    - `docs/product/sprint_board.md` (sprint board)
    - `docs/architecture/graphs/` (architecture graph directory)
2.  **If ANY marker is missing**:
    - Print: "⚠️ Project not initialized. Running `/project-init` first..."
    - Execute the full `/project-init` flow to scaffold the missing structure.
    - After `/project-init` completes, resume this Plan command from Phase 1.
3.  **If ALL markers exist**: Proceed to Step 4.
4.  **Config Completeness Check**: Verify `pactkit.yaml` has all expected sections (hooks, ci, issue_tracker, lint_blocking, auto_fix).
    - If any sections are missing, the config is stale. Run `pactkit update` to backfill missing sections.
    - Report what was added (e.g., "Config refreshed: added hooks, ci sections").
    - If the config is already complete and up to date, skip silently to Phase 1.

## 🧠 Phase 0.7: Clarify Gate (Auto-detect Ambiguity)
> **PURPOSE**: Surface and resolve requirement ambiguity before the Spec is written. Better to clarify now than rewrite a Spec.
1.  **Detect Ambiguity**: Analyze the user's input (`$ARGUMENTS`) against these signals:
    - [High] No quantitative metrics ("高并发" without QPS, "fast" without benchmark)
    - [High] No boundary conditions ("user management" without specifying which operations)
    - [Medium] No technical constraints (no auth method, no framework specified)
    - [Medium] Single sentence input (< 15 words) — likely under-specified
    - [Medium] Vague quantifiers ("some", "many", "a few", "大量", "一些", "简单")
    - [Medium] No target user specified
2.  **Trigger Logic**:
    - ≥ 2 High signals (no metrics, no boundaries) → **Auto-trigger** Clarify
    - 1 High + ≥ 2 Medium signals → **Auto-trigger** Clarify
    - ≥ 2 Medium signals → **Suggest** Clarify (ask user: "Input seems underspecified. Clarify? yes/skip")
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
1.  **Visual Scan**: Run `visualize` to see the module dependency graph. Use `--mode class` for structure, `--mode call` for logic.
    - For large codebases (50+ files), use `--focus <module> --depth 2` to limit scope.
2.  **Logic Trace (CRITICAL)** — use pactkit-trace skill:
    - If modifying existing logic, trace the current implementation.
    - *Goal*: Identify the exact function/class responsible for the logic.

## 🎬 Phase 2: Design & Impact
1.  **Diff**: Compare User Request vs Current Reality (from Phase 1).
2.  **Update HLD**: Modify `docs/architecture/graphs/system_design.mmd`.
    - *Rule*: Keep the `code_graph.mmd` as is (it updates automatically).

## 🎬 Phase 3: Deliverables
1.  **Spec**: Create `docs/specs/{ID}.md` detailing the *Change*.
    - *Requirement*: Include a "Target Call Chain" section in the Spec based on your Trace findings.
    - **MUST**: Fill in the `## Requirements` section using RFC 2119 keywords (MUST/SHOULD/MAY).
    - **MUST**: Fill in the `## Acceptance Criteria` section with Given/When/Then scenarios.
    - Each Scenario SHOULD map to a verifiable test case in `docs/test_cases/`.
    - **MUST**: Fill in the `Release` metadata field by reading the `version` field from `.claude/pactkit.yaml` (or `pyproject.toml`). Use that EXACT value — do NOT increment or predict a future version. If the file cannot be read, use `TBD`.
    - **OPTIONAL — Implementation Steps**: If Phase 1 Trace identifies 2+ files to modify, add `## Implementation Steps` section with table format:
      ```
      | Step | File | Action | Dependencies | Risk |
      |------|------|--------|--------------|------|
      | 1 | `src/foo.py` | Description | None | Low |
      ```
      The `Dependencies` column accepts `None`, `Step N`, or comma-separated step references. The `Risk` column accepts `Low`, `Medium`, `High`. This section is optional but RECOMMENDED for multi-file changes.
    - **MUST — Security Scope**: Add `## Security Scope` section to the Spec based on the changed files identified in Phase 1 Trace. Use these detection rules:
      | Check | Applicable When |
      |-------|-----------------|
      | SEC-1 | Any source code file modified (`.py`, `.js`, `.ts`, `.go`, `.java`, etc.) |
      | SEC-2 | Code contains `request.`, `form.`, `input`, `argv`, `sys.stdin`, `process.argv` |
      | SEC-3 | Files in `models/`, `dao/`, `repository/`; or code contains `SELECT`, `INSERT`, `UPDATE`, `DELETE`, ORM patterns |
      | SEC-4 | Frontend files (`.tsx`, `.vue`, `.svelte`, `.html`); or code contains `innerHTML`, `dangerouslySetInnerHTML`, template rendering |
      | SEC-5 | Files in `auth/`, `session/`, `login/`; or code contains `token`, `jwt`, `cookie`, `session` |
      | SEC-6 | Files in `api/`, `routes/`, `endpoints/`, `controllers/`; or new public endpoints added |
      | SEC-7 | Files in `api/`, `routes/`; or code contains exception handling patterns |
      | SEC-8 | Dependency files modified (`package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`) |

      **Docs/tests-only shortcut**: If ONLY files matching `docs/**`, `tests/**`, `*.md`, `README*` are modified, mark ALL checks N/A with reason "docs/tests only".

      Output format in the Spec:
      ```markdown
      ## Security Scope
      | Check | Applicable | Reason |
      |-------|------------|--------|
      | SEC-1 | Yes | Source code modified |
      | SEC-2 | No | No user input handling |
      | SEC-3 | Yes | models/user.py modified |
      ```
    - **Spec Lint Self-Check**: After writing the Spec, run `pactkit spec-lint docs/specs/{ID}.md`. If ERROR rules fail, self-correct the Spec immediately (you wrote it — you have authority to fix it). Re-run until clean. This prevents the Spec from being rejected at Act Phase 0.5.
2.  **Board**: Add Story using `add_story`.
3.  **Memory MCP (Conditional)**: IF Memory MCP is available, use create_entities to store design context (decisions, target files, rationale) under entity `{STORY_ID}`. Record story dependencies if applicable.
4.  **Session Context Update**: Update `docs/product/context.md` using the Context.md Canonical Format (see Shared Protocols). Set "Last updated by" to `/project-plan`.
5.  **Handover**: "Trace complete. Spec created. Ready for Act."
