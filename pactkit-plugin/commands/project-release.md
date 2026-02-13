---
description: "Version release: snapshot, archive, Tag"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Release (v20.0)
- **Usage**: `/project-release "$ARGUMENTS"`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block.
1.  **Audit**: Are all Stories archived? Is the Board clean?
2.  **Version**: Validate semantic version format.

## 🎬 Phase 1: Version Update
1.  **Update Meta**: Run `python3 ~/.claude/skills/pactkit-board/scripts/board.py update_version "$ARGUMENTS"`.
2.  **Update Stack**: Update the project's package manifest version (see `LANG_PROFILES` package_file; e.g., `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`).
3.  **Backfill Specs**: Scan `docs/specs/*.md` for any Spec with `Release: TBD`. For each one whose Story is completed (archived or all tasks done), update the line to `- **Release**: $ARGUMENTS`.

## 🎬 Phase 2: Architecture Snapshot
1.  **Sync Graphs**:
    - `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize`
    - `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize --mode class`
    - `python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize --mode call`
2.  **Snapshot**: Run `python3 ~/.claude/skills/pactkit-board/scripts/board.py snapshot "$ARGUMENTS"`.
    - *Result*: Saves graphs to `docs/architecture/snapshots/{version}_*.mmd`.

## 🎬 Phase 3: Git Operations
1.  **Archive**: Run `python3 ~/.claude/skills/pactkit-board/scripts/board.py archive`.
2.  **Commit**: `git commit -am "chore(release): $ARGUMENTS"`.
3.  **Tag**: `git tag $ARGUMENTS`.
