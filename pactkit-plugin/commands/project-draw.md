---
description: "Generate Draw.io XML architecture diagrams (supporting multiple diagram types)"
allowed-tools: [Read, Write]
---

# Command: Draw (v22.0 Enterprise)
- **Usage**: `/project-draw "$ARGUMENTS"`
- **Agent**: Visual Architect

## Phase 0: The Thinking Process (Mandatory)
> **INSTRUCTION**: Output a `<thinking>` block before using any tools.

### Step 1: Detect Diagram Type
Classify the user request into one of these types:

| Type | Trigger Keywords | Layout |
|------|-----------------|--------|
| **architecture** | architecture, system, layered, microservice, layers | Top -> Bottom (vertical layers) |
| **dataflow** | dataflow, process, pipeline, ETL, flow | Left -> Right (horizontal) |
| **deployment** | deployment, infra, cloud, k8s, docker, VPC | Grouped (nested containers) |

### Step 2: Identify Components
- Classify each component from user input into a style role (see Style Dictionary below).
- For each pair of components, identify the connection type (sync/async) and protocol label.

### Step 3: Plan Layout
- **Architecture**: Arrange in horizontal layers. Top = Client/User, Middle = Service, Bottom = Data.
- **Dataflow**: Arrange left to right. Source -> Process -> Sink.
- **Deployment**: Use Container nodes to group related services. Nest child nodes inside containers.

## Enterprise Style Dictionary
> **CRITICAL RULE**: Every style string MUST include `html=1;whiteSpace=wrap;`.

### Node Styles

| Role | Shape | Style String |
|------|-------|-------------|
| **Input/Start** (Green) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#2ecc71;strokeColor=#27ae60;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Process/Service** (Blue) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#1f497d;strokeColor=#c7c7c7;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Decision/Logic** (Orange) | Rhombus | `rhombus;whiteSpace=wrap;html=1;fillColor=#f39c12;strokeColor=#e67e22;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Output/End** (Red) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#e74c3c;strokeColor=#c0392b;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Storage/DB** (Purple) | Cylinder | `shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#8e44ad;strokeColor=#7d3c98;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Container/Group** (Light Gray) | Dashed Rect | `rounded=1;whiteSpace=wrap;html=1;container=1;collapsible=0;fillColor=#f5f5f5;strokeColor=#666666;dashed=1;fontStyle=1;fontFamily=Helvetica;verticalAlign=top;` |
| **External System** (Dark Gray) | Rounded Rect | `rounded=1;whiteSpace=wrap;html=1;fillColor=#636363;strokeColor=#424242;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Queue/MessageBus** (Teal) | Parallelogram | `shape=parallelogram;whiteSpace=wrap;html=1;fillColor=#16a085;strokeColor=#0e6655;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Actor/User** (Blue) | Person | `shape=mxgraph.basic.person;whiteSpace=wrap;html=1;fillColor=#3498db;strokeColor=#2980b9;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;` |
| **Note/Annotation** (Yellow) | Note | `shape=note;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#333333;fontStyle=0;fontFamily=Helvetica;size=15;` |

### Edge Styles

| Type | Style String |
|------|-------------|
| **Standard** (Sync) | `edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;` |
| **Async/Return** (Dashed) | `edgeStyle=orthogonalEdgeStyle;dashed=1;rounded=1;strokeColor=#8e44ad;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;` |

> **Edge Labels**: Set the `value` attribute on edge `mxCell` to the protocol name (e.g., `value="REST"`, `value="gRPC"`, `value="Event"`).


## Layout Patterns

### Architecture (Top -> Bottom)
- **Layer 0** (y=40): Client / Actor / External
- **Layer 1** (y=200): Gateway / API / Load Balancer
- **Layer 2** (y=360): Service / Business Logic
- **Layer 3** (y=520): Storage / Database / Cache
- **Horizontal spacing**: dx=220 within each layer
- **Node size**: width=160, height=60

### Dataflow (Left -> Right)
- **Zone 0** (x=40): Source / Input
- **Zone 1** (x=300): Processing / Transform
- **Zone 2** (x=560): Output / Sink
- **Vertical spacing**: dy=120 within each zone
- **Node size**: width=160, height=60

