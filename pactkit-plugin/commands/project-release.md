---
description: "Version release: snapshot, archive, Git tag, and GitHub Release"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Command: Release (v1.4.0)
- **Usage**: `/project-release`
- **Agent**: Repo Maintainer

## 🧠 Phase 0: Pre-flight Check
1.  **Version Detection**: Check if `pyproject.toml` version was changed vs the previous commit.
    - Run `git diff HEAD~1 pyproject.toml | grep version` (or vs branch base)
    - Capture the new version value (e.g., `1.4.1`).
    - If no version change detected: print "ℹ️ No version bump detected. Update `pyproject.toml` version before releasing." and STOP.
2.  **Read Config**: Read `pactkit.yaml` to detect stack and release configuration.

## 🎬 Phase 1: Invoke pactkit-release Skill
1.  **Delegate to skill**: Invoke the `pactkit-release` skill with `VERSION={version}` from Phase 0.
    - The skill handles the full release protocol:
      Version Update → Spec Backfill → Architecture Snapshot → Git Operations → GitHub Release.
    - Pass the detected version so the skill skips its own auto-detection step.
