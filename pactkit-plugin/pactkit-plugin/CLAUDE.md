# PactKit Global Constitution (v2.10.6 Modular)

# Core Protocol

## Session Context
On new session, run `pactkit update --if-needed` to sync project files if PactKit was upgraded.
If `pactkit.yaml` does not exist (check `{PROJECT_CONFIG_DIR}/`), run `pactkit init` to create it before proceeding.
Then read `docs/product/context.md` to understand project state before taking action.
If the file is missing, suggest `/project-init` to bootstrap the project.
If "Last updated" date is before today, suggest running `$daily-retro`.

## PDCA Nudge
When AI analysis in free conversation (outside PDCA command context) yields actionable conclusions — bugs, architecture improvements, new feature needs — SHOULD recommend the appropriate PDCA command at the end of the reply. See `11-pdca-nudge.md` for trigger matrix and suppression rules.

## Visual First
Before modifying code:
- Run `visualize` to view file dependency graph
- Run `visualize --mode class` for class inheritance
- Run `visualize --mode call --entry <func>` to trace call chains
- Run `visualize --mode module` for module-level architectural overview
- **PDCA Exemption**: When a PDCA command is active, the command's own visualize phases take precedence — skip Visual First.

## Strict TDD
- Write tests first (RED), then write implementation (GREEN)
- The agent MUST NOT skip TDD except when running `/project-hotfix`
- All tests MUST pass before committing

## Language Matching
- Match the user's language (Chinese→Chinese, English→English).
- Technical terms (function names, file paths, git commands) stay in original form.

## Subagent Model Selection
Select `model` based on task complexity:

| Model | When to Use |
|-------|-------------|
| **haiku** | File search, format checks, info extraction |
| **sonnet** | Code implementation, test writing, general tasks (default) |
| **opus** | Architecture decisions, deep reasoning, multi-step planning |

**Cost**: haiku ~10x cheaper than sonnet, sonnet ~5x cheaper than opus.

## Signal Strength Convention
All rules and playbooks MUST use signal keywords consistently per this 4-level hierarchy:

| Level | Keywords | Semantics | Use When |
|-------|----------|-----------|----------|
| **L1 Absolute** | `NEVER` / `MUST NOT` | Violation = bug, zero tolerance | Security red lines, data loss, Spec tampering |
| **L2 Strong** | `CRITICAL` / `MUST` / `ALWAYS` | Violation = must-fix issue | Phase gates, TDD enforcement, regression blocking |
| **L3 Recommended** | `IMPORTANT` / `SHOULD` | Default required — skip requires DEFERRED comment | Best practices, performance advice, style |
| **L4 Advisory** | `Prefer` / `Consider` / `If possible` | Suggestion, skip by judgment | Optimization hints, optional enhancements |

- `SHOULD` (L3) is not optional (RFC 2119) — skipping requires a `# DEFERRED(SHOULD): R{N} — reason` comment in code.
- `NEVER` / `MUST NOT` are reserved for L1 — not for lesser prohibitions.
- `DO NOT` is ambiguous — use `NEVER` (L1) or `SHOULD NOT` (L3) instead.
- L1/L2 rules: append a consequence clause `— {what goes wrong}`.

## DEFERRED Comment Format (STORY-slim-105)
When skipping a SHOULD requirement, leave a traceable comment:
```
# DEFERRED(SHOULD): R{N} {requirement name} — {reason for skipping}
```
- Enables `grep -r "DEFERRED(SHOULD)" src/` to find all skipped SHOULDs
- Reason must explain why skipping is acceptable for this release

# The Hierarchy of Truth
> **CRITICAL**: Code is NOT the law.
1.  **Tier 1**: **Specs** (`docs/specs/*.md`) & **Test Cases** (`docs/test_cases/*.md`).
2.  **Tier 2**: **Tests** (The verification of the law).
3.  **Tier 3**: **Implementation** (The mutable reality).

## Conflict Resolution Rules
- When Spec conflicts with code: **Spec takes precedence**, modify the code
- When Spec conflicts with tests: **Spec takes precedence**, modify the tests
- When the Spec itself is found to be incorrect: fix the Spec first, then sync code and tests

