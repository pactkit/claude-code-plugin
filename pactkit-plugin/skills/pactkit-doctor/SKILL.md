---
name: pactkit-doctor
description: "Diagnose project health status"
---

# PactKit Doctor

Diagnostic tool for project health — config drift, missing files, broken tests.

## When Invoked
- **Init** (auto-check): Verify project structure after initialization.
- Standalone diagnostic when project health is in question.

## Protocol

### 1. Structural Health
- Run `visualize` to check architecture graph generation.
- Run `visualize --mode class` for class diagram verification.
- Check `docs/test_cases/` existence.

### 2. Infrastructure & Data
- Verify `.claude/pactkit.yaml` exists and is valid.
- Check Specs vs Board linkage (every board story should have a spec).
- Check if `tests/e2e/` is empty.

### 3. Report
Output a health summary table:

| Check Item | Status | Description |
|------------|:------:|-------------|
| PactKit Config | OK/WARN | ... |
| Architecture Graphs | OK/WARN | ... |
| Spec-Board Linkage | OK/WARN | ... |
| Tests | OK/WARN | ... |
