---
name: pactkit-release
description: "Version release: snapshot, archive, and Git tag"
---

# PactKit Release

Version release management — update versions, snapshot architecture, create Git tags.

## When Invoked
- **Done Phase 4** (release variant): When a version bump story is being closed.
- Standalone release workflow when cutting a new version.

## Protocol

### 1. Version Update
- Run `update_version "$VERSION"` via pactkit-board skill.
- Update the project's package manifest (e.g., `pyproject.toml`, `package.json`).
- Backfill Specs: scan `docs/specs/*.md` for `Release: TBD` and update completed ones.

### 2. Architecture Snapshot
- Run `visualize` (all three modes: file, class, call).
- Run `snapshot "$VERSION"` via pactkit-board skill.
- Result: graphs saved to `docs/architecture/snapshots/{version}_*.mmd`.

### 3. Git Operations
- Run `archive` via pactkit-board skill.
- Commit: `git commit -am "chore(release): $VERSION"`.
- Tag: `git tag $VERSION`.
