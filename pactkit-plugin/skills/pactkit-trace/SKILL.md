---
name: pactkit-trace
description: "Deep code tracing and execution flow analysis"
model: sonnet
---

# PactKit Trace

Deep code analysis and execution path tracing via static analysis.

## When Invoked
- **Plan Phase 1** (Archaeology): Trace existing logic before designing changes.
- **Act Phase 1** (Precision Targeting): Confirm call sites before touching code.

## Protocol

### 1. Feature Discovery
- Use `Grep` to locate entry points (API route, CLI arg, Event handler).
- Map core files involved — don't read everything yet.

### 2. Call Graph Analysis
- Run `visualize --mode call --entry <function_name>` to obtain call chains.
- Query callers/callees: use `pactkit query --callers/--callees <func>` (when graph_provider: codegraph), or grep `docs/architecture/graphs/call_graph.mmd`.

### 3. Deep Tracing
- Follow call chain file by file, recording data transformations.
- Note how data structures change (e.g., `dict` -> `UserObj` -> `JSON`).

#### Layered Output: Interface Summary vs Full Implementation

| Module Role | Output Level | How |
|-------------|-------------|-----|
| Target (to be modified) | Full implementation | `Read <file>` |
| Related (dependency, not modified) | Interface summary | `pactkit interface-summary <file>` |

For related (non-target) modules, run `pactkit interface-summary <file>` instead of reading full source. This CLI command uses AST parsing to output only signatures + types + docstrings — function bodies are excluded by code, not by prompt instruction.

If `pactkit` is not on `$PATH`, use `python3 -m pactkit interface-summary <file>`.

### 4. Visual Synthesis
Output a **Mermaid Sequence Diagram** to visualize the flow.

### 5. Topology-Aware Trace (Conditional)
If `detect_topology(root)` returns topologies beyond PDCA/Service:

**Frontend API Topology** (if `api_call` detected):
- Run `api_convention_summary(root)` to get path prefixes, fetch function names, total call count.
- Include conventions in output so downstream code uses the correct API path prefix (e.g., `/api/v1/`) and fetch wrapper (e.g., `apiFetch`).
- Flag any dynamic paths (`[dynamic]` markers) that may need special handling.

**Agent Topology** (if `agent` detected):
- AgentParser extracts orchestration from: LangGraph `StateGraph` (stdlib ast), YAML agent definitions, MCP server configs.
- Include agent nodes and `orchestrates` edges in the report.
- Flag multi-strategy merge results — agents may appear in multiple sources but are deduplicated.

### 6. Archaeologist Report
- **Patterns**: Design Patterns used.
- **Debt**: Hardcoded values, complex logic, lack of tests.
- **Key Files**: Top 3 files critical to this feature.
- **API Conventions** (if frontend): Path prefixes, fetch functions, call count.
- **Agent Flow** (if agents): Orchestration graph, delegation chains.