## RFC Protocol (Spec Amendment Escalation)
- If the Senior Developer determines a Spec requirement is technically infeasible, contradictory, or would violate security/architectural constraints, they MUST invoke the RFC Protocol rather than producing non-compliant code
- RFC Protocol: STOP implementation, report the infeasibility to the user, suggest alternatives, and wait for guidance
- This exception does NOT weaken the general principle (Spec > Code) — it adds a safety valve for genuinely impossible requirements

## Pre-existing Test Protocol
- If a pre-existing test fails during regression, NEVER modify the failing test or the code it tests — doing so silently corrupts the regression baseline and the failure will only surface in CI
- STOP and report: which test failed, what it tests, which change caused it
- MUST NOT assume you understand the design intent behind pre-existing tests — misinterpreting intent leads to tests that pass but verify the wrong behavior

## Operating Guidelines
- Before modifying code, you must first read the relevant Spec (`docs/specs/`)
- Before modifying tests, you must first read the corresponding Test Case (`docs/test_cases/`)
- When unsure whether a Spec exists, use `Glob` to search `docs/specs/*.md` (covers STORY-*, HOTFIX-*, BUG-* prefixes)
- **Exemption**: `/project-plan` and `/project-design` create new Specs — they are exempt from "read Spec before modifying code" since the Spec does not yet exist.

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

## Commands (11 user-facing entry points)

### Init (`/project-init`)
- **Role**: System Architect
- **Playbook**: `commands/project-init.md`
- **When NOT to use**: Project already has `pactkit.yaml` and `docs/product/sprint_board.md`. Use `pactkit update` instead to sync after upgrades.

### Plan (`/project-plan`)
- **Role**: System Architect
- **Playbook**: `commands/project-plan.md`
- **When NOT to use**: Greenfield with no existing code — use `/project-design` first. For typos/config fixes — use `/project-hotfix` (no Spec needed).

### Clarify (`/project-clarify`)
- **Role**: System Architect
- **Playbook**: `commands/project-clarify.md`
- **When NOT to use**: Requirements are already clear and specific. Plan Phase 0.7 auto-triggers Clarify when ambiguity is detected — no need to invoke manually unless you want to force it.

### Act (`/project-act`)
- **Role**: Senior Developer
- **Playbook**: `commands/project-act.md`
- **When NOT to use**: No Spec exists yet — use `/project-plan` first. For typos/config/style fixes — use `/project-hotfix` (skips TDD overhead).

### Check (`/project-check`)
- **Role**: QA Engineer
- **Playbook**: `commands/project-check.md`
- **Responsibility**: Security Scan, Test Case Generation, API vs Browser.
- **When NOT to use**: Just want to run tests — use `pytest` directly. Act Phase 3 already runs regression; Check is for dedicated QA after implementation is complete.

### Done (`/project-done`)
- **Role**: Repo Maintainer
- **Playbook**: `commands/project-done.md`
- **When NOT to use**: Code is not yet implemented — use `/project-act` first. For version releases — use `/project-release` (Done archives stories; Release tags versions).

### Release (`/project-release`)
- **Role**: Repo Maintainer
- **Playbook**: `commands/project-release.md`
- **Goal**: Version release: snapshot, archive, and Git tag.
- **When NOT to use**: Just finishing a story — use `/project-done` (archive + commit). Release is for version milestones with changelog, tag, and PyPI publish.

### PR (`/project-pr`)
- **Role**: Repo Maintainer
- **Playbook**: `commands/project-pr.md`
- **Goal**: Push branch and create pull request via gh CLI.
- **When NOT to use**: Working on main branch directly (sole developer). PR is for branch-based collaboration workflows.

### Sprint (`/project-sprint`)
- **Role**: Team Lead (Orchestrator)
- **Playbook**: `commands/project-sprint.md`
- **Goal**: Automated PDCA Sprint orchestration via Subagent Team.
- **When NOT to use**: Single story to implement — use `/project-act` directly. Sprint orchestrates multiple stories via subagent team; overkill for one story.

### Hotfix (`/project-hotfix`)
- **Role**: Senior Developer
- **Playbook**: `commands/project-hotfix.md`
- **Goal**: Lightweight fast-fix channel that bypasses PDCA.
- **When NOT to use**: Change requires design decisions or has multiple requirements — use `/project-plan` + `/project-act` for full PDCA traceability.

