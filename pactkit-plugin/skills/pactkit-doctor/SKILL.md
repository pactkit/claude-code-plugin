---
name: pactkit-doctor
description: "Diagnose project health status"
---

# PactKit Doctor

Diagnostic tool for project health — config drift, missing files, stale graphs, orphaned specs.

## When Invoked
- **Init** (auto-check): Verify project structure after initialization.
- Standalone diagnostic when project health is in question.

## Severity Levels
| Level | Meaning |
|-------|---------|
| INFO | Informational, no action required |
| WARN | Potential issue, should be addressed |
| ERROR | Critical mismatch, must be fixed |

## Protocol

### 1. Structural Health
- Run `visualize` to check architecture graph generation.
- Run `visualize --mode class` for class diagram verification.
- Check `docs/test_cases/` existence.

### 2. Stale Architecture Graph Detection
- Compare `docs/architecture/graphs/*.mmd` modification times against newest source file mtime.
- If any graph file is older than the newest source file by > 7 days: report WARN.
- Suggest: "Run `visualize` to refresh stale architecture graphs."

### 3. Orphaned and Missing Specs
- **Orphaned Specs** (INFO): List spec files in `docs/specs/` that have no matching entry in `docs/product/sprint_board.md` or `docs/product/archive/`.
- **Missing Specs** (WARN): List story IDs found in Sprint Board that have no corresponding `docs/specs/{ID}.md` file.
- Suggest: "Run `/project-plan` to create missing specs."

### 4. Configuration Drift Detection
- Compare `pactkit.yaml` against deployed files in `.claude/`:
  - Check if enabled agents match deployed agent files.
  - Check if enabled rules match deployed rule files.
  - Check if enabled skills match deployed skill directories.
- Any mismatch: report ERROR with specific drift details.
- Suggest: "Run `pactkit update` to sync configuration."

### 5. Infrastructure & Data
- Verify `.claude/pactkit.yaml` exists and is valid.
- Check Specs vs Board linkage (every board story should have a spec).
- Check if `tests/e2e/` is empty.

### 6. Report
Output a structured health report grouped by category:

| Category | Check Item | Severity | Description |
|----------|------------|:--------:|-------------|
| Architecture | Graph Freshness | INFO/WARN | Stale if > 7 days |
| Specs | Orphaned Specs | INFO | Specs without board entries |
| Specs | Missing Specs | WARN | Board stories without specs |
| Config | Drift Detection | ERROR | pactkit.yaml vs deployed |
| Tests | Test Suite | INFO/WARN | Test runner status |

End with overall status: "Health: OK" (no WARN/ERROR) or "Health: NEEDS ATTENTION" (WARN/ERROR found).
