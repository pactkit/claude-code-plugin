---
description: "Initialize project scaffolding and governance structure"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Init (v1.3.0 Rich)
- **Usage**: `/project-init`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process
1.  **Environment Check**: Is this a fresh folder or legacy project?
2.  **Compliance**: Does the user need `pactkit.yaml`?
3.  **Strategy**: If legacy, I must prioritize `visualize` to capture Reality.

## 🛡️ Phase 0.5: Git Repository Guard
> **INSTRUCTION**: Check if the directory is inside a git repository. This check is non-interactive — never prompt the user.
1.  **Check**: Run `git rev-parse --is-inside-work-tree` (suppress stderr).
2.  **If NOT a git repo** (command fails):
    - Print warning: "⚠️ No git repository detected. Git operations (commit, branch) will not work. Run `git init` to initialize one."
    - Continue with the rest of init. Do NOT prompt or block.
3.  **If already a git repo**: Skip silently to Phase 1.

## 🎬 Phase 1: Environment & Config
> **NOTE**: This playbook is pre-rendered per-format during deployment. All paths below are already resolved for **{DISPLAY_NAME}** (`{FORMAT_NAME}`). No runtime IDE detection needed.
1.  **Check CLI Availability**: Run `pactkit version` to check if CLI is available.
    - **If available**: Proceed to Step 2.
    - **If NOT available** (command fails): Print warning: "⚠️ pactkit CLI not found. Install with: `pip install pactkit`". Then manually create a minimal `pactkit.yaml` in `{PROJECT_CONFIG_DIR}/` with `stack: <detected>`, `root: .`, `developer: ""` and skip to Step 3.
2.  **Generate Config**: Check if `{PACTKIT_YAML}` exists.
    - **If missing**: Run `pactkit init --format {FORMAT_NAME}`
    - **If exists**: Run `pactkit update --format {FORMAT_NAME}`
3.  **Stack Detection** (config-first, then file-based fallback):
    - **Config-first**: If `{PACTKIT_YAML}` exists and has a `stack` value set (including `auto`), use that value and skip file-based detection.
    - **File-based detection** (only if no config value):
      - Valid values: `python`, `node`, `go`, `java`, `auto`
      - If `pyproject.toml` or `requirements.txt` or `setup.py` exists → `stack: python`
      - If `package.json` exists → `stack: node`
      - If `go.mod` exists → `stack: go`
      - If `pom.xml` or `build.gradle` exists → `stack: java`
    - **Safe fallback**: If none match and no config exists, default to `stack: auto` and print warning: "⚠️ No stack detected, defaulting to auto. You can set `stack:` in `{PACTKIT_YAML}` later."
    - Do NOT block on user input for stack selection mid-flow.
4.  **Project Instructions File**: Check/Create `./{PROJECT_CONFIG_DIR}/{INSTRUCTIONS_FILE}` if missing (do NOT overwrite).
    - Use the directory name as the project name. Fill test_runner and lint_command from the detected language stack in LANG_PROFILES.
    - Include: venv instructions, dev commands, and `pactkit context` as the cold-start bootstrap; do not `@import` generated Context.

## 🔌 Phase 1.5: External Dependencies (STORY-slim-137)
> Runs BEFORE Phase 3 — Discovery (codegraph) depends on these tools.
1.  Run `pactkit deps check`. If all present, skip silently.
2.  If anything is missing, list items + purposes and ask the user: "Install now?"
3.  On explicit yes: run `pactkit deps install`. NEVER improvise install commands — the CLI owns the registry.
4.  If declined/failed/refused (`enterprise.no_external`): print the manual commands and continue — MUST NOT block init.

## 🎬 Phase 2: Architecture Governance
1.  **Scaffold**: Run `{VISUALIZE_CMD} init_arch`.
    - *Result*: Folders created. Placeholders (`system_design.mmd`) created.
2.  **Ensure**: `mkdir -p docs/product docs/specs docs/test_cases tests/e2e/api tests/e2e/browser tests/unit`.

## 🎬 Phase 3: Discovery (Reverse Engineering)
1.  **Scan Reality**: Run `{VISUALIZE_CMD} visualize`.
    - *Goal*: If this is an existing project, overwrite the empty `code_graph.mmd` with the REAL class structure immediately.
2.  **Class Scan**: Run `{VISUALIZE_CMD} visualize --mode class`.
3.  **Module Scan**: Run `{VISUALIZE_CMD} visualize --mode module` to generate module-level overview for multi-module projects.
4.  **Verify**: Read `docs/architecture/graphs/code_graph.mmd` and `class_graph.mmd`.
    - *Check*: Is it still "No code yet"? If files exist in src, this graph MUST contain classes.

## 🎬 Phase 4: Project Skeleton
1.  **Story Facts**: Create `docs/product/stories/`. Do not create a writable Board; render one explicitly with `pactkit board render` only when configured. For an existing aggregate project, preview `pactkit governance migrate`, then ask before applying `pactkit governance migrate --apply`.
    - This ensures the board has all three section headers: `## 📋 Backlog`, `## 🔄 In Progress`, `## ✅ Done`.

## 🎬 Phase 5: Knowledge Base (The Law)
1.  **Law**: Write `docs/architecture/governance/rules.md`.
2.  **History**: Create `docs/architecture/governance/lessons/`; every Lesson is a create-only record written by `pactkit lesson-append`.

## 🎬 Phase 6: Session Context Bootstrap
1.  **Generate Context**: Run `pactkit context` to generate ignored local `.pactkit/context.md`; never stage it.

## 🎬 Phase 7: Next Step
1.  **Output**: "✅ PactKit Initialized. Reality Graph captured. Knowledge Base ready."
2.  **Advice**: "⚠️ IMPORTANT: Continue with `/project-plan 'Reverse engineer'` in this session when requested; a new session is optional."
