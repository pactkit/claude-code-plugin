---
description: "Analyze requirements, create Spec and Story"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Plan (v1.3.0 Integrated Trace)
- **Usage**: `/project-plan "$ARGUMENTS"`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block.
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

## 🎬 Phase 1: Archaeology (The "Know Before You Change" Step)
1.  **Visual Scan**: Run `visualize` to see the module dependency graph.
    - **Mode Selection**: Use `--mode class` for structure analysis, `--mode call` for logic modification, default for overview.
    - **Large Codebase Heuristic**: If the project has more than 50 source files, use `--focus <module> --depth 2` instead of a full graph to avoid context window pollution.
2.  **Logic Trace (CRITICAL)** — use pactkit-trace skill:
    - If modifying existing logic, trace the current implementation:
      Use `Grep` to locate entry points, then `visualize --mode call --entry <func>` to map call chains.
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
    - **MUST**: Fill in the `Release` metadata field with the current version from `pactkit.yaml` (or leave `TBD` if unknown).
2.  **Board**: Add Story using `add_story`.
3.  **Memory MCP (Conditional)**: IF `mcp__memory__create_entities` tool is available, store the design context:
    - Use `mcp__memory__create_entities` with: `name: "{STORY_ID}"`, `entityType: "story"`, `observations: [key architectural decisions, target files, design rationale]`
    - IF this story depends on other stories, use `mcp__memory__create_relations` to record dependencies (e.g., `from: "{STORY_ID}", to: "STORY-XXX", relationType: "depends_on"`)
4.  **Issue Tracker (Conditional)**: IF `pactkit.yaml` has `issue_tracker.provider: github`:
    - Check if `gh` CLI is available (run `gh --version`)
    - If available: create a GitHub Issue with `gh issue create --title "STORY-XXX: Title" --body "Requirements summary"`
    - Update the Sprint Board entry to include the issue URL
    - If `gh` CLI is unavailable or issue creation fails: print warning, continue without issue link
    - If `issue_tracker.provider: none` or section missing: skip silently
5.  **Session Context Update**: Update `docs/product/context.md` to reflect the new Story:
    - Read `docs/product/sprint_board.md` (now containing the new Story)
    - Read `docs/architecture/governance/lessons.md` (last 5 entries)
    - Run `git branch --list 'feature/*' 'fix/*'`
    - Write `docs/product/context.md` using the standard format (see `/project-done` Phase 4.5 for format)
    - Set "Last updated by" to `/project-plan`
6.  **Handover**: "Trace complete. Spec created. Ready for Act."
