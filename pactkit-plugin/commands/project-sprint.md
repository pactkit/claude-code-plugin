---
description: "Automated PDCA Sprint orchestration via Subagent Team (Slim Team)"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Sprint (v1.4.0 Protocol-Only Orchestrator)
- **Usage**: `/project-sprint "$ARGUMENTS"`
- **Agent**: Team Lead (current session)

> **CORE PRINCIPLE**: Thin Orchestrator — Lead does ZERO file reading, only dispatches.
> Each subagent reads `docs/specs/`, `commands/*.md`, and `docs/product/sprint_board.md` from disk.

## Phase 0: Setup
1. Parse requirement from `$ARGUMENTS`. Determine next STORY-ID via Glob on `docs/specs/`.
2. `TeamCreate("sprint-{STORY_ID}")`.
3. `TaskCreate` for each stage: Build (no deps), Check-QA (blockedBy: Build), Check-Security (blockedBy: Build), Close (blockedBy: both Checks).
4. Verify worktree support (`git worktree list`). Use `isolation="worktree"` if supported.

## Phase 1: PDCA Execution

### Stage A: Build (Plan + Act merged)
- Launch `system-architect` with worktree isolation.
- Prompt: Execute `commands/project-plan.md` then `commands/project-act.md` for {STORY_ID}. Report "BUILD PASS" or "BUILD FAIL: reason".
- On completion: merge worktree branch, verify Spec exists. On failure: STOP.

### Stage B: Check (PARALLEL — launch both in ONE message)
- Launch `qa-engineer` (model: sonnet, isolation="worktree"): Execute `commands/project-check.md`. Report "QA PASS/FAIL".
- Launch `security-auditor` (model: sonnet, isolation="worktree"): OWASP audit for {STORY_ID}. Report "SECURITY PASS/FAIL".
- Collect reports from worktrees. On any FAIL: STOP.

### Stage C: Close
- Launch `repo-maintainer` (model: sonnet, isolation="worktree"): Execute `commands/project-done.md`. Report "DONE PASS/FAIL".
- Merge worktree branch on success.

## Phase 2: Cleanup
1. `SendMessage(type="shutdown_request")` to all teammates.
2. `TeamDelete` to remove task directory.
3. Report: Spec path, test results, commit hash, report files.

## Error Handling
- ANY stage failure → STOP immediately, report, always run `TeamDelete`.
- Merge conflict → STOP, report conflicting files, suggest `git merge --abort`.
- Worktree fallback: If `git worktree list` fails (e.g., shallow clone), run without isolation and warn about potential conflicts.

## Subagent Reference
| Stage | subagent_type | Model | Playbook |
|-------|--------------|-------|----------|
| Build (Plan+Act) | system-architect | default (Opus) | project-plan.md + project-act.md |
| Check-QA | qa-engineer | sonnet | project-check.md |
| Check-Security | security-auditor | sonnet | (inline OWASP audit) |
| Close | repo-maintainer | sonnet | project-done.md |
