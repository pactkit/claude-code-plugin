---
name: pactkit-garden
description: "Codebase quality patrol — detect dead code, stale docs, pattern duplication"
---

# PactKit Garden

Codebase entropy detection — scans for dead code, stale documentation, and pattern duplication.

## When Invoked
- Periodically (weekly) to prevent codebase entropy accumulation.
- Before release to ensure cleanup.
- As part of Sprint QA flow.

## Protocol

### 1. Run Garden Scan
Run `pactkit garden` to perform automated quality checks:
- **Dead Imports**: Unused Python imports (F401-equivalent).
- **Empty Except**: Bare `except: pass` blocks.
- **Stale Docs**: Done specs referencing deleted files, orphaned test cases, stale context.md.
- **Duplicate Functions**: Same function signature in multiple modules.
- **Stale Canonical Copies**: Inline copies that diverged from their canonical source.

### 2. Interpret Results
- Exit 0: No findings — codebase is clean.
- Exit 1: Findings detected — review and address.

### 3. Options
- `pactkit garden --json` — machine-readable output for CI integration.
- `pactkit garden --scope <path>` — scan specific directory only.
