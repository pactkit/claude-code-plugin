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

### 1. Run Deterministic Checks
Run `pactkit doctor` to perform automated diagnostics:
- **Orphaned/Missing Specs**: Cross-references `docs/specs/` vs board + archive.
- **Config Drift**: Compares `pactkit.yaml` items vs deployed files.
- **Stale Graphs**: Checks `docs/architecture/graphs/*.mmd` mtimes vs source files.

### 2. Structural Health (Manual)
- Run `visualize` to check architecture graph generation.
- Run `visualize --mode class` for class diagram verification.
- Check `docs/test_cases/` existence.

### 3. Infrastructure & Data
- Verify `pactkit.yaml` exists (in `.claude/pactkit.yaml` or `.opencode/pactkit.yaml`) and is valid.
- Check if `tests/e2e/` is empty.

### 4. Report
Output a structured health report grouped by category:

| Category | Check Item | Severity | Description |
|----------|------------|:--------:|-------------|
| Architecture | Graph Freshness | INFO/WARN | Stale if > 7 days |
| Specs | Orphaned Specs | INFO | Specs without board entries |
| Specs | Missing Specs | WARN | Board stories without specs |
| Config | Drift Detection | ERROR | pactkit.yaml vs deployed |
| Tests | Test Suite | INFO/WARN | Test runner status |

End with overall status: "Health: OK" (no WARN/ERROR) or "Health: NEEDS ATTENTION" (WARN/ERROR found).