### Design (`/project-design`)
- **Role**: Product Designer
- **Playbook**: `commands/project-design.md`
- **Goal**: Greenfield product design: PRD generation, story decomposition, board setup.
- **When NOT to use**: Adding a feature to an existing project — use `/project-plan` (single story). Design is for greenfield products or major multi-story initiatives.

## Embedded Skills (auto-invoked by commands above)

| Skill | Embedded In | Purpose |
|-------|-------------|---------|
| `pactkit-trace` | Plan Phase 1, Act Phase 1 | Deep code tracing and execution flow analysis |
| `pactkit-release` | Release Phase 1 (snapshot/archive) | Version release: snapshot, archive, Tag |

## Agent Skills (invoked via agent roles, not by commands)

| Skill | Available To | Purpose |
|-------|-------------|---------|
| `pactkit-draw` | visual-architect, system-architect agents | Generate Draw.io XML architecture diagrams |
| `pactkit-status` | system-medic agent | Project state overview |
| `pactkit-doctor` | system-medic agent | Diagnose project health |
| `pactkit-review` | qa-engineer agent | PR Code Review |
| `pactkit-analyze` | senior-developer (Act Phase 0.6 inline) | Cross-artifact consistency check: Spec ↔ Board ↔ Test Cases |

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

## Change Type Declaration (STORY-slim-105)
Before modifying code, declare the change type:

| Type | Meaning | Requirement |
|------|---------|-------------|
| `ROOT_CAUSE` | Fixing the root cause | None |
| `WORKAROUND` | Temporary bypass | MUST create tech-debt Story |

Choosing WORKAROUND is allowed, but incurs the cost of creating a tracking Story — no silent bypasses.

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

### Draw.io MCP (`mcp__drawio__*`)
- **Purpose**: Open generated diagrams directly in Draw.io editor for instant visual verification and interactive editing
- **When to use**: If `mcp__drawio__open_drawio_xml` tool is available in the current runtime
- **Tools**: `open_drawio_xml`, `open_drawio_csv`, `open_drawio_mermaid`
- **Trigger**: After generating a `.drawio` XML file or when visualizing existing `.mmd` Mermaid files in Draw.io

## Usage by PDCA Phase

| Phase | MCP Server | Condition |
|-------|-----------|-----------|
| **Plan** | Memory | If `mcp__memory__*` tools are available |
| **Plan** | Draw.io MCP | If `mcp__drawio__*` tools are available (diagram generation) |
| **Design** | shadcn | If `components.json` exists in project root |
| **Design** | Draw.io MCP | If `mcp__drawio__*` tools are available (architecture visualization) |
| **Act** | Context7 | If implementing with unfamiliar library API |
| **Act** | Memory | If `mcp__memory__*` tools are available |
| **Check** | Playwright MCP | If `mcp__playwright__*` tools are available |
| **Check** | Chrome DevTools | If `mcp__chrome-devtools__*` tools are available |
| **Done** | Memory | If `mcp__memory__*` tools are available |

# Shared Protocols

## Lazy Visualize Protocol
> Referenced by: Act Phase 4, Done Phase 2

If source files changed (per `LANG_PROFILES[stack].source_dirs`) OR `code_graph.mmd` is missing, run visualize in all 3 modes (file, class, call). Else skip with log: "Graph up-to-date — no source changes".

## Test Mapping Protocol
> Referenced by: Act Phase 3, Check Phase 5, Done Phase 2.5, Hotfix Phase 2

Map changed source files to test files via `LANG_PROFILES[stack].test_map_pattern`. If no mapping can be determined, fall back to the full test suite.

## Context.md Canonical Format
> Referenced by: Init Phase 6, Plan Phase 3, Act Phase 4, Done Phase 4.5

Write `docs/product/context.md` using this format:
```markdown
# Project Context (Auto-generated)
> Last updated: {ISO timestamp} by {command}

## Sprint Status
{In Progress stories with IDs | Backlog count | Done count}

## Current Stories
{Active stories with brief descriptions}

## Recent Completions
{Last 3 completed stories, one line each}

## Active Branches
{git branch output, or "None" if no feature/fix branches}

## Key Decisions
{Last 5 lessons from lessons.md}

## Next Recommended Action
{If In Progress: `/project-act STORY-XXX` | If Backlog only: `/project-plan` | If empty: `/project-design`}
```

