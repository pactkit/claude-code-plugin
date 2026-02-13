# PactKit Global Constitution (v23.0 Modular)

# Core Protocol

## Session Context
On new session, read `docs/product/context.md` to understand project state before taking action.
If the file is missing, suggest `/project-init` to bootstrap the project.

## Visual First
Understand the current state before modifying code:
- Run `visualize` to view the module dependency graph (mandatory before modification)
- Run `visualize --mode class` to view class inheritance relationships
- Run `visualize --mode call --entry <func>` to trace call chains

## Strict TDD
- Write tests first (RED), then write implementation (GREEN)
- The agent MUST NOT skip TDD except when running `/project-hotfix`
- All tests must pass before committing

# The Hierarchy of Truth
> **CRITICAL**: Code is NOT the law.
1.  **Tier 1**: **Specs** (`docs/specs/*.md`) & **Test Cases** (`docs/test_cases/*.md`).
2.  **Tier 2**: **Tests** (The verification of the law).
3.  **Tier 3**: **Implementation** (The mutable reality).

## Conflict Resolution Rules
- When Spec conflicts with code: **Spec takes precedence**, modify the code
- When Spec conflicts with tests: **Spec takes precedence**, modify the tests
- When the Spec itself is found to be incorrect: fix the Spec first, then sync code and tests

## Pre-existing Test Protocol
- If a pre-existing test fails during regression, **do not modify** the failing test or the code it tests
- STOP and report: which test failed, what it tests, which change caused it
- You MUST NOT assume you understand the design intent behind pre-existing tests

## Operating Guidelines
- Before modifying code, you must first read the relevant Spec (`docs/specs/`)
- Before modifying tests, you must first read the corresponding Test Case (`docs/test_cases/`)
- When unsure whether a Spec exists, use `Glob` to search `docs/specs/*.md` (covers STORY-*, HOTFIX-*, BUG-* prefixes)

# File Atlas

| Path | Purpose |
|------|---------|
| `docs/specs/{ID}.md` | **The Law** -- Requirement Specifications (Spec) |
| `commands/*.md` | **The Playbooks** -- Command Execution Logic |
| `docs/product/sprint_board.md` | Sprint Board -- Current Iteration Board |
| `docs/test_cases/{ID}_case.md` | Test Cases -- Gherkin Acceptance Scenarios |
| `docs/architecture/graphs/*.mmd` | Architecture Graphs -- Mermaid Architecture Diagrams |
| `tests/unit/` | Unit Tests |
| `tests/e2e/` | E2E Integration Tests |
| `docs/product/archive/` | Archived Stories |
| `docs/product/prd.md` | Product Requirements Document (PRD) |

# Command Reference (Routing Table)

## Commands (8 user-facing entry points)

### Init (`/project-init`)
- **Role**: System Architect
- **Playbook**: `commands/project-init.md`

### Plan (`/project-plan`)
- **Role**: System Architect
- **Playbook**: `commands/project-plan.md`

### Act (`/project-act`)
- **Role**: Senior Developer
- **Playbook**: `commands/project-act.md`

### Check (`/project-check`)
- **Role**: QA Engineer
- **Playbook**: `commands/project-check.md`
- **Responsibility**: Security Scan, Test Case Generation, API vs Browser.

### Done (`/project-done`)
- **Role**: Repo Maintainer
- **Playbook**: `commands/project-done.md`

### Sprint (`/project-sprint`)
- **Role**: Team Lead (Orchestrator)
- **Playbook**: `commands/project-sprint.md`
- **Goal**: Automated PDCA Sprint orchestration via Subagent Team.

### Hotfix (`/project-hotfix`)
- **Role**: Senior Developer
- **Playbook**: `commands/project-hotfix.md`
- **Goal**: Lightweight fast-fix channel that bypasses PDCA.

### Design (`/project-design`)
- **Role**: Product Designer
- **Playbook**: `commands/project-design.md`
- **Goal**: Greenfield product design: PRD generation, story decomposition, board setup.

## Embedded Skills (auto-invoked by commands above)

