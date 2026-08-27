---
description: "Sequential PDCA in the current session"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Sprint (Current-Session PDCA Orchestrator)
- **Usage**: `/project-sprint "$ARGUMENTS"`
- **Execution**: Continue sequentially in this conversation. Keep all phase
  evidence in the current session unless the user explicitly chooses another
  supported execution mode.

## Resolve work

In single-story mode, resolve an existing Story ID from the argument. For a new
requirement, run `pactkit generate-id`, carry that STORY-ID into Plan, and use
its `docs/specs/{STORY_ID}.md` as the file-driven contract.

In Wave Mode (empty arguments), inspect the board and `pactkit spec-graph
--json` to produce a deterministic Wave Plan. Process eligible Stories
sequentially by dependency order. Do not use `max_parallel` unless the user
explicitly requests parallel execution; unknown or conflicting touch surfaces
remain serialized.

## Phase capsule lifecycle

Keep exactly one active phase. Before entering a phase, use the host Read tool
to read its managed capsule below; do not treat this list as Markdown imports:

- Plan: `{SKILLS_ROOT}/_rules/phases/plan-contract.md`
- Act: `{SKILLS_ROOT}/_rules/phases/act-contract.md`
- Check: `{SKILLS_ROOT}/_rules/phases/check-contract.md`
- Done: `{SKILLS_ROOT}/_rules/phases/done-contract.md`

Then execute the corresponding native command playbook in order:

1. Plan — create or update the Spec and Story.
2. Act — implement and produce fresh, adequate behavior evidence.
3. Check — perform QA for security, quality, scope, tests, and Spec alignment.
4. Done — close the Story only when requested external effects are authorized.

When a phase finishes, mark its capsule historical and activate only the next
capsule. A failed Check returns to Act for repair in this same session. Missing
evidence makes completion incomplete; it does not lock reading, implementation,
testing, or repair and does not require restarting Sprint.

## Completion

Report the active Story, changed files, phase evidence, tests, and remaining
gaps. Never infer success from an old workflow state or an agent response.