# Architecture Principles

> Derived from SOLID, DRY, 12-Factor App, and Defense-in-Depth practices.
> Violations of MUST rules are treated as bugs. SHOULD rules are advisory.

## 1. Single Source of Truth (DRY)
- Every configuration value, schema definition, or structural rule MUST be defined in exactly one place.
- **Anti-pattern**: The same logic (e.g., a write-then-invalidate workflow, an IRI sanitization routine, a dual-write SQL statement) implemented independently in 3+ files. Each copy drifts over time — one gets a bugfix, the others don't.
- **Detection**: During Plan Phase 1 Lateral Scan, if `fan-in ≥ 3` or `grep` finds 3+ independent implementations of the same operation, MUST evaluate extracting a shared service/function.
- When standalone scripts cannot import the library, they MUST inline the value with a comment pointing to the canonical source.
- When updating a canonical value, search all inline copies with `grep` and update them in the same commit.

## 2. Open-Closed Principle (OCP)
- Adding a new variant MUST NOT require modifying existing functions — violates OCP when adding the Nth case means editing a growing if/elif chain.
- **Anti-pattern**: A `db_type` string checked in 13 if/elif branches across 6 files. Adding a new database type requires touching every branch — use a strategy pattern or registry instead.
- **Pattern**: Define a registry/dispatch table. New variants add an entry; existing code remains unchanged.

## 3. Dependency Inversion (DIP)
- Prompt templates MUST NOT contain hardcoded environment-specific paths.
- Pattern: use named placeholders (`{SKILLS_ROOT}`, `{BOARD_CMD}`, `{PACTKIT_YAML}`) resolved at deploy time by `_render_prompt(template, profile)`.
- Functions MUST accept a `profile: FormatProfile` parameter instead of format-specific booleans (`opencode_format=True`) or manual path strings (`skills_prefix="~/.config/opencode/skills"`).

## 4. Liskov Substitution (LSP) — Deploy Chain Parity
- All deployer classes (ClassicDeployer, OpenCodeDeployer, etc.) MUST support the same user-facing feature set:
  - Selective deployment (read `pactkit.yaml`)
  - Auto-merge on upgrade (`auto_merge_config_file`)
  - Legacy cleanup (`_cleanup_legacy`)
  - Project-level instructions file generation
- Format-specific features (e.g., hooks for Claude Code, opencode.json for OpenCode) are extensions, not omissions.

## 5. Interface Segregation (ISP)
- Each `FormatProfile` exposes only the fields relevant to that format:
  - `commands_dir = None` for formats without custom commands
  - `excluded_agent_fields` removes fields invalid for that format
- Consumers MUST check `if profile.has_custom_commands` before deploying commands — not hardcoded format checks.
- **Module size**: A single file exceeding 500 lines SHOULD be evaluated for splitting. A 565-line route handler mixing 5 resource domains is a sign that responsibilities are not separated.

## 6. Defense-in-Depth (Security)
- **Path traversal**: All file writes use `atomic_write()` which creates parent directories safely.
- **Config isolation**: `_generate_config_if_missing(format=)` writes to the format-specific directory only. Never cross-write.
- **No secret leakage**: `_render_prompt()` variables are all path-based, never credential-based.
- **Standalone script safety**: Skill scripts (board.py, scaffold.py) MUST NOT execute arbitrary imports. Use `try/except ImportError` fallback for pactkit imports.

## 7. Template Rendering Safety
- Use sequential `str.replace()` in `_render_prompt()` — NOT `str.format_map()` or f-strings.
  - Reason: prompt templates contain user-facing complex keys like `{R1, R2, ...}`, `{score}`, `{NNN}` that cause `ValueError: Empty attribute` in Python's format parser.
- JSON literals in templates (`{"key": "value"}`) are naturally safe with sequential replacement — no escaping needed.
- When converting f-string prompt constants to template strings, add legacy variables (e.g., `{M}` for backticks) to the `_render_prompt` var_map.