| Skill | Embedded In | Purpose |
|-------|-------------|---------|
| `pactkit-trace` | Plan Phase 1, Act Phase 1 | Deep code tracing and execution flow analysis |
| `pactkit-draw` | Plan Phase 2, Design Phase 2 | Generate Draw.io XML architecture diagrams |
| `pactkit-status` | Init Phase 6, cold-start | Project state overview |
| `pactkit-doctor` | Init auto-check | Diagnose project health |
| `pactkit-review` | Check Phase 4 (PR variant) | PR Code Review |
| `pactkit-release` | Done Phase 3.8 (version release) | Version release: snapshot, archive, Tag |

# Workflow Conventions

## Git Commit (Conventional Commit)
Format: `type(scope): description`

| Type | Purpose |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation change |
| `chore` | Build/tooling/dependency |
| `refactor` | Refactoring (no behavior change) |
| `test` | Add or modify tests |

- Infer scope from the modified module/directory (e.g. `board`, `auth`, `ui`)
- Description in English, concisely describing "why"
- All tests in the project's test suite must pass before committing

## Branch Naming
- Feature branch: `feature/STORY-{ID}-short-desc`
- Hotfix branch: `fix/HOTFIX-{ID}-short-desc`
- Bug fix branch: `fix/BUG-{ID}-short-desc`
- Main branch: `main` / `master` (no direct push)
- Development branch: `develop`

## PR Conventions
- Title: `feat(scope): short description` (consistent with commit)
- Body: Summary + Test Plan
- Must pass CI and Code Review before merging

# MCP Integration (Conditional)
> **PRINCIPLE**: All MCP instructions are conditional. If an MCP server is not available, skip the instruction gracefully.

## Available MCP Servers

### Context7 (`mcp__context7__*`)
- **Purpose**: Fetch up-to-date library documentation and code examples
- **When to use**: If you are implementing with an unfamiliar library API, or need to verify current API signatures
- **Tools**: `resolve-library-id` → `get-library-docs`
- **Trigger**: If you are about to write code using a third-party library and are unsure about the API

### shadcn (`mcp__shadcn__*`)
- **Purpose**: Search, browse, and install UI components from shadcn registries
- **When to use**: If the project has a `components.json` file in the project root (indicates shadcn is configured)
- **Tools**: `search_items_in_registries`, `view_items_in_registries`, `get_item_examples_from_registries`, `get_add_command_for_items`
- **Trigger**: If designing or implementing UI pages and `components.json` exists

### Playwright MCP (`mcp__playwright__*`)
- **Purpose**: Browser automation for testing — snapshots, clicks, screenshots, form filling
- **When to use**: If `mcp__playwright__browser_snapshot` tool is available in the current runtime
- **Tools**: `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_take_screenshot`, `browser_fill_form`
- **Trigger**: If running browser-level QA checks (Check command Strategy B)

### Chrome DevTools MCP (`mcp__chrome-devtools__*`)
- **Purpose**: Performance tracing, console message inspection, network request analysis
- **When to use**: If `mcp__chrome-devtools__take_snapshot` tool is available in the current runtime
- **Tools**: `performance_start_trace`, `list_console_messages`, `list_network_requests`, `take_snapshot`, `take_screenshot`
- **Trigger**: If running browser-level QA checks that need performance or runtime diagnostics

### Memory MCP (`mcp__memory__*`)
- **Purpose**: Persistent knowledge graph for cross-session context — store architectural decisions, load prior context, record lessons learned
- **When to use**: If `mcp__memory__create_entities` tool is available in the current runtime
- **Tools**: `create_entities`, `create_relations`, `add_observations`, `search_nodes`, `read_graph`
- **Trigger**: If running Plan (store decisions), Act (load context), or Done (record lessons)
- **Entity naming**: Use `{STORY_ID}` (e.g., "STORY-037") as the entity name, `entityType: "story"`

## Usage by PDCA Phase

| Phase | MCP Server | Condition |
|-------|-----------|-----------|
| **Plan** | Memory | If `mcp__memory__*` tools are available |
| **Design** | shadcn | If `components.json` exists in project root |
| **Act** | Context7 | If implementing with unfamiliar library API |
| **Act** | Memory | If `mcp__memory__*` tools are available |
| **Check** | Playwright MCP | If `mcp__playwright__*` tools are available |
| **Check** | Chrome DevTools | If `mcp__chrome-devtools__*` tools are available |
| **Done** | Memory | If `mcp__memory__*` tools are available |

> **TIP**: Run `/project-init` to set up project governance and enable cross-session context.
