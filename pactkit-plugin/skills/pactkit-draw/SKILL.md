---
name: pactkit-draw
description: "Generate Draw.io XML architecture diagrams"
---

# PactKit Draw

Generate system architecture diagrams using Draw.io XML. Supports architecture, dataflow, and deployment diagram types.

## When Invoked
- **Plan Phase 2** (Design): Generate architecture diagrams on demand.
- **Design Phase 2** (Architecture): Visualize system-level design.

## Protocol

### 1. Detect Diagram Type
| Type | Trigger Keywords | Layout |
|------|-----------------|--------|
| **architecture** | architecture, system, layered | Top -> Bottom |
| **dataflow** | dataflow, process, pipeline | Left -> Right |
| **deployment** | deployment, infra, cloud, k8s | Grouped |

### 2. Identify Components
Classify each component into a style role (Input, Process, Decision, Output, Storage, Container, External).

### 3. Generate XML
Write the `.drawio` file following the Enterprise Style Dictionary and Anti-Bug Rules.

## Anti-Bug Rules
- Every `mxCell` style MUST include `html=1;whiteSpace=wrap;`.
- Every `id` MUST be unique (use prefixes: `n_`, `e_`, `c_`).
- Edge `mxCell` MUST have valid `source` and `target` attributes.
- Container nodes MUST include `container=1` in their style.

## MCP Mode (Conditional)
IF `open_drawio_xml` tool is available (Draw.io MCP):
1. Generate XML as usual and write to `.drawio` file (primary output).
2. Call `open_drawio_xml` with the generated XML content to open it in Draw.io editor for instant preview.
3. Optionally call `open_drawio_mermaid` to open existing `.mmd` files in Draw.io for interactive editing.

IF Draw.io MCP tools are NOT available:
- Fallback to the current behavior — write `.drawio` file to disk only.
