---
name: pactkit-visualize
description: "Generate project code dependency graph (Mermaid), supporting file-level, class-level, function-level, and module-level analysis"
model: haiku
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
| `--focus <module>` | Scope scan to a specific module directory. **MUST** be an exact module name from the project (e.g., `pactkit`, `app`), not a keyword or concept. Run without `--focus` first to see available modules. | - |

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

## Graph Query Protocol

> **MUST NOT `Read` a full `.mmd` graph file** — graph files are large (50K–120K, 1000–2000+ lines). Full reads waste tokens before any work begins.

### Codegraph Mode (when `graph_provider: codegraph` in pactkit.yaml)

Setup: `codegraph init` (first time), `codegraph sync` (after code changes).
When codegraph MCP server is running, file changes auto-sync (2-second debounce).

```bash
# Unified pactkit query (reads .codegraph/codegraph.db):
pactkit query --callers atomic_write
pactkit query --callees deploy
pactkit query --chain atomic_write       # transitive upstream
pactkit query --chain deploy --down      # transitive downstream

# Direct codegraph CLI (richer features):
codegraph callers <symbol>
codegraph callees <symbol>
codegraph impact <symbol> --depth 3      # transitive impact radius
codegraph query <search> --kind function # FTS5 symbol search
codegraph context <task>                 # task-focused context builder
codegraph affected <files...>            # find affected test files
codegraph status                         # check index health
```

MCP tools (if codegraph MCP server configured): `codegraph_callers`, `codegraph_callees`, `codegraph_impact`, `codegraph_trace`, `codegraph_context`.

### Grep Mode (default — when graph_provider not set, use .mmd files)

```bash
grep " --> .*deployer" docs/architecture/graphs/code_graph.mmd  # fan-in (importers)
grep "deployer.* --> " docs/architecture/graphs/code_graph.mmd  # fan-out (deps)
grep " --> .*deployer" docs/architecture/graphs/code_graph.mmd | wc -l  # count
grep "my_func" docs/architecture/graphs/call_graph.mmd  # call-level
grep "MyClass" docs/architecture/graphs/class_graph.mmd  # class-level
```

**Fallback rule**: If grep returns 0 results, fall back to full `Read`.
