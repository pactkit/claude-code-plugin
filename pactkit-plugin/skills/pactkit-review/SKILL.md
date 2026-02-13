---
name: pactkit-review
description: "PR Code Review with structured SOLID, security, and quality checklists"
---

# PactKit Review

Structured PR code review with severity-ranked findings.

## When Invoked
- **Check Phase 4** (PR variant): When `/project-check` is given a PR number/URL.
- **Sprint Stage B**: As part of automated QA in Sprint orchestration.

## Severity Levels
| Level | Name | Action |
|-------|------|--------|
| **P0** | Critical | Must block merge |
| **P1** | High | Should fix before merge |
| **P2** | Medium | Fix in PR or follow-up |
| **P3** | Low | Optional improvement |

## Protocol

### 1. PR Information
- Fetch PR metadata: `gh pr view $ARG --json title,body,author,baseRefName,headRefName,files`
- Fetch PR diff: `gh pr diff $ARG`
- Extract STORY-ID from title/body if present.

### 2. Review Checklists
- **SOLID**: SRP, OCP, LSP, ISP, DIP analysis on changed files.
- **Security**: OWASP baseline (injection, auth, secrets, XSS, SSRF).
- **Quality**: Error handling, performance, boundary conditions, logic correctness.

### 3. Report
```
## Code Review: PR $ARG
**Result**: APPROVE / REQUEST_CHANGES
### Issues
- [P0] [file:line] Description
- [P1] [file:line] Description
### Spec Alignment
- [x] R1: Implemented
- [ ] R2: Missing
```

> **CONSTRAINT**: This skill is read-only. Do not modify code files.
