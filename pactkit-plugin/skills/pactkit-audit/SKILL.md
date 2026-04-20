---
name: pactkit-audit
description: "H1-H7 AI Readiness Assessment — harness audit scoring and hotspot analysis"
---

# PactKit Audit

H1-H7 AI Coding Harness readiness assessment. Scans project structure against a 7-layer model, produces a Harness Score (0-100), and identifies code hotspots.

## When Invoked
- **Done Phase 8** (Harness Audit Refresh): Auto-invoked via `pactkit audit --append`.
- **Standalone**: Ad-hoc project health assessment.
- **Headless / Frontend integration**: Called as `/pactkit-audit` via Claude Code headless mode.

## The 7 Layers

| Layer | Name | What It Checks |
|-------|------|----------------|
| H1 | Prompt Engineering | CLAUDE.md, rules, agents, commands |
| H2 | Context Engineering | Specs, test cases, architecture graphs |
| H3 | Process Governance | Sprint board, PDCA workflow artifacts |
| H4 | Tool Governance | Skills, CLI tools, MCP integration |
| H5 | Safety & Guardrails | Pre-commit hooks, security rules, credential guards |
| H6 | Observability | Logging, cost tracking, lessons, self-audit rules |
| H7 | Evolution | Version management, changelog, CI/CD publish |

## Scoring
- Each layer scores **L0-L3** (None → Basic → Structured → Advanced).
- **Harness Score** = sum(all 7 levels) / 21 × 100.
- **AI Ready** = min(all 7 levels) ≥ L1.

## Protocol

### 1. Run Audit
```bash
pactkit audit
```
- Outputs: scorecard + top hotspots (concise by default).
- Output file: `docs/architecture/governance/harness_audit.json`.

### 2. Options
| Flag | Purpose |
|------|---------|
| `--json` | JSON output only (machine-readable) |
| `--layer H1-H7` | Check a single layer |
| `--append` | Silent update for `/project-done` integration |
| `--if-needed STORY_ID` | Only refresh when `harness_audit.json` exists and its `story_id` matches; skips otherwise |
| `--verbose` | Full detail: findings + insights + hotspots |

### 3. Interpret Results
- **Score < 50**: Major gaps — address weakest layer first.
- **Score 50-80**: Functional but room for improvement.
- **Score > 80**: Strong harness — focus on hotspot refinement.
- **Hotspots**: Files ranked by composite score (complexity, blast radius, fan-in, test coverage, smells).

### 4. Suggested Tasks
When hotspots are detected and `developer` is configured in `pactkit.yaml`, the audit generates suggested task entries that can be added to the sprint board.

## Usage Scenarios
- `/project-done`: Run `pactkit audit --append --if-needed {STORY_ID}` — only refreshes if the audit belongs to this story; silently skips otherwise.
- Sprint planning: Run `pactkit audit --verbose` to identify technical debt priorities.
- CI integration: Run `pactkit audit --json` for machine-readable pipeline checks.
- Frontend dashboard: Call `/pactkit-audit` via headless mode for real-time project health.
