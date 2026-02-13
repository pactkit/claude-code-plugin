---
description: "PR Code Review: structured review with SOLID, security, quality checklists"
allowed-tools: [Read, Bash, Grep, Glob]
---

# Command: Review (v22.0 Deep Code Review)
- **Usage**: `/project-review "$ARGUMENTS"`
- **Agent**: QA Engineer

> **PRINCIPLE**: Review is a read-only operation; do not modify any code files.

## Severity Levels

| Level | Name | Action |
|-------|------|--------|
| **P0** | Critical | Must block merge — security vulnerability, data loss risk, correctness bug |
| **P1** | High | Should fix before merge — logic error, significant SOLID violation, performance regression |
| **P2** | Medium | Fix in this PR or create follow-up — code smell, maintainability concern |
| **P3** | Low | Optional improvement — style, naming, minor suggestion |

## Phase 0: PR Information Retrieval (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block.
1.  **Parse Input**: `$ARGUMENTS` can be a PR number (e.g. `123`) or a full URL.
2.  **Fetch PR Metadata**: Run `gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,files`.
3.  **Fetch PR Diff**: Run `gh pr diff $ARGUMENTS`.
4.  **Extract STORY-ID**: Extract the `STORY-\d+` pattern from the PR title or body (if present).

**Edge cases:**
- **No changes**: If `gh pr diff` is empty, inform user and stop.
- **Large diff (>500 lines)**: Summarize by file first, then review in batches by module/feature area.
- **Mixed concerns**: Group findings by logical feature, not just file order.

## Phase 1: Context Loading
1.  **Spec Alignment** (if STORY-ID found):
    - Read `docs/specs/{STORY-ID}.md`
    - Extract Requirements and Acceptance Criteria
    - These become the **review checklist**
2.  **No Spec** (if no STORY-ID):
    - Review based on general best practices only
    - Note: "No associated Spec found. Reviewing against general standards."
3.  **Detect Stack from Diff**: Check changed file extensions:
    - `.tsx`/`.vue`/`.svelte`/`.css`/`.scss` → Also apply `DEV_REF_FRONTEND` (component, a11y, rendering perf)
    - `.py`/`.go`/`.java`/`.rs` → Also apply `DEV_REF_BACKEND` (API design, data layer, observability)
    - Mixed → Apply both

## Phase 2: SOLID + Architecture Analysis
Apply the SOLID checklist to all changed files:

- **SRP**: Does any changed file own unrelated concerns?
- **OCP**: Are there growing switch/if blocks that should use extension points?
- **LSP**: Do subclasses break parent expectations or require type checks?
- **ISP**: Are interfaces too wide with unused methods?
- **DIP**: Is high-level logic coupled to concrete implementations?

Also check for common code smells: long methods, feature envy, data clumps, primitive obsession, shotgun surgery, dead code, speculative generality, magic numbers.

When proposing refactors, explain *why* it improves cohesion/coupling. For non-trivial refactors, propose an incremental plan.

## Phase 3: Removal Candidates
Identify code that is unused, redundant, or feature-flagged off:

- Distinguish **safe delete now** vs **defer with plan**
- For each candidate, provide: location, rationale, evidence, impact, deletion steps
- Provide a follow-up plan with concrete steps and checkpoints

## Phase 4: Security & Reliability Scan (OWASP+)
Apply the Security checklist to all changed files:

- **Input/Output**: XSS, injection (SQL/NoSQL/command), SSRF, path traversal
- **AuthN/AuthZ**: Missing auth guards, tenant checks, IDOR
- **JWT & Tokens**: Algorithm confusion, weak secrets, missing expiry validation
- **Secrets & PII**: API keys in code/logs, excessive PII logging
- **Supply Chain**: Unpinned deps, dependency confusion, known CVEs
- **Runtime**: Unbounded loops, missing timeouts, resource exhaustion, ReDoS
- **Race Conditions**: TOCTOU, missing locks, concurrent read-modify-write
- **Crypto**: Weak algorithms, hardcoded IVs, encryption without authentication
- **Data Integrity**: Missing transactions, partial writes, missing idempotency

Call out both **exploitability** and **impact** for each finding.

## Phase 5: Code Quality Scan
Apply the Code Quality checklist to all changed files:

- **Error Handling**: Swallowed exceptions, overly broad catch, missing error handling, async errors
- **Performance**: N+1 queries, CPU hotspots in hot paths, missing cache, unbounded memory
- **Boundary Conditions**: Null handling, empty collections, numeric boundaries, off-by-one, unicode
- **Logic Correctness**: Does the change match stated intent? Are edge cases handled?

Flag issues that may cause silent failures or production incidents.

## Phase 6: Review Report
Output the following structured report:

```
## Code Review: PR $ARGUMENTS

### Summary
- **PR**: [title] by [author]
- **Branch**: [head] -> [base]
- **Files reviewed**: X files, Y lines changed
- **Spec**: [STORY-ID or "None"]
- **Overall assessment**: [APPROVE / REQUEST_CHANGES / COMMENT]

---

### P0 - Critical
(none or list with `[file:line]` format)

### P1 - High
- **[file:line]** Brief title
  - Description of issue
  - Suggested fix

### P2 - Medium
...

### P3 - Low
...

---

### Removal/Iteration Plan
(if applicable — use safe-delete vs defer format)

### Spec Alignment
- [x] R1: ... (Implemented)
- [ ] R2: ... (Missing)

### Verdict
**APPROVE** / **REQUEST_CHANGES**
[One-line justification]
```

**Clean review**: If no issues found, explicitly state what was checked and any areas not covered.

## Phase 7: Next Steps Confirmation

After presenting findings, ask user how to proceed:

```
---

## Next Steps

I found X issues (P0: _, P1: _, P2: _, P3: _).

**How would you like to proceed?**

1. **Fix all** — I'll implement all suggested fixes
2. **Fix P0/P1 only** — Address critical and high priority issues
3. **Fix specific items** — Tell me which issues to fix
4. **No changes** — Review complete, no implementation needed

Please choose an option or provide specific instructions.
```

**IMPORTANT**: Do NOT implement any changes until user explicitly confirms. This is a review-first workflow.

## Constraints
- This command is **read-only**. Do NOT modify any files.
- If `gh` CLI is not authenticated, report the error and suggest `gh auth login`.
- If the PR number is invalid, report clearly and stop.
