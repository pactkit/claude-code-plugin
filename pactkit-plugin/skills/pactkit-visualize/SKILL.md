---
name: pactkit-visualize
description: "Generate project code dependency graph (Mermaid), supporting file-level, class-level, and function-level call chain analysis"
---

# PactKit Visualize

Generate project code relationship graphs (Mermaid format), supporting three analysis modes.

> **Script location**: Use the base directory from the skill invocation header to resolve script paths. Classic deployment: `${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py`

## Prerequisites
- The project must have Python source files (`.py`) to generate meaningful graphs
- The `docs/architecture/graphs/` directory is automatically created by `init_arch`

## Command Reference

### visualize -- Generate code dependency graph
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize [--mode file|class|call] [--entry <func>] [--focus <module>]
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--mode file` | File-level dependency graph (inter-module import relationships) | Default |
| `--mode class` | Class diagram (including inheritance) | - |
| `--mode call` | Function-level call graph | - |
| `--entry <func>` | BFS transitive chain tracing from specified function (requires `--mode call`) | - |
| `--focus <module>` | Focus on call relationships of specified module (requires `--mode call`) | - |

### init_arch -- Initialize architecture directory
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py init_arch
```
- Creates `docs/architecture/graphs/` and `docs/architecture/governance/`
- Generates placeholder file `system_design.mmd`

### list_rules -- List governance rules
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py list_rules
```
- Outputs the list of rule files under `docs/architecture/governance/`

## Output Files

| Mode | Output Path | Mermaid Type |
|------|-------------|-------------|
| `--mode file` | `docs/architecture/graphs/code_graph.mmd` | graph TD |
| `--mode class` | `docs/architecture/graphs/class_graph.mmd` | classDiagram |
| `--mode call` | `docs/architecture/graphs/call_graph.mmd` | graph TD |
| `--focus` | `docs/architecture/graphs/focus_graph.mmd` | graph TD |

## Usage Scenarios
- `/project-plan`: Run `visualize` to understand current project state before making design decisions
- `/project-act`: Run `visualize --focus <module>` to understand dependencies of the modification target
- `/project-doctor`: Run `visualize` to check whether architecture graphs can be generated correctly
- `/project-trace`: Run `visualize --mode call --entry <func>` to trace call chains
