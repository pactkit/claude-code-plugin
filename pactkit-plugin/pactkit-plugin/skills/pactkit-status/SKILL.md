---
name: pactkit-status
description: "Project state overview for cold-start orientation"
---

# PactKit Status

Read-only project state report. Provides sprint board summary, git state, and health indicators.

## When Invoked
- **Init Phase 6** (Session Context): Bootstrap initial context.
- **Cold-start detection**: Auto-invoked when session needs orientation.

## Protocol

### 1. Gather Data
- Check if `docs/product/sprint_board.md` exists.
- If yes: extract story counts by section (Backlog / In Progress / Done).
- Count Specs in `docs/specs/*.md` vs total board stories.
- Check architecture graph freshness.

### 2. Git State
- Current branch, uncommitted changes, active feature branches.

### 3. Output Report
```
## Project Status Report
### Sprint Board
- Backlog: {N} stories
- In Progress: {N} stories
- Done: {N} stories
### Git State
- Branch: {current}
- Uncommitted: {Y/N}
### Health Indicators
- Architecture graphs: {fresh/stale/missing}
- Specs coverage: {N/N}
### Recommended Next Action
{Decision tree}
```

> **CONSTRAINT**: This skill is read-only. It does not modify any files.
