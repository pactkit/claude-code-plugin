---
description: "QA verification: security scan, code quality scan, Spec alignment"
allowed-tools: [Read, Bash, Grep, Glob]
---

# Command: Check (v1.3.0 Deep QA)
- **Usage**: `/project-check $ARGUMENTS`
- **Agent**: QA Engineer

> **PRINCIPLE**: Check is a verification-only operation; identify issues but do not fix them.

## Severity Levels

| Level | Name | Action |
|-------|------|--------|
| **P0** | Critical | Must block — security vulnerability, data loss risk, correctness bug |
| **P1** | High | Should fix — logic error, significant violation, performance regression |
| **P2** | Medium | Fix or follow-up — code smell, maintainability concern |
| **P3** | Low | Optional — style, naming, minor suggestion |

## Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go.
1.  **Analyze Context**: Read the active `docs/specs/{ID}.md`.
2.  **Determine Layer**:
    * *Logic Only?* -> Strategy: **API Level**.
    * *UI/DOM/Interaction?* -> Strategy: **Browser Level**.
3.  **Detect Stack**: If changed files include `.tsx`/`.vue`/`.svelte`, also apply frontend-specific checks (component structure, accessibility, rendering performance).
4.  **Gap Analysis**: Do we have a structured Test Case? If not, plan to create one.
5.  **Security Scope**: Check if the Spec contains a `## Security Scope` section.
    - If present: parse the `Applicable` column for each SEC-* check. Pass this scope to Phase 1.
    - If absent (legacy Spec): run `pactkit sec-scope <changed-files>` to auto-detect, or fall back to all 8 checks.

## Phase 1: Security Scan (OWASP+)
> **Config**: If `pactkit.yaml` contains `check.security_checklist: false`, skip this phase and log: "Security checklist disabled via config".
> **Scope**: If `pactkit.yaml` contains `check.security_scope_override: full`, run ALL 8 checks regardless of the Spec's Security Scope. Otherwise, use the scope parsed in Phase 0.

For each SEC-* check:
- If the Security Scope (from Phase 0) marks the check as **Applicable: Yes** (or no scope available): execute the check and output **PASS**, **FAIL**, or **N/A** (not applicable to this story).
- If the Security Scope marks the check as **Applicable: No** or **N/A**: output `SEC-{N}: SKIPPED ({reason from scope table})` — do not execute the check.

Evaluate all applicable code related to the Story against this structured 8-item checklist:

| ID | Category | Check |
|----|----------|-------|
| SEC-1 | Secrets | No hardcoded API keys, tokens, or passwords in source code |
| SEC-2 | Input | All user inputs validated (schema validation or whitelist) |
| SEC-3 | SQL | All database queries use parameterized queries (no string concat) |
| SEC-4 | XSS | User-provided content sanitized before rendering |
| SEC-5 | Auth | Authentication tokens in httpOnly cookies (not localStorage) |
| SEC-6 | Rate | Rate limiting configured on public endpoints |
| SEC-7 | Error | Error messages do not expose stack traces or internal paths |
| SEC-8 | Deps | No known CVEs in dependencies (npm audit / pip-audit clean) |

**Severity rules**:
- Any **FAIL** on SEC-1 through SEC-5 → classify as **P0 Critical** — report immediately, do not wait for full scan.
- Any **FAIL** on SEC-6 through SEC-8 → classify as **P1 High**.

**Additional OWASP patterns to consider**: Injection (SQL/NoSQL/command injection), SSRF (Server-Side Request Forgery), Race Condition / TOCTOU (Time-of-Check-Time-of-Use), path traversal, session fixation. Flag any occurrence as P0 if exploitable.

**Cross-phase linkage (R5.1)**: If the Spec contains `## Implementation Steps` with Risk=High items, prioritize those files for security review.

Include the checklist results in Phase 5 Verdict under `### Security Checklist`.

## Phase 2: Code Quality Scan
Apply a code quality checklist to all code related to the Story:

- **Error Handling**: Swallowed exceptions, overly broad catch, missing error handling, async errors
- **Performance**: N+1 queries, CPU hotspots in hot paths, missing cache, unbounded memory growth
- **Boundary Conditions**: Null/undefined handling, empty collections, off-by-one, division by zero, numeric overflow
- **Logic Correctness**: Does the implementation match Spec intent? Are edge cases handled?

For each finding, assign a severity (P0-P3). Flag issues that may cause silent failures.

## Phase 3: Spec Verification & Test Case Definition (The Law)
1.  **Verify Spec Structure**: Run `pactkit spec-lint docs/specs/{STORY_ID}.md` to validate Spec structure (E006 checks for `## Acceptance Criteria`).
    * *If ERRORs*: WARN the user — "Spec structure issues found. Run `/project-plan` to fix."
    * *If WARNs only*: Note warnings and continue.
2.  **Extract Scenarios**: List all Scenarios from the Spec's `## Acceptance Criteria` section.
3.  **Check**: Does `docs/test_cases/{STORY_ID}_case.md` exist?
4.  **Action**: If missing, generate it based *strictly* on the Spec's Acceptance Criteria.
    * *Format*: Gherkin (Given/When/Then).
    * *Constraint*: Do not write Python code yet.
5.  **Validate Test Case Structure**: Run `pactkit lint-testcase docs/test_cases/{STORY_ID}_case.md` to validate the test case file structure. If errors, WARN the user.
6.  **Coverage Report**: Compare Scenarios in Spec vs Test Cases. Report any uncovered Scenario.

## Phase 3.5: Test Quality Gate
> **Purpose**: Prevent tautological or low-value tests from passing the regression gate unchallenged.

