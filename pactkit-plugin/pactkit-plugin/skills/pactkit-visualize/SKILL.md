---
name: pactkit-visualize
description: "Generate project code dependency graph (Mermaid), supporting file-level, class-level, function-level, and module-level analysis"
---

# PactKit Visualize

Generate project code relationship graphs (Mermaid format), supporting four analysis modes.

> **Script location**: Use the base directory from the skill invocation header to resolve script paths.

## Prerequisites
- The project must have Python source files (`.py`) to generate meaningful graphs
- The `docs/architecture/graphs/` directory is automatically created by `init_arch`

## Command Reference

### visualize -- Generate code dependency graph
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pactkit-visualize/scripts/visualize.py visualize [--mode file|class|call|module] [--entry <func>] [--focus <module>]
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--mode file` | File-level dependency graph (inter-module import relationships) | Default |
| `--mode class` | Class diagram (including inheritance) | - |
| `--mode call` | Function-level call graph | - |
| `--mode module` | Module-level dependency graph with weighted cross-module edges | - |
| `--entry <func>` | BFS transitive chain tracing from specified function (requires `--mode call`) | - |
| `--focus <module>` | Scope scan to a specific module directory (works with file, class, call modes) | - |

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
| `--mode module` | `docs/architecture/graphs/module_graph.mmd` | graph TD |
| `--focus` (file) | `docs/architecture/graphs/focus_file_graph.mmd` | graph TD |
| `--focus` (class) | `docs/architecture/graphs/focus_class_graph.mmd` | classDiagram |
| `--focus` (call) | `docs/architecture/graphs/focus_call_graph.mmd` | graph TD |

## Usage Scenarios
- `/project-plan`: Run `visualize` to understand current project state before making design decisions
- `/project-act`: Run `visualize --focus <module>` to understand dependencies of the modification target
- `pactkit-doctor` skill: Run `visualize` to check whether architecture graphs can be generated correctly
- `pactkit-trace` skill: Run `visualize --mode call --entry <func>` to trace call chains
