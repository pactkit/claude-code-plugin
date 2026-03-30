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
1.  **Check CLI Availability**: Run `pactkit version` to check if CLI is available.
    - **If available**: Proceed to Step 2.
    - **If NOT available** (command fails): Print warning: "⚠️ pactkit CLI not found. Install with: `pip install pactkit`". Then manually create a minimal `pactkit.yaml` (in `.claude/` or `.opencode/` depending on environment) with `stack: <detected>`, `version: 0.0.1`, `root: .`, `developer: ""` and skip to Step 4.
2.  **Environment Detection** (MUST run BEFORE any `pactkit init/update` call — BUG-slim-001):
    - Check if `~/.config/opencode/AGENTS.md` exists OR `which opencode` succeeds.
    - Set `DETECTED_ENV`:
      - **OpenCode detected** → `DETECTED_ENV=opencode`
      - **Otherwise** → `DETECTED_ENV=classic`
    - This variable determines the `--format` flag for all subsequent `pactkit` CLI calls.
3.  **Generate Config**: Check if `pactkit.yaml` exists (check `.claude/pactkit.yaml` then `.opencode/pactkit.yaml`).
    - **If missing**:
      - If `DETECTED_ENV=opencode`: Run `pactkit init --format opencode`
      - If `DETECTED_ENV=classic`: Run `pactkit init`
    - **If exists**:
      - If `DETECTED_ENV=opencode`: Run `pactkit update --format opencode`
      - If `DETECTED_ENV=classic`: Run `pactkit update`
4.  **Stack Detection** (config-first, then file-based fallback):
    - **Config-first**: If `pactkit.yaml` exists (in `.claude/` or `.opencode/`) and has a `stack` value set (including `auto`), use that value and skip file-based detection.
    - **File-based detection** (only if no config value):
      - Valid values: `python`, `node`, `go`, `java`, `auto`
      - If `pyproject.toml` or `requirements.txt` or `setup.py` exists → `stack: python`
      - If `package.json` exists → `stack: node`
      - If `go.mod` exists → `stack: go`
      - If `pom.xml` or `build.gradle` exists → `stack: java`
    - **Safe fallback**: If none match and no config exists, default to `stack: auto` and print warning: "⚠️ No stack detected, defaulting to auto. You can set `stack:` in `pactkit.yaml` later."
    - Do NOT block on user input for stack selection mid-flow.
5.  **Project Instructions File** (environment-aware):
    - **If `DETECTED_ENV=classic`**: Check/Create `./.claude/CLAUDE.md` if missing (do NOT overwrite).
      - Use the directory name as the project name. Fill test_runner and lint_command from the detected language stack in LANG_PROFILES.
      - Include: venv instructions (if detected), dev commands, `@./docs/product/context.md` reference for cross-session context.
    - **If `DETECTED_ENV=opencode`**: Do NOT create `.claude/` or `CLAUDE.md`. Proceed to Step 6.
6.  **OpenCode Project Setup** (only if `DETECTED_ENV=opencode`):
    - Ensure `pactkit.yaml` exists in `.opencode/` (already handled by Step 3).
    - Generate `./opencode.json` if missing:
      ```json
      {
        "$schema": "https://opencode.ai/config.json",
        "instructions": ["AGENTS.md", "docs/product/context.md"],
        "permission": { "edit": "allow", "bash": { "*": "allow", "rm -rf /*": "deny" } },
        "mcp": { "context7": { "type": "remote", "url": "https://mcp.context7.com/mcp" } }
      }
      ```
    - Generate `./AGENTS.md` if missing (project instructions, can reference global AGENTS.md or be standalone).
    - Print: "ℹ️ OpenCode environment detected. Generated opencode.json, AGENTS.md, and pactkit.yaml."

## 🎬 Phase 2: Architecture Governance
1.  **Scaffold**: Determine the skills path based on `DETECTED_ENV`:
    - If `DETECTED_ENV=opencode`: `SKILLS_PATH=~/.config/opencode/skills`
    - If `DETECTED_ENV=classic`: `SKILLS_PATH=${CLAUDE_PLUGIN_ROOT}/skills`
    Run `python3 $SKILLS_PATH/pactkit-visualize/scripts/visualize.py init_arch`.
    - *Result*: Folders created. Placeholders (`system_design.mmd`) created.
2.  **Ensure**: `mkdir -p docs/product docs/specs docs/test_cases tests/e2e/api tests/e2e/browser tests/unit`.

## 🎬 Phase 3: Discovery (Reverse Engineering)
1.  **Scan Reality**: Run `python3 $SKILLS_PATH/pactkit-visualize/scripts/visualize.py visualize`.
    - *Goal*: If this is an existing project, overwrite the empty `code_graph.mmd` with the REAL class structure immediately.
2.  **Class Scan**: Run `python3 $SKILLS_PATH/pactkit-visualize/scripts/visualize.py visualize --mode class`.
3.  **Verify**: Read `docs/architecture/graphs/code_graph.mmd` and `class_graph.mmd`.
    - *Check*: Is it still "No code yet"? If files exist in src, this graph MUST contain classes.

## 🎬 Phase 4: Project Skeleton
1.  **Board**: Run `python3 $SKILLS_PATH/pactkit-scaffold/scripts/scaffold.py create_board` if `docs/product/sprint_board.md` does not exist.
    - This ensures the board has all three section headers: `## 📋 Backlog`, `## 🔄 In Progress`, `## ✅ Done`.

## 🎬 Phase 5: Knowledge Base (The Law)
1.  **Law**: Write `docs/architecture/governance/rules.md`.
2.  **History**: Write `docs/architecture/governance/lessons.md` with table header `| Date | Lesson | Context |` and separator `|------|--------|---------|`. The third column MUST be `Context`, not `Source`.

## 🎬 Phase 6: Session Context Bootstrap
1.  **Generate Context**: Run `pactkit context` to generate `docs/product/context.md`. Set "Last updated by" to `/project-init`.

## 🎬 Phase 7: Handover
1.  **Output**: "✅ PactKit Initialized. Reality Graph captured. Knowledge Base ready."
2.  **Advice**: "⚠️ IMPORTANT: Run `/project-plan 'Reverse engineer'` to align the HLD."