1.  **Identify Story Tests**: Find all test files created or modified for the current Story (use `git diff --name-only` or match `test_{STORY_ID}` / `test_story*` patterns).
2.  **Read & Audit**: Read each test file and check for these anti-patterns:
    - **Tautological assertions** (P1): `assert True`, `assert 1 == 1`, or any assertion that can never fail regardless of implementation correctness.
    - **Missing assertions** (P1): Test functions that execute code but contain no `assert` statement — they pass silently without verifying anything.
    - **Over-mocking** (P2): Test mocks or stubs every dependency so that no real logic is exercised; the test only verifies the mock wiring, not actual behavior.
    - **Happy-path only** (P2): All test methods only cover the success case with no error inputs, boundary conditions, or edge cases tested.
3.  **Report**: For each finding, assign the severity above and include it in the Phase 5 verdict.
4.  **Gate**: If any P1 test quality issue is found, flag it as a required fix (same as a code quality P1).

## Phase 4: E2E Execution (Config-Driven)
> Read `pactkit.yaml` field `e2e.type` to select strategy. Default: `none` (skip).

| e2e.type | Test Path | Tools | Cleanup |
|----------|-----------|-------|---------|
| `none` | Skip — log "E2E skipped" | — | — |
| `cli` | `{e2e.test_dir}/cli/test_{STORY_ID}_cli.py` | pytest + subprocess | pytest `tmp_path` fixture (auto) |
| `frontend` | `{e2e.test_dir}/browser/test_{STORY_ID}_browser.py` | Playwright + MSW mock from `e2e.api_spec` | MSW in-memory interceptors (auto) |
| `backend` | `{e2e.test_dir}/api/test_{STORY_ID}_api.py` | pytest + httpx, contract via `e2e.api_spec` | transaction rollback via fixtures |
| `fullstack` | `{e2e.test_dir}/browser/test_{STORY_ID}_full.py` | docker-compose up + Playwright | `docker-compose down -v` |

* **Playwright MCP**: IF available, use for browser verification (frontend/fullstack).
* **Chrome DevTools MCP**: IF available, use for performance tracing.
* **`e2e.env_file`** (default `.env.test`): Load test credentials (API tokens, DB strings) from this file before running E2E. If file missing, WARN but continue.
* **`e2e.blocking`** (default `false`): If `false`, E2E failures → WARN. If `true`, E2E failures → FAIL (blocks `/project-done`).

## Phase 4.5: PactGuard Compliance Scan (Config-Gated)
> Read `pactkit.yaml` field `check.pactguard.enabled`. Default: `false` (skip).

1.  If `check.pactguard.enabled` is `false` (default) → **silently skip** this phase entirely. Do NOT add a row to the Verdict table.
2.  If enabled: check if `pactguard` CLI is available (`which pactguard`). If not found → silently skip.
3.  Run: `pactguard check --mode {check.pactguard.mode} -r {check.pactguard.ruleset} --json-output <changed_files>`
    - If `check.pactguard.ruleset` is empty, omit the `-r` flag (use PactGuard defaults).
4.  Parse JSON output. Add to Phase 5 Verdict table: `PactGuard | PASS/WARN/FAIL | N violations`
5.  If `check.pactguard.blocking: true` and violations found → contribute FAIL to overall verdict.
6.  If `pactguard` exits with error → add `PactGuard | WARN | execution error` to Verdict. Do NOT block.

## Phase 4.7: Observability Scan (Config-Gated)
> Read `pactkit.yaml` field `check.observe.enabled`. Default: `false` (skip).

1.  If `check.observe.enabled` is `false` (default) → **silently skip** this phase entirely. Do NOT add a row to the Verdict table.
2.  If enabled: detect available MCP sources (`mcp__chrome-devtools__*`, `mcp__playwright__*`). If none available → silently skip.
3.  Collect signals (or run `pactkit observe --json` for structured collection):
    - Chrome DevTools: `list_console_messages`, `list_network_requests` (cap: `check.observe.max_console`, `check.observe.max_network`)
    - Playwright: `browser_take_screenshot` for post-test visual verification
4.  Classify signals by severity (ERROR/WARNING/INFO per R3 in Spec).
5.  Add to Phase 5 Verdict table: `Observability | PASS/WARN/FAIL | N console errors, M network failures`

## Phase 5: The Verdict
1.  **Run Unit (Incremental)**: Run `pactkit test-map <changed-files>` to map source files to test files. Run only mapped tests. Fallback to full suite if no mapping.
2.  **Run E2E**: If `e2e.type` is not `none`, execute the E2E test file created in Phase 4.
3.  **Report**: Output structured verdict:

```
## QA Verdict: STORY-{ID}

**Result**: PASS / FAIL

### Scan Summary
| Category | P0 | P1 | P2 | P3 |
|----------|----|----|----|----|
| Security     |    |    |    |    |
| Quality      |    |    |    |    |
| Test Quality |    |    |    |    |

### Issues (if any)
- **[P0] [file:line]** Description
- **[P1] [file:line]** Description

### Spec Alignment
- [x] S1: ... (Covered)
- [ ] S2: ... (Gap)

### Security Checklist
| ID | Check | Result |
|----|-------|--------|
| SEC-1 | Secrets | PASS/FAIL/N/A |
| SEC-2 | Input | PASS/FAIL/N/A |
| SEC-3 | SQL | PASS/FAIL/N/A |
| SEC-4 | XSS | PASS/FAIL/N/A |
| SEC-5 | Auth | PASS/FAIL/N/A |
| SEC-6 | Rate | PASS/FAIL/N/A |
| SEC-7 | Error | PASS/FAIL/N/A |
| SEC-8 | Deps | PASS/FAIL/N/A |

### Test Results
- Unit: X passed, Y failed
- E2E: X passed, Y failed
```