### Deployment (Grouped)
- Use **Container** nodes as parent groups (width=400+, height=auto)
- Place child nodes inside containers (set `parent` attribute to Container id)
- **Container spacing**: dx=450 between groups
- **Inner spacing**: dx=40, dy=80 inside container


## Anti-Bug Rules (Mandatory)
- **Anti-Bug 1**: `mxGeometry` MUST be a child element of `mxCell`, never self-closing `mxCell`.
- **Anti-Bug 2**: Labels with special chars MUST be XML-escaped (e.g., `&lt;br&gt;`, `&amp;`).
- **Anti-Bug 3**: Every `id` MUST be unique across the entire diagram. Use prefixes like `n_`, `e_`, `c_` for nodes, edges, containers.
- **Anti-Bug 4**: Edge `mxCell` MUST have valid `source` and `target` attributes pointing to existing node ids.
- **Anti-Bug 5**: Child nodes inside a Container MUST set `parent="<container_id>"`, not `parent="1"`.
- **Anti-Bug 6**: The root `mxCell` with `id="0"` and layer `mxCell` with `id="1" parent="0"` are mandatory boilerplate. Never omit them.
- **Anti-Bug 7**: Container nodes MUST include `container=1` in their style. Otherwise children won't nest properly.


## Legend (Optional)
Only add a Legend when the user explicitly requests one, or when the diagram uses more than 4 distinct node types. If needed, place it at the bottom-right corner of the diagram to avoid overlapping content nodes.

## Execution Protocol
1. **Classify**: Detect diagram type (architecture / dataflow / deployment).
2. **Component List**: Extract components, assign style roles.
3. **Layout**: Choose the matching layout pattern and compute (x, y) for each node.
4. **Generate XML**: Write the final `.drawio` file using the template below.

## XML Template (Landscape, No Legend)
```xml
<mxfile host="Electron" agent="PactKit-v20.0" version="26.2.2">
  <diagram name="Architecture" id="PACTKIT_ARCH">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Add nodes and edges here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 📝 Few-shot Example (4-Node Architecture with Container and Edge Labels)

Below is a complete example of a simple API architecture diagram:

```xml
<mxfile host="Electron" agent="PactKit-v20.0" version="26.2.2">
  <diagram name="Example" id="EXAMPLE_001">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="n_user" value="User" style="shape=mxgraph.basic.person;whiteSpace=wrap;html=1;fillColor=#3498db;strokeColor=#2980b9;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="100" y="40" width="80" height="80" as="geometry" />
        </mxCell>
        <mxCell id="c_backend" value="Backend Services" style="rounded=1;whiteSpace=wrap;html=1;container=1;collapsible=0;fillColor=#f5f5f5;strokeColor=#666666;dashed=1;fontStyle=1;fontFamily=Helvetica;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="40" y="200" width="400" height="180" as="geometry" />
        </mxCell>
        <mxCell id="n_api" value="API Gateway" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2ecc71;strokeColor=#27ae60;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="c_backend">
          <mxGeometry x="20" y="50" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="n_svc" value="Auth Service" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1f497d;strokeColor=#c7c7c7;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="c_backend">
          <mxGeometry x="220" y="50" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="n_db" value="PostgreSQL" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#8e44ad;strokeColor=#7d3c98;fontColor=#ffffff;fontStyle=1;fontFamily=Helvetica;" vertex="1" parent="1">
          <mxGeometry x="260" y="460" width="160" height="80" as="geometry" />
        </mxCell>
        <mxCell id="e_user_api" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;" edge="1" source="n_user" target="n_api" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_api_svc" value="gRPC" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;" edge="1" source="n_api" target="n_svc" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_svc_db" value="SQL" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#e67e22;strokeWidth=2;html=1;fontFamily=Helvetica;fontSize=10;" edge="1" source="n_svc" target="n_db" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

This example demonstrates: Container grouping (`c_backend`), Actor node (`n_user`), edge labels (`HTTPS`, `gRPC`, `SQL`), unique id prefixes, proper parent nesting, and landscape canvas.
