---
description: "QA verification: security scan, code quality scan, Spec alignment"
allowed-tools: [Read, Bash, Grep, Glob]
---

# Command: Check (v22.0 Deep QA)
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

## Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block before using any tools.
1.  **Analyze Context**: Read the active `docs/specs/{ID}.md`.
2.  **Determine Layer**:
    * *Logic Only?* -> Strategy: **API Level**.
    * *UI/DOM/Interaction?* -> Strategy: **Browser Level**.
3.  **Detect Stack**: If changed files include `.tsx`/`.vue`/`.svelte`, also consult `DEV_REF_FRONTEND` for client-side security and rendering performance checks.
4.  **Gap Analysis**: Do we have a structured Test Case? If not, plan to create one.

## Phase 1: Security Scan (OWASP+)
Apply a comprehensive security checklist to all code related to the Story:

- **Input/Output Safety**: XSS, Injection (SQL/NoSQL/command), SSRF, path traversal
- **AuthN/AuthZ**: Missing auth guards, tenant checks, IDOR, session fixation
- **Race Condition**: TOCTOU (check-then-act), concurrent read-modify-write, missing locks
- **Secrets & PII**: API keys in code/logs, excessive PII logging, hardcoded credentials
- **Runtime Risks**: Unbounded loops, missing timeouts, resource exhaustion, ReDoS
- **Cryptography**: Weak algorithms (MD5/SHA1), hardcoded IVs, encryption without authentication
- **Supply Chain**: Unpinned dependencies, dependency confusion, known CVEs

For each finding, assign a severity (P0-P3) and note both exploitability and impact.
If a P0 issue is found, report it immediately — do not wait for the full scan.

## Phase 2: Code Quality Scan
Apply a code quality checklist to all code related to the Story:

- **Error Handling**: Swallowed exceptions, overly broad catch, missing error handling, async errors
- **Performance**: N+1 queries, CPU hotspots in hot paths, missing cache, unbounded memory growth
- **Boundary Conditions**: Null/undefined handling, empty collections, off-by-one, division by zero, numeric overflow
- **Logic Correctness**: Does the implementation match Spec intent? Are edge cases handled?

For each finding, assign a severity (P0-P3). Flag issues that may cause silent failures.

## Phase 3: Spec Verification & Test Case Definition (The Law)
1.  **Verify Spec Structure**: Read `docs/specs/{STORY_ID}.md`.
    * *Check*: Does the Spec contain `## Acceptance Criteria` with Given/When/Then Scenarios?
    * *If missing*: WARN the user — "Spec lacks structured Acceptance Criteria. Run `/project-plan` to fix."
2.  **Extract Scenarios**: List all Scenarios from the Spec's `## Acceptance Criteria` section.
3.  **Check**: Does `docs/test_cases/{STORY_ID}_case.md` exist?
4.  **Action**: If missing, generate it based *strictly* on the Spec's Acceptance Criteria.
    * *Format*: Gherkin (Given/When/Then).
    * *Constraint*: Do not write Python code yet.
5.  **Coverage Report**: Compare Scenarios in Spec vs Test Cases. Report any uncovered Scenario.

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

## Phase 4: Layered Execution
Choose the strategy identified in Phase 0:

### Strategy A: API Level (Fast & Stable)
* **Context**: Backend logic, calculations.
* **Action**: Create/Run `tests/e2e/api/test_{STORY_ID}.py` using `pytest` + `requests`.

### Strategy B: Browser Level (Visual & Real)
* **Context**: UI, DOM, User Flows.
* **Action**:
    1.  **Check Tool**: Is `playwright` installed?
    2.  Create/Run `tests/e2e/browser/test_{STORY_ID}_browser.py`.
    * *Note*: Use `--headless` unless debugging.
* **Playwright MCP (Conditional)**: IF `mcp__playwright__browser_snapshot` tool is available, prefer using Playwright MCP for browser-level verification:
    - Use `browser_navigate` to load the target page
    - Use `browser_snapshot` to capture the accessibility tree (preferred over screenshots for assertions)
    - Use `browser_click` and `browser_fill_form` for interaction testing
    - Use `browser_take_screenshot` for visual evidence
* **Chrome DevTools MCP (Conditional)**: IF `mcp__chrome-devtools__take_snapshot` tool is available, use Chrome DevTools MCP for runtime diagnostics:
    - Use `performance_start_trace` (with `reload: true, autoStop: true`) to capture Core Web Vitals and performance insights
    - Use `list_console_messages` (filter by `types: ["error", "warn"]`) to detect runtime errors
    - Use `list_network_requests` to verify API calls and detect failed requests

## Phase 5: The Verdict
1.  **Run Suite**: Execute the specific test file created above (Story E2E test).
2.  **Run Unit (Incremental)**: Run only unit tests related to changed modules, not the full suite.
    - **Identify changed modules**: `git diff --name-only HEAD` to list modified source files.
    - **Map to related tests**: Use `test_map_pattern` in `LANG_PROFILES` to find corresponding test files.
    - **Run incremental**: Execute only the mapped test files.
    - **Fallback**: If no test mapping can be determined, fall back to full `pytest tests/unit/`.
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

### Test Results
- Unit: X passed, Y failed
- E2E: X passed, Y failed
```
