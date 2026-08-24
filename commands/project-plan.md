---
description: "Analyze requirements, create Spec and Story through bounded WorkUnits"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Plan — WorkUnit Compatibility Facade
- **Usage**: /project-plan "$ARGUMENTS"
- **Agent**: System Architect


## Pre-Final Protocol (MUST)
Run and obey `pactkit workflow contract project-plan --json`. Before final run `pactkit workflow finish-guard <run-id> --json`: `continue_current_turn` means continue; only `done`/`await_user` ends. Progress is not final.

This entry preserves the existing user command while Core owns all workflow
state, validators, governance writes, greenfield routing, and completion decisions.
If Core classifies the request as greenfield, present its /project-design redirect;
the host must not duplicate or override that routing decision.

1. Start or resume with pactkit work-unit start project-plan --goal "$ARGUMENTS".
2. On Codex App Server, run `pactkit-codex-work-unit run <run-id> --owner codex`.
   The managed runner reuses one persisted thread, obtains a structured candidate Receipt from
   each turn, and asks Core for every next WorkUnit. On other hosts or when App Server is
   unavailable, acquire exactly one WorkUnit with `pactkit work-unit acquire`.
3. When the leased unit is `story_identity`, bind the allocated ID with `pactkit work-unit
   bind-story <run-id> <story-id> --owner <owner> --idempotency-key <key>` before receipt submission.
4. Invoke only the canonical Portable Method named by that unit and obey its read/write scope.
5. The Codex runner and `pactkit work-unit submit` both submit only an untrusted EvidenceReceipt.
   Core rereads files, runs validators, and computes fingerprints before selecting the next unit.
6. A host final records only an ExecutionAttempt; it never completes the WorkflowRun.
7. On Codex App Server, the managed runner is the sole finalizer: the `finalize_plan`
   turn returns Story identity, title, and ordered tasks but MUST NOT invoke
   `pactkit work-unit finalize-plan` or write governance projections. The adapter
   performs that journaled transaction exactly once with a Unit-version key.
   Portable/manual hosts only invoke `pactkit work-unit finalize-plan` themselves.

Never select or skip the next unit, duplicate completion logic, write Board or context
outside finalize-plan, or rely on a Stop hook. Hosts without verified thread resume
present the returned next WorkUnit for manual resume.
