---
description: "Initialize project scaffolding and governance structure"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Init (v18.6 Rich)
- **Usage**: `/project-init`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block before using any tools.
1.  **Environment Check**: Is this a fresh folder or legacy project?
2.  **Compliance**: Does the user need `pactkit.yaml`?
3.  **Strategy**: If legacy, I must prioritize `visualize` to capture Reality.

## 🎬 Phase 1: Environment & Config
1.  **Action**: Check/Create `./.claude/pactkit.yaml` in **Current Directory**.
    - *Content*: `stack: <detected>`, `version: 0.0.1`, `root: .`, `language: <detected>`.
2.  **Language Detection** (for `language` field in `pactkit.yaml`):
    - If `pyproject.toml` or `requirements.txt` or `setup.py` exists → `language: python`
    - If `package.json` exists → `language: node`
    - If `go.mod` exists → `language: go`
    - If `pom.xml` or `build.gradle` exists → `language: java`
    - If none match → ask the user to specify
    - The detected language determines which `LANG_PROFILES` entry to use for test runner, cleanup, etc.

## 🎬 Phase 2: Architecture Governance
1.  **Scaffold**: Run `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py init_arch`.
    - *Result*: Folders created. Placeholders (`system_design.mmd`) created.
2.  **Ensure**: `mkdir -p docs/product docs/specs docs/test_cases tests/e2e/api tests/e2e/browser tests/unit`.

## 🎬 Phase 3: Discovery (Reverse Engineering)
1.  **Scan Reality**: Run `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize`.
    - *Goal*: If this is an existing project, overwrite the empty `code_graph.mmd` with the REAL class structure immediately.
2.  **Class Scan**: Run `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`.
3.  **Verify**: Read `docs/architecture/graphs/code_graph.mmd` and `class_graph.mmd`.
    - *Check*: Is it still "No code yet"? If files exist in src, this graph MUST contain classes.

## 🎬 Phase 4: Project Skeleton
1.  **Board**: Create `docs/product/sprint_board.md` if missing.

## 🎬 Phase 5: Knowledge Base (The Law)
1.  **Law**: Write `docs/architecture/governance/rules.md`.
2.  **History**: Write `docs/architecture/governance/lessons.md`.

## 🎬 Phase 6: Session Context Bootstrap
1.  **Generate Context**: Write `docs/product/context.md` with initial project state:
    - Read `docs/product/sprint_board.md` (likely empty for new projects)
    - Read `docs/architecture/governance/lessons.md` (last 5 entries)
    - Run `git branch --list 'feature/*' 'fix/*'`
    - Write `docs/product/context.md` using the standard format (see `/project-done` Phase 4.5 for format)
    - Set "Last updated by" to `/project-init`

## 🎬 Phase 7: Handover
1.  **Output**: "✅ PactKit Initialized. Reality Graph captured. Knowledge Base ready."
2.  **Advice**: "⚠️ IMPORTANT: Run `/project-plan 'Reverse engineer'` to align the HLD."
