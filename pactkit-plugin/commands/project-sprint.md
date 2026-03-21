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
1. Parse requirement from `$ARGUMENTS`. Run `pactkit next-id` to determine next STORY-ID.
2. `TeamCreate("sprint-{STORY_ID}")`.
3. `TaskCreate` for each stage: Plan (no deps), Act (blockedBy: Plan), Check-QA (blockedBy: Act), Check-Security (blockedBy: Act), Close (blockedBy: both Checks).
4. Verify worktree support (`git worktree list`). Use `isolation="worktree"` if supported.
5. Read `pactkit.yaml` (check `{PACTKIT_YAML}`), extract `agent_models`: `plan_model=agent_models.get('system-architect','opus')`, `act_model=agent_models.get('senior-developer','sonnet')`. Default: fallback to `sonnet` if model unavailable.

## Phase 1: PDCA Execution

### Stage A: Build

**A1** (`system-architect`, model: opus, isolation="worktree"): Execute `commands/project-plan.md`. Verify Spec. STOP on failure.

**A2** (`senior-developer`, model: sonnet, isolation="worktree"): Execute `commands/project-act.md`. Merge worktree. STOP on failure.

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
| Plan | system-architect | opus (agent_models) | project-plan.md |
| Act  | senior-developer | sonnet (agent_models) | project-act.md |
| Check-QA | qa-engineer | sonnet | project-check.md |
| Check-Security | security-auditor | sonnet | (inline OWASP audit) |
| Close | repo-maintainer | sonnet | project-done.md |
