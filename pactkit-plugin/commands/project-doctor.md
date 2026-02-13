---
description: "Diagnose project health status"
allowed-tools: [Read, Bash, Glob]
---

# Command: Doctor (v18.6 Rich)
- **Usage**: `/project-doctor`
- **Agent**: System Medic

## 🧠 Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block.
1.  **Diagnosis**: Is this a configuration drift, missing file, or broken test?
2.  **Scope**: Local (`.claude/`) vs Project (`src/`).

## 🛡️ Phase 0.5: Init Guard (Auto-detect)
> **INSTRUCTION**: Check if the project has been initialized before proceeding.
1.  **Check Markers**: Verify the existence of ALL three:
    - `.claude/pactkit.yaml` (project-level config)
    - `docs/product/sprint_board.md` (sprint board)
    - `docs/architecture/graphs/` (architecture graph directory)
2.  **If ANY marker is missing**:
    - Print: "⚠️ Project not initialized. Missing markers detected."
    - Ask the user to choose: **(a)** Auto-fix by running `/project-init`, or **(b)** Continue diagnosis without initialization.
    - If the user chooses **(a)**: Execute `/project-init`, then resume Doctor from Phase 1.
    - If the user chooses **(b)**: Proceed to Phase 1 and include the missing markers in the health report.
3.  **If ALL markers exist**: Skip silently to Phase 1.

## 🎬 Phase 1: Structural Health
1.  **Scan**: Run `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize`.
2.  **Class Scan**: Run `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`.
3.  **Check**: `docs/test_cases/` existence.

## 🎬 Phase 2: Infrastructure & Data
1.  **Config**: Check `./.claude/pactkit.yaml`.
2.  **Data**: Specs vs Board linkage.
3.  **Tests**: Is `tests/e2e/` empty?

## 🎬 Phase 3: Report
1.  **Output**: Health Summary.