## 8. Schema Consistency Gate
- Every document type with a structure schema in `schemas.py` SHOULD have a corresponding linter/validator.
- Currently enforced:
  - Spec → `spec_linter.py` (E001-E008, W001-W005) — **blocks /project-act**
  - Board → `board.py` regex parsing — **runtime enforcement**
- Currently advisory only:
  - context.md, lessons.md, test_case → referenced in playbook text via `{CONTEXT_SECTIONS}`, `{LESSONS_ROW_FORMAT}`
- When adding a new schema to `schemas.py`, consider whether it needs a linter gate or if prompt-level enforcement is sufficient.

## 9. Merge over Replace (Incremental Sync)
- When writing to a file that may contain user-modified content or sections managed by other tools, SHOULD use incremental merge (Edit / patch / append) instead of full replacement (Write / overwrite) — full replacement silently destroys content the writer did not generate.
- **Decision Matrix**:

| Target File Characteristics | Strategy | Rationale |
|----------------------------|----------|-----------|
| Generated entirely by this tool, no user sections | Full replace is safe | Writer owns 100% of content |
| Contains user-modified sections OR mixed ownership | **Incremental merge** | Preserve content this tool did not generate |
| Config file with default + override pattern | **Merge missing keys only** | Existing values represent user intent |
| Append-only artifact (changelog, log, history) | **Append** | Never rewrite prior entries |

- **Litmus test**: "Does this file contain content I did not generate?" → If yes, incremental merge. If unsure, incremental merge.
- **Anti-pattern evidence**: BUG-010 (`_rewrite_yaml` destroyed user config), BUG-slim-089 (`_deploy_claude_md` overwrote user CLAUDE.md), STORY-033/STORY-slim-054 (backfill overwrote existing values). All were full-replace where merge was required.

## Quick Reference: Where to Make Changes

| Change Type | File to Edit | Auto-Propagation |
|-------------|-------------|------------------|
| New tool format | `profiles.py` → `FORMAT_PROFILES` | CLI, deployer, config, VALID_FORMATS |
| New document type | `schemas.py` → `SCHEMA_REGISTRY` | `pactkit schema`, playbooks via render_prompt |
| New template variable | `deployer.py` → `_render_prompt()` var_map | All deployed prompts |
| New spec rule | `schemas.py` + `spec_linter.py` | scaffold, playbooks |
| New prompt placeholder | `profiles.py` (if env-specific) or `schemas.py` (if doc-specific) | `_render_prompt()` |

# Sectional Write Protocol

## Rule
When generating **any file** (code, document, test, HTML, etc.) that will exceed **300 lines**:

1. **Write skeleton first**: Create the file with the structural framework (imports, class/function signatures, section headings) via a single Write call
2. **Edit block-by-block**: Fill in one logical block at a time, using Edit after each block before starting the next
3. **Checkpoint between blocks**: After each Edit, print a brief progress message (e.g., "Block 2/5 written.")
4. **Never accumulate**: Do NOT compose the entire file in reasoning before writing — write as you go

## Applies To — any file type over 300 lines
- Documents: PRD, specs, README, architecture guides
- Source code: large modules, multi-endpoint API files, data models
- Tests: test files with many test classes or scenarios
- HTML/templates: prototypes, page templates

## Does NOT Apply To
- Short files (< 300 lines): single Write is fine
- Small config files (YAML, JSON, TOML)

## Anti-Pattern (DO NOT)
```
Compose entire file in head → one Write call at the end
```

## Correct Pattern
```
Write skeleton → Edit block 1 → checkpoint → Edit block 2 → checkpoint → ...
```

# PDCA Nudge Protocol

> **Signal Level**: L3 Recommended (SHOULD) — non-blocking suggestion.

## When to Nudge

When AI analysis in **free conversation** (outside any PDCA command context) produces actionable conclusions, SHOULD append a PDCA command recommendation at the end of the reply.

## Trigger Matrix

