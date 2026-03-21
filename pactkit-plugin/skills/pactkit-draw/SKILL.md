---
name: pactkit-draw
description: "Generate Draw.io XML architecture diagrams"
---

# PactKit Draw

Generate system architecture diagrams using Draw.io XML.

## Enterprise Style Dictionary

Copy these style strings exactly — do NOT improvise styles:

| Role | Style String |
|------|-------------|
| **Input** | `rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;` |
| **Process** | `rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;` |
| **Decision** | `rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;` |
| **Output** | `rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;` |
| **Storage** | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#e1d5e7;strokeColor=#9673a6;` |
| **Container** | `swimlane;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;fillColor=#f5f5f5;strokeColor=#666666;` |
| **External** | `rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#ffe6cc;strokeColor=#d79b00;` |
| **Edge** | `edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;` |

## XML Template

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram name="Page-1" id="diag_1">
    <mxGraphModel dx="1000" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- NODES HERE: id="n_1", id="n_2", ... -->
        <!-- EDGES HERE: id="e_1", id="e_2", ... -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Node Template

```xml
<mxCell id="n_1" value="Label" style="STYLE_STRING" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

## Edge Template

```xml
<mxCell id="e_1" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="n_1" target="n_2">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Protocol

1. **Detect Type**: architecture (top→bottom), dataflow (left→right), deployment (grouped)
2. **List Components**: Name each, assign Role from style dictionary
3. **Layout**: Place nodes on grid (x/y multiples of 20), connect with edges
4. **Write File**: Output complete XML to `.drawio` file

## Anti-Bug Rules

- Every style MUST end with `html=1;` (already in dictionary)
- Every `id` MUST be unique: `n_` prefix for nodes, `e_` for edges, `c_` for containers
- Edge `source` and `target` MUST reference existing node IDs
- Container children: set `parent="c_1"` (container ID), not `parent="1"`

## MCP Mode

IF `open_drawio_xml` tool available:
1. Write `.drawio` file
2. Call `open_drawio_xml` with XML content for instant preview
3. Optionally call `open_drawio_mermaid` to open existing `.mmd` files in Draw.io

IF MCP tools NOT available:
- Fallback to file write only (no editor preview)
