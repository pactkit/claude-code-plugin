---
name: pactkit-board
description: "Sprint Board atomic operations: add Story, update Task, archive completed Stories"
model: haiku
---

# PactKit Board

Atomic operations tool for sharded Story facts (`docs/product/stories/{ITEM_ID}.yaml`). `docs/product/sprint_board.md` is an optional read-only projection.

> **Script location**: Use the base directory from the skill invocation header to resolve script paths.

## Prerequisites
- PactKit Core must provide the `StoryRepository` schema used by every adapter.
- Commands modify one Story record only. Run `render` explicitly to update the optional projection.

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
- Changes only the matching task in the Story YAML record.
- Output: `✅ Task updated` or `❌ Task not found`

### archive -- Archive completed Stories
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py archive
```
- Marks completed Story records as `archived`; no shared archive file is appended.

### list_stories -- View current Stories
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py list_stories
```

### render -- Explicitly generate/check Board projection
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py render
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-board/scripts/board.py render --check
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
- Rebuilds the deterministic projection from Story records; it never parses the projection as facts.

## Usage Scenarios
- `/project-plan`: Use `add_story` to create a Story
- `/project-act`: Use `update_task` to mark completed tasks
- `/project-done`: Use `archive` to archive completed Stories
- `pactkit-release` skill: Use `snapshot` to archive architecture graphs during release
- `pactkit-doctor` skill: Use `fix_board` to repair misplaced stories