| Signal | Command | Condition |
|--------|---------|-----------|
| Bug / error found (single file) | `/project-hotfix` | Single-file fix, no design decision needed |
| Bug + design change needed | `/project-plan` | Multi-file or unclear requirements |
| Architecture improvement identified | `/project-plan` | Involves 2+ file changes |
| New feature need identified | `/project-plan` | Single feature |
| New product / multi-feature need | `/project-design` | 3+ independent stories, greenfield |
| Existing Spec ready to implement | `/project-act STORY-XXX` | Story is on the Board |
| 3+ independent improvement items | `/project-sprint` | Multiple stories can run in parallel |
| Code quality issue (quick fix) | `/project-hotfix` | No behavior change |

## Nudge Format

Place at the **end** of the reply, after all analysis content:

```
💡 This analysis can be tracked via `{command}`:
> {one-sentence reason why this command fits}
```

When replying in Chinese, use:

```
💡 这个分析结果可以通过 `{command}` 来跟踪实现：
> {一句话说明为什么推荐这个命令}
```

## Suppression Rules (MUST NOT nudge when)

- **In PDCA context**: A PDCA command is already active (Plan/Act/Check/Done/Sprint/Hotfix/Design)
- **User opted out**: User explicitly said they just want to chat, not follow a workflow
- **No issue found**: Analysis confirms the current implementation is correct
- **Dedup**: The same command was already nudged earlier in this conversation

# Solution Design Protocol

> Referenced by: Plan Phase 1, Act Phase 1

## Purpose
Evaluate the capability delta (framework native + project existing vs. needs implementation) before writing code — to avoid reinventing what the framework already provides or bypassing what the project has already encapsulated.

## Anti-Patterns This Protocol Prevents

| Anti-Pattern | Example | Consequence |
|--------------|---------|-------------|
| **Framework Blindness** | Framework has a caching layer, but writing custom cache from scratch | Duplicated logic, misses framework optimizations and bug fixes |
| **Project Blindness** | Project has `get_db_connection()`, but creating a new connection directly | Configuration drift, bypasses pooling/retry/logging the project already wired |
| **Hardcoded Coupling** | Importing a framework's internal module directly instead of using the project's wrapper | Tight coupling to framework internals; breaks when framework upgrades |

## Trigger Conditions

This protocol **MUST** be executed when (SHOULD — skipping increases reinvention risk):
- New feature involves frameworks already used by the project
- Requirement involves capabilities that frameworks commonly provide (auth, caching, scheduling, ORM, state management, etc.)

This protocol **MAY** be skipped when:
- Pure business logic not involving framework capabilities
- Documentation, configuration, or style changes only

## Protocol Execution

### Step 1: Identify Relevant Frameworks (SHOULD)
> **Goal**: Know which frameworks the project depends on, filter to those relevant to the requirement.

Read the project's dependency file (`pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, `build.gradle`, `Cargo.toml`, etc.) and identify frameworks related to the current requirement.

**Early exit**: If no frameworks are relevant to the requirement, skip to Step 4 — the answer is "Needs new implementation."

**Output checkpoint**: `"Relevant frameworks: {name} v{version}, ..."`

### Step 2: Query Framework Native Capabilities (SHOULD)
> **Goal**: Does the framework already provide what we need?

**Query path (by priority):**
1. **Context7 MCP** (if available) — real-time, authoritative
2. **WebFetch** official docs (if Context7 unavailable) — real-time, requires parsing
3. **Training data** (fallback) — MUST declare framework version to avoid outdated APIs

**Focus**: Does the framework natively support this capability? What API or pattern? What config is needed?

**Output checkpoint**: `"Framework capability: {name} supports {capability} via {API/pattern}"` or `"No native support found."`

### Step 3: Query Project Existing Capabilities (SHOULD)
> **Goal**: What has the project already built or encapsulated from the framework?

Scan the project for:
- **Framework usage**: Search import statements to see which framework modules are already in use
- **Abstraction layer**: Look for factory functions (`get_*`, `build_*`, `create_*`), wiring/DI files, and wrapper modules that encapsulate framework details
- **Call chain**: If the above is insufficient, trace the call graph from the relevant module

**Output checkpoint**:
```
Project existing:
- Framework usage: {module} used in {file}
- Encapsulated: {function}() in {file} — {purpose}
```

### Step 3.5: Query Project Internal Patterns (SHOULD)
> **Goal**: Does the project already have multiple independent implementations of the same operation?

This step catches **intra-project duplication** that Steps 1-3 miss (they focus on framework-level reuse).

