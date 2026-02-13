---
name: pactkit-scaffold
description: "File scaffolding: create Spec, test files, E2E tests, Git branches, Skills"
---

# PactKit Scaffold

Project file scaffolding tool for quickly creating standardized project files.

## Prerequisites
- `docs/specs/` directory must exist (required by `create_spec`)
- `tests/unit/` and `tests/e2e/` directories must exist (required by test scaffolding)
- Git repository must be initialized (required by `git_start`)

## Command Reference

### create_spec -- Create a Spec file
```
python3 scripts/scaffold.py create_spec ITEM-ID "Title"
```
- `ITEM-ID`: Work item identifier, e.g. `STORY-001`, `HOTFIX-001`, `BUG-001`
- `Title`: Spec title
- Output: `docs/specs/{ITEM-ID}.md` (with template structure)

### create_test_file -- Create a unit test
```
python3 scripts/scaffold.py create_test_file src/module.py
```
- Automatically generates the corresponding test file based on the source file path
- Output: `tests/unit/test_module.py`

### create_e2e_test -- Create an E2E test
```
python3 scripts/scaffold.py create_e2e_test ITEM-ID "scenario_name"
```
- Output: `tests/e2e/test_{ITEM-ID}_{scenario}.py`

### git_start -- Create a Git branch
```
python3 scripts/scaffold.py git_start ITEM-ID
```
- Branch prefix is inferred from the item type:
  - `STORY-*` → `feature/STORY-*`
  - `HOTFIX-*` → `fix/HOTFIX-*`
  - `BUG-*` → `fix/BUG-*`

### create_skill -- Create a Skill directory scaffold
```
python3 scripts/scaffold.py create_skill skill-name "Description of the skill"
```
- `skill-name`: Skill identifier (must start with lowercase letter: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`)
- `Description`: Brief description for SKILL.md frontmatter
- Output: `~/.claude/skills/{skill-name}/` with `SKILL.md`, `scripts/{clean_name}.py`, `references/.gitkeep`
- Refuses to overwrite if the skill directory already exists

## Usage Scenarios
- `/project-plan`: Use `create_spec` to create a Spec template
- `/project-act`: Use `create_test_file` to create test scaffolding
- `/project-check`: Use `create_e2e_test` to create E2E tests
- Ad-hoc: Use `create_skill` to scaffold a new reusable skill
