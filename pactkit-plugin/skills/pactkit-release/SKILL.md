---
name: pactkit-release
description: "Version release: snapshot, archive, Git tag, and GitHub Release"
---

# PactKit Release

Version release management — update versions, snapshot architecture, create Git tags, and publish GitHub Releases.

## When Invoked
- **`/project-release` command**: VERSION is passed explicitly from the command's pre-flight check.
- **Standalone / legacy path**: VERSION is not provided — auto-detected from `pyproject.toml`.

## Version Parameter
- If `VERSION` is provided (e.g., by `/project-release`): use it directly, skip auto-detection.
- If version is not provided: auto-detect by running `git diff HEAD~1 pyproject.toml | grep version` and extracting the new value.

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

### 4. GitHub Release (Conditional)
- **Check config**: Read `pactkit.yaml` for `release.github_release`.
  - If `release.github_release: true`: proceed with GitHub Release creation.
  - If `release.github_release: false` or section missing: log "GitHub Release: SKIP — not configured" and stop.
- Extract the `[$VERSION]` section from `CHANGELOG.md` as release notes.
- Create a GitHub Release: `gh release create $VERSION --title "$VERSION" --notes "$NOTES"`.
- Verify: `gh release view $VERSION` confirms the release exists and is marked Latest.
