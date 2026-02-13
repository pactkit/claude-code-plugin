---
description: "Automated PDCA Sprint orchestration via Subagent Team (Slim Team)"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Sprint (v22.0 Slim Team)
- **Usage**: `/project-sprint "$ARGUMENTS"`
- **Agent**: Team Lead (current session)

> **CORE PRINCIPLE**: Thin Orchestrator + File-Driven Context.
> The Lead does ZERO file reading — only Glob for STORY-ID, then dispatch.
> Each subagent reads `docs/specs/`, `commands/*.md`, and `docs/product/sprint_board.md` from disk.
> Do NOT relay context through conversation — pass STORY-ID and file paths via prompt.

## ⚠️ Model Requirement
> **IMPORTANT**: This command requires the **Opus 4.6** model to orchestrate the Subagent Team.
> If the current model is Sonnet 4, use the manual PDCA workflow instead:
> `/project-plan` → `/project-act` → `/project-check` → `/project-done`

## ⚠️ Model Tiering Prerequisite
> For Bedrock environments, ensure the sonnet model is configured:
> ```bash
> export ANTHROPIC_DEFAULT_SONNET_MODEL='claude-sonnet-4'
> ```
> This enables `model: "sonnet"` for cost-efficient subagents (QA, Security, Closer).

## 🧠 Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block.
> **CRITICAL**: Do NOT use the `Read` tool in this phase. Lead must stay thin.
1.  **Analyze**: Parse the requirement from `$ARGUMENTS`.
2.  **STORY-ID**: Determine next available ID by scanning `docs/specs/` using **Glob only** (not Read).
3.  **Strategy**: Plan the 3-stage Slim Team orchestration (Build → Check → Close).

## 🎬 Phase 1: Team Setup
1.  **Create Team**: `TeamCreate("sprint-{STORY_ID}")`.
2.  **Create Tasks**: Use `TaskCreate` for each phase:
    - Task: "Build — Plan + TDD Implementation" (no dependencies)
    - Task: "Check-QA — Spec Verification" (blockedBy: Build)
    - Task: "Check-Security — OWASP Audit" (blockedBy: Build)
    - Task: "Close — Archive & Commit" (blockedBy: Check-QA, Check-Security)

## 🎬 Phase 2: Slim PDCA Execution

### Stage A: Build (Plan + Act merged)
> **WHY MERGED**: The architect who designs the spec has the best codebase understanding.
> Keeping Plan+Act in one agent eliminates 1 context fork and 1 round-trip,
> while preserving continuity — the builder validates spec feasibility during implementation.

1.  **Launch**: `Task(subagent_type="system-architect")`
    - **prompt**:
      ```
      You are the Builder (System Architect + Senior Developer).
      STORY-ID: {STORY_ID}
      Requirement: {$ARGUMENTS}

      Execute TWO phases in sequence:
      1. PLAN: Read `commands/project-plan.md` and execute it. Create `docs/specs/{STORY_ID}.md`.
      2. ACT: Read `commands/project-act.md` and execute it. Implement with TDD. All tests must be GREEN.

      When done, write a summary to `docs/product/reports/{STORY_ID}-build.md` and
      report a single line: "BUILD PASS" or "BUILD FAIL: <reason>"
      ```
2.  **Wait**: For subagent completion.
3.  **Verify**: Confirm `docs/specs/{STORY_ID}.md` was created (Glob, not Read).
4.  **On Failure**: STOP orchestration. Report failure to user. Do NOT proceed.
5.  **Update**: `TaskUpdate(build_task, status=completed)`.

### Stage B: Check (PARALLEL)
> **CRITICAL**: Launch BOTH subagents in a SINGLE message (parallel tool calls).

1.  **Launch QA**: `Task(subagent_type="qa-engineer", model="sonnet")`
    - **prompt**:
      ```
      You are the QA Engineer.
      STORY-ID: {STORY_ID}
      Spec: `docs/specs/{STORY_ID}.md`

      Read `commands/project-check.md` and execute your full playbook.
      When done, write a report to `docs/product/reports/{STORY_ID}-qa.md` and
      report a single line: "QA PASS" or "QA FAIL: <reason>"
      ```
2.  **Launch Security** (same message): `Task(subagent_type="security-auditor", model="sonnet")`
    - **prompt**:
      ```
      You are the Security Auditor.
      STORY-ID: {STORY_ID}
      Spec: `docs/specs/{STORY_ID}.md`

      Audit all code related to {STORY_ID}. Focus on OWASP top 10 vulnerabilities.
      When done, write a report to `docs/product/reports/{STORY_ID}-security.md` and
      report a single line: "SECURITY PASS" or "SECURITY FAIL: <reason>"
      ```
3.  **Wait**: For BOTH subagents to complete.
4.  **On Failure**: If either reports FAIL, STOP. Report to user.
5.  **Update**: `TaskUpdate(check tasks, status=completed)`.

### Stage C: Close
1.  **Launch**: `Task(subagent_type="repo-maintainer", model="sonnet")`
    - **prompt**:
      ```
      You are the Repo Maintainer.
      STORY-ID: {STORY_ID}
      Spec: `docs/specs/{STORY_ID}.md`

      Read `commands/project-done.md` and execute your full playbook.
      Report a single line: "DONE PASS" or "DONE FAIL: <reason>"
      ```
2.  **Wait**: For subagent completion.
3.  **Update**: `TaskUpdate(close_task, status=completed)`.

## 🎬 Phase 3: Cleanup
1.  **Shutdown**: Send `SendMessage(type="shutdown_request")` to all teammates.
2.  **Delete Team**: `TeamDelete` to remove `~/.claude/tasks/sprint-{STORY_ID}/`.
3.  **Report**: Output final summary to user:
    - Spec path
    - Test results
    - Commit hash (if created)
    - Reports: `docs/product/reports/{STORY_ID}-*.md`

## ⚠️ Error Handling
- If ANY stage fails, **STOP immediately**. Do NOT proceed to the next stage.
- Report the failure phase, subagent output, and suggest manual intervention.
- Always run `TeamDelete` in cleanup, even on failure.

## 📋 Subagent Type Reference
| Phase | subagent_type | Model | Playbook |
|-------|--------------|-------|----------|
| Build (Plan+Act) | system-architect | default (Opus) | project-plan.md + project-act.md |
| Check-QA | qa-engineer | sonnet | project-check.md |
| Check-Security | security-auditor | sonnet | (inline OWASP audit) |
| Close | repo-maintainer | sonnet | project-done.md |

## 📊 Token Efficiency (vs v21.0)
| Metric | v21.0 (5 agents) | v22.0 Slim (4 agents) |
|--------|------------------|----------------------|
| Context forks | 5 | 4 |
| Lead context at fork | ~50-95K (growing) | ~15-17K (flat) |
| Duplication overhead | ~370K tokens | ~64K tokens |
| Parallelism | Check only | Check only (same) |
| Cost reduction | Baseline | ~83% overhead + sonnet tiering |