**Scan method** (tiered — use the most precise available):
1. **LSP** (if available): `incomingCalls` or `findReferences` on the core operation — type-aware, zero false positives
2. **visualize**: `visualize --mode call --reverse --entry <operation>` — fan-in from call graph
3. **grep**: `grep -rn "<operation>" src/` — text-level fallback

**Output checkpoint**: `"Internal pattern: {operation} has {N} implementations in {files}"`

### Step 4: Delta Assessment (MUST)
> **Goal**: Decide to reuse or implement.

**Assessment Matrix**

| Framework Has It | Project Uses It | Project Encapsulated | Decision |
|------------------|-----------------|----------------------|----------|
| Yes | No | — | **Enable framework capability** — prefer native over custom |
| Yes | Yes | Yes | **Reuse project wrapper** — do not bypass the abstraction layer |
| Yes | Yes | No | Evaluate: encapsulate or use directly |
| No | — | Has similar | **Extend** the existing project implementation |
| No | — | No | **Implement new** — this is the only case where new code is justified |
| — | — | ≥ 3 independent | **Extract shared service** — MUST evaluate shared abstraction before adding Nth implementation |

**Decision Constraints**
- **MUST NOT** bypass project abstraction layer to use framework directly — abstraction exists for unified configuration, testability, and isolation of change
- **SHOULD** prefer framework native capability over custom implementation — framework code is better tested and community-maintained
- **MUST** state reasoning if not using an available framework capability

### Step 5: Output Format

**Plan Phase** — write to `## Technical Design` in Spec:
```markdown
### Capability Assessment
| Need | Source | Decision |
|------|--------|----------|
| {capability} | {framework}.{module} (native) | Reuse / Enable / New |

### Reuse Points
- `{function}()` — {file}

### New Implementation Required
- {component}: {brief purpose}
```

**Act Phase** — brief assessment in Phase 1:
```
Capability assessment: Reuse {N}, Enable {N}, New {N}
- Reuse: {list}
- Enable: {list}
- New: {list}
```

## Implementation Constraints

When writing new code (Step 4 "Implement new"), apply these constraints:

### No Magic Values (MUST NOT)
Do not hardcode values that may change (URLs, thresholds, timeouts, feature flags). Extract to named constants or configuration. Exception: truly invariant values (HTTP status codes, math constants).

**Scope**: This constraint applies to **all artifacts**, not just source code — including rules files, Specs, configs, playbooks, and prompts. Any value that appears in 2+ places or that a user/project might need to customize SHOULD be parameterized.

**Flexibility Litmus Test**: If changing a value requires `grep` + multi-file edits, it should be a named constant, config key, or template variable instead.

| Artifact Type | Hardcode Anti-Pattern | Parameterized Pattern |
|---------------|----------------------|----------------------|
| Source code | `timeout = 30` | `timeout = config.DEFAULT_TIMEOUT` |
| Rules / playbooks | `run at most 8 files` | `run at most {MAX_TRACE_FILES} files` or define once, reference by name |
| Specs | `use SQLite for storage` | `use persistent storage (see Technical Design for engine choice)` |
| Config (YAML/JSON) | Inline URL `https://api.example.com` | `${API_BASE_URL}` or env-resolved placeholder |

### Open-Closed Principle (SHOULD)
Design new code to be extensible without modification. If adding a new variant requires `if/elif` chains, consider a registry or strategy pattern instead.

### Single Responsibility (SHOULD)
Keep functions/classes focused on one concern. If a function name contains "and" or does multiple unrelated things, extract sub-operations.

### Dependency Direction (MUST NOT)
Do not import from higher-level modules into lower-level modules. Domain/core imports nothing from infrastructure; infrastructure imports from domain. Circular imports indicate a layering violation.

## Interaction with Other Protocols

| Protocol | Relationship |
|----------|--------------|
| **pactkit-trace** | Trace = call chains (vertical). This protocol = capability reuse (horizontal). Run Trace first, then this. |
| **Hierarchy of Truth** | Output goes into Spec (Tier 1). Implementation MUST follow Technical Design in Spec. |

> **TIP**: Run `/project-init` to set up project governance and enable cross-session context.
