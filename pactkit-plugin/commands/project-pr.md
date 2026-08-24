---
description: "Execute project-pr through Core-owned bounded WorkUnits"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: project-pr — Managed WorkUnit Facade
- **Usage**: /project-pr "$ARGUMENTS"


## Pre-Final Protocol (MUST)
Run and obey `pactkit workflow contract project-pr --json`. Before final run `pactkit workflow finish-guard <run-id> --json`: `continue_current_turn` means continue; only `done`/`await_user` ends. Progress is not final.

Core is the only workflow scheduler and completion authority for this command.

1. Start with `pactkit work-unit start project-pr --goal "$ARGUMENTS"`.
2. Run `pactkit-codex-work-unit run <run-id> --owner codex`. The runner persists
   and resumes one App Server thread, dispatches only the current Core WorkUnit,
   and submits structured EvidenceReceipts for deterministic validation.
3. If the runner returns `retry`, invoke the same run command again; Core versions
   the failed or expired lease and resumes at the same WorkUnit.
4. If it returns `await_user`, show the listed manual operations and wait for explicit
   authorization. Resume with one `--authorize <operation>` per approved operation.
5. `done` is valid only after Core's journaled finalizer accepts the terminal WorkUnit.

Never select, skip, or mark a WorkUnit complete from prose. Never call the finalizer
from inside a model turn. Do not perform commit, push, tag, publish, release, pull-request,
or orchestration operations unless the runner received matching explicit authorization.
Portable/manual hosts may acquire and submit one WorkUnit at a time and must use
`pactkit work-unit finalize-workflow` for non-Plan terminal units.
Canonical portable methods remain discoverable under `{SKILLS_ROOT}/`; their
legacy checkpoint files are compatibility evidence only and never schedule managed runs.

