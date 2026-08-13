---
description: "Push branch and create pull request via gh CLI"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: PR (v1.4.0)
- **Usage**: `/project-pr`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: Pre-flight Check
1.  **Branch Check**:
    - Run `git branch --show-current` to get current branch name
    - If branch is `main` or `master`: print "Skipping PR: working on main branch" → STOP
2.  **Existing PR Check**:
    - Run `gh pr list --head <branch> --state open --json number` to check for existing PR
    - If PR exists: print "PR already open: <URL>" → STOP
    - If `gh` CLI unavailable: print "⚠️ gh CLI not available — cannot create PR" → STOP
3.  **Story Detection**: Infer active Story ID from branch name (e.g., `feature/STORY-051-desc` → `STORY-051`).

## 🎬 Phase 1: Push Assurance
1.  **Check Remote**: If remote tracking branch does not exist, run `git push -u origin <branch>`.
2.  **If push fails**: STOP and report the error.

## 🎬 Phase 2: PR Generation
1.  **Generate PR Title**: Format `{type}({scope}): {spec_title}`
    - `type`: `feat` for STORY, `fix` for BUG/HOTFIX
    - `scope`: infer from primary modified directory
    - `spec_title`: extract from `# {ID}: {Title}` heading in Spec (strip the ID prefix)
    - Max 70 characters
2.  **Generate PR Body**: Extract from Spec and test results:
    ```markdown
    ## Summary
    {1-3 sentences from Spec ## Background}

    ## Changes
    {R1, R2, ... from Spec ## Requirements, one bullet each with MUST/SHOULD/MAY}

    ## Acceptance Criteria
    {AC1, AC2, ... as checklist items — mark [x] if a test for it passed}

    ## Test Results
    - Unit: {N} passed, {N} failed
    - E2E: {N} passed, {N} failed

    ## Spec
    - [{STORY_ID}](docs/specs/{STORY_ID}.md)

    🤖 Generated with [Claude Code](https://claude.com/claude-code)
    ```
3.  **User Confirmation**: Show the PR title + body preview. Ask: "Create this PR? (yes/no/edit)"
    - `yes` → execute `gh pr create --title "..." --body "..."`
    - `no` → skip
    - `edit` → accept user feedback, regenerate, ask again
4.  **Output**: Print PR URL on success.
