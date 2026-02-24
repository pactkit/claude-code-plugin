---
name: pactkit-board
description: "Sprint Board atomic operations: add Story, update Task, archive completed Stories"
---

# PactKit Board

Atomic operations tool for Sprint Board (`docs/product/sprint_board.md`).

> **Script location**: Use the base directory from the skill invocation header to resolve script paths. Classic deployment: `${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py`

## Prerequisites
- `docs/product/sprint_board.md` must exist (created by `/project-init`)
- `docs/product/archive/` directory is used for archiving (automatically created by the archive command)

## Command Reference

### add_story -- Add a work item (Story, Hotfix, or Bug)
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py add_story ITEM-ID "Title" "Task A|Task B"
```
- `ITEM-ID`: Work item identifier, e.g. `STORY-001`, `HOTFIX-001`, `BUG-001`
- `Title`: Item title
- `Task A|Task B`: Task list, use `|` as separator for multiple tasks
- Output: `✅ Story ITEM-ID added` or `❌` error message

### update_task -- Update Task status
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py update_task ITEM-ID "Task Name"
```
- `Task Name`: Must be an exact match with the task name in the Board
- Changes `- [ ] Task Name` to `- [x] Task Name`
- Output: `✅ Task updated` or `❌ Task not found`

### archive -- Archive completed Stories
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py archive
```
- Moves all Stories with every task marked `[x]` to `docs/product/archive/archive_YYYYMM.md`

### list_stories -- View current Stories
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py list_stories
```

### update_version -- Update version number
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py update_version 1.0.0
```

### snapshot -- Architecture snapshot
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py snapshot "v1.0.0"
```
- Saves current architecture graphs to `docs/architecture/snapshots/{version}_*.mmd`

### fix_board -- Relocate misplaced stories to correct sections
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py fix_board
```
- Scans for stories outside their correct section and relocates them based on task status:
  - All `[ ]` → `## 📋 Backlog`
  - Mixed `[ ]`/`[x]` → `## 🔄 In Progress`
  - All `[x]` → `## ✅ Done`
- Output: `✅ Board fixed: N stories relocated.` or `✅ No misplaced stories found.`

## Usage Scenarios
- `/project-plan`: Use `add_story` to create a Story
- `/project-act`: Use `update_task` to mark completed tasks
- `/project-done`: Use `archive` to archive completed Stories
- `pactkit-release` skill: Use `update_version` + `snapshot` to publish a release
- `pactkit-doctor` skill: Use `fix_board` to repair misplaced stories
