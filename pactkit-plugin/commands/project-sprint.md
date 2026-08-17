---
description: "Automated PDCA Sprint orchestration via Subagent Team (Slim Team)"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Sprint (v1.5.0 Protocol-Only Orchestrator)
- **Usage**: `/project-sprint "$ARGUMENTS"`
- **Agent**: Team Lead (current session)

> **CORE PRINCIPLE**: Thin Orchestrator — Lead does ZERO file reading, only dispatches.
> Each subagent reads `docs/specs/`, `commands/*.md`, and `docs/product/sprint_board.md` from disk.

## Phase 0: Setup
0. **Mode Detection (STORY-slim-144)**: `$ARGUMENTS` non-empty → single-story mode (proceed below). Empty → Wave Mode (see Wave Mode section).
1. Parse requirement from `$ARGUMENTS`. Run `pactkit next-id` to determine next STORY-ID.
2. `TeamCreate("sprint-{STORY_ID}")`.
3. `TaskCreate` for each stage: Plan (no deps), Act (blockedBy: Plan), Check-QA (blockedBy: Act), Close (blockedBy: Check-QA).
4. Verify worktree support (`git worktree list`). Use `isolation="worktree"` if supported.
5. Read `pactkit.yaml` (check `{PACTKIT_YAML}`), extract `agent_models`: `plan_model=agent_models.get('system-architect','opus')`, `act_model=agent_models.get('senior-developer','sonnet')`. Default: fallback to `sonnet` if model unavailable.

## Phase 1: PDCA Execution

### Stage A: Build

**A1** (`system-architect`, model: opus, isolation="worktree"): Execute `commands/project-plan.md`.
- **Sprint override**: Skip Phase 0.7 Clarify Gate. Use STORY-ID {STORY_ID} (already determined — skip `pactkit next-id`).
- Verify Spec. STOP on failure.

**A2** (`senior-developer`, model: sonnet, isolation="worktree"): Execute `commands/project-act.md`. Merge worktree. STOP on failure.

### Stage B: Check
- Launch `qa-engineer` (model: sonnet, isolation="worktree"): Execute `commands/project-check.md` (includes SEC-1~8 in Phase 1). Report "QA PASS/FAIL".
- Collect reports from worktree. On FAIL: STOP.

### Stage C: Close
- Launch `repo-maintainer` (model: sonnet, isolation="worktree"): Execute `commands/project-done.md`.
- **Sprint overrides**: Skip `pactkit update` in Phase 4. Skip `pactkit visualize --lazy` in Phase 2 (Act already ran it).
- Report "DONE PASS/FAIL". Merge worktree branch on success.

## Phase 2: Cleanup
1. `SendMessage(type="shutdown_request")` to all teammates.
2. `TeamDelete` to remove task directory.
3. Report: Spec path, test results, commit hash, report files.

## Wave Mode (STORY-slim-144)
> Trigger: `/project-sprint` with empty `$ARGUMENTS` — conflict-aware parallel orchestration over the backlog. Scheduling data comes from code (`spec-graph`), NEVER from Lead judgment.

1. **Wave Plan (before any dispatch)**: Run `{BOARD_CMD} list_stories` (BACKLOG IDs) + `pactkit spec-graph --json` (waves + conflicts, deterministic). Filter to backlog IDs with Specs. Partition each wave:
   - **Parallel batch**: declared Touches (no placeholder) AND pairwise non-conflicting per the matrix. Cap: `sprint.max_parallel` from `{PACTKIT_YAML}` (default 3); excess spills to the next sub-batch.
   - **Serialized tail**: same-wave-conflicted or undeclared Touches — run one at a time after the batch. Safe-by-default: unknown conflict surface = NEVER parallelize.
   - If no story is parallelizable, log and suggest single-story mode instead.
2. **Print the wave plan** (wave N: parallel=[...], serialized=[...], skipped=[...] with reasons) and wait for user confirmation before spawning any subagent.
3. **Dispatch**: each story (parallel or serialized) runs the Stage A→B→C chain above in its own worktree — reference those stages verbatim; do NOT redefine them.
4. **Wave Gate**: wave N+1 MUST NOT start until every wave-N story is merged green. Merges are always sequential (one worktree at a time).
5. **Failure policy**: fail-fast — any story failure STOPs the wave; report completed/merged vs pending; NEVER auto-retry. Resume = re-run `/project-sprint` (spec-graph excludes Done stories, so re-runs are idempotent).

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
| Close | repo-maintainer | sonnet | project-done.md |
