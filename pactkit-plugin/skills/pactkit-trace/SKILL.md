---
name: pactkit-trace
description: "Deep code tracing and execution flow analysis"
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
- Read `docs/architecture/graphs/call_graph.mmd` to see all reachable functions.

### 3. Deep Tracing
- Follow call chain file by file, recording data transformations.
- Note how data structures change (e.g., `dict` -> `UserObj` -> `JSON`).

### 4. Visual Synthesis
Output a **Mermaid Sequence Diagram** to visualize the flow.

### 5. Archaeologist Report
- **Patterns**: Design Patterns used.
- **Debt**: Hardcoded values, complex logic, lack of tests.
- **Key Files**: Top 3 files critical to this feature.
