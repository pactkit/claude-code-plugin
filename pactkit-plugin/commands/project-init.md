---
description: "Initialize project scaffolding and governance structure"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Init (v1.3.0 Rich)
- **Usage**: `/project-init`
- **Agent**: System Architect

## 🧠 Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block before using any tools.
1.  **Environment Check**: Is this a fresh folder or legacy project?
2.  **Compliance**: Does the user need `pactkit.yaml`?
3.  **Strategy**: If legacy, I must prioritize `visualize` to capture Reality.

## 🛡️ Phase 0.5: Git Repository Guard
> **INSTRUCTION**: Check if the directory is inside a git repository before creating files.
1.  **Check**: Run `git rev-parse --is-inside-work-tree` (suppress stderr).
2.  **If NOT a git repo** (command fails):
    - Ask the user: "No git repository detected. Initialize one with `git init`?"
    - **If user confirms**: Run `git init` in the current directory.
    - **If user declines**: Print warning: "⚠️ Git operations (commit, branch) will not work without a repository." Continue with the rest of init.
3.  **If already a git repo**: Skip silently to Phase 1.

## 🎬 Phase 1: Environment & Config
1.  **Check CLI Availability**: Run `pactkit version` to check if CLI is available.
    - **If available**: Proceed to Step 2.
    - **If NOT available** (command fails): Print warning: "⚠️ pactkit CLI not found. Install with: `pip install pactkit`". Then manually create a minimal `.claude/pactkit.yaml` with `stack: <detected>`, `version: 0.0.1`, `root: .` and skip to Step 4.
2.  **Generate Config**: Check if `./.claude/pactkit.yaml` exists.
    - **If missing**: Run `pactkit init` to generate complete configuration.
    - **If exists**: Run `pactkit update` to backfill any missing sections (preserves user customizations).
3.  **Stack Detection** (auto-detected by `pactkit init`, or manual fallback):
    - Valid values: `python`, `node`, `go`, `java`
    - If `pyproject.toml` or `requirements.txt` or `setup.py` exists → `stack: python`
    - If `package.json` exists → `stack: node`
    - If `go.mod` exists → `stack: go`
    - If `pom.xml` or `build.gradle` exists → `stack: java`
    - If none match → ask the user to specify
4.  **Project CLAUDE.md**: Check/Create `./.claude/CLAUDE.md` if missing (do NOT overwrite if it already exists).
    - *Purpose*: Project-level instructions for Claude Code (separate from global `~/.claude/CLAUDE.md`).
    - *Venv Detection*: Check if a virtual environment exists (`.venv/`, `venv/`, or `env/` with `bin/python3`).
    - *Content template*:
      ```markdown
      # {Project Name} — Project Context

      {IF venv detected}
      ## Virtual Environment
      Always use the project's virtual environment:
      - **Activate**: `source {venv_path}/bin/activate`
      - **Python**: `{venv_path}/bin/python3`
      - **Pytest**: `{venv_path}/bin/pytest`
      - **Pip**: `{venv_path}/bin/pip`
      {END IF}

      ## Dev Commands

      ```
      # Run tests
      {IF venv detected}{venv_path}/bin/{ELSE}{END IF}{test_runner from LANG_PROFILES}

      # Lint
      {lint_command from LANG_PROFILES}
      ```

      @./docs/product/context.md
      ```
    - Use the directory name as the project name.
    - Fill `test_runner` and `lint_command` from `LANG_PROFILES` based on the detected language.
    - If venv detected, prefix test commands with venv bin path (e.g., `.venv/bin/pytest`).
    - The `@./docs/product/context.md` reference enables cross-session context loading.

## 🎬 Phase 2: Architecture Governance
1.  **Scaffold**: Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py init_arch`.
    - *Result*: Folders created. Placeholders (`system_design.mmd`) created.
2.  **Ensure**: `mkdir -p docs/product docs/specs docs/test_cases tests/e2e/api tests/e2e/browser tests/unit`.

## 🎬 Phase 3: Discovery (Reverse Engineering)
1.  **Scan Reality**: Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize`.
    - *Goal*: If this is an existing project, overwrite the empty `code_graph.mmd` with the REAL class structure immediately.
2.  **Class Scan**: Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`.
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
