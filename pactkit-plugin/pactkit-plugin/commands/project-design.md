---
description: "Product design for greenfield projects: PRD generation, story decomposition, board setup"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Command: Design (v1.3.0 Product Designer)
- **Usage**: `/project-design "$ARGUMENTS"`
- **Agent**: Product Designer

> **PURPOSE**: Transform a product vision into a comprehensive PRD, decompose it into
> implementable Specs, and populate the Sprint Board — bridging the gap between
> "I have an idea" and "I have a prioritized backlog ready for `/project-sprint`."

## 🧠 Phase 0: The Thinking Process
> **Execution Style**: Work through each phase incrementally — output progress as you go. Do NOT try to plan all PRD sections in your head before producing output. Start each section, show your findings, then move to the next.
1.  **Parse Vision**: What is the core product idea? What problem does it solve?
2.  **Identify Domain**: E-commerce, SaaS, internal tool, mobile app, CLI, etc.
3.  **Detect Stack Hints**: Does the user mention specific technologies? (React, Python, Go, etc.)
4.  **Scope Assessment**: Is this a full product or a module within an existing system?

## 🎬 Phase 1: PRD Generation
> **Goal**: Create `docs/product/prd.md` — the single source of truth for the product.

1.  **Scaffold**: Run `{SCAFFOLD_CMD} create_prd "{ProductName}"`.
2.  **Read Scaffolded File**: Read `docs/product/prd.md` before writing content (required — Write/Edit tools cannot modify unread files).
3.  **Fill Sections** — Complete each section in the PRD using **sectional write**: Edit each Group into `prd.md` immediately after completing it, then print a checkpoint before moving on.

### Group A: Product Foundation (Sections 1.1-1.2)

### 1.1 Product Overview
- **Vision**: One-sentence product vision statement
- **Problem Statement**: What pain point does this solve? For whom?
- **Target Users**: Primary and secondary user segments

### 1.2 User Personas (minimum 2)
For each persona, fill:
- **Role**: Job title or user archetype
- **Goals**: What they want to achieve
- **Pain Points**: Current frustrations
- **Jobs-to-be-Done**:
  - *Functional*: What task are they trying to accomplish?
  - *Emotional*: How do they want to feel?
  - *Social*: How do they want to be perceived?

4.  **Edit**: Write Group A content (Sections 1.1-1.2) into `docs/product/prd.md`. Print checkpoint: "Group A written. Proceeding to Group B."

### Group B: Features & Design (Sections 1.3-1.6)

### 1.3 Feature Breakdown (Epics → Stories)
Organize features into Epics. For each Story within an Epic, score:

| Story | Impact (1-5) | Effort (1-5) | Priority (I/E) |
|-------|:------------:|:------------:|:--------------:|
| ...   | ...          | ...          | ...            |

- **Impact**: User value (how much does it matter?) + Business value (revenue, retention, growth)
- **Effort**: Technical complexity + Risk (unknowns, dependencies)
- **Priority**: Impact ÷ Effort — higher is better

### 1.4 Architecture Design
- Draw a system-level Mermaid architecture diagram
- Identify major components: frontend, backend, database, external services
- Note technology recommendations (not mandates)

### 1.5 Page/Screen Design
For each key screen:
- **Purpose**: What user goal does this screen serve?
- **Components**: UI component hierarchy (header, forms, lists, modals, etc.)
- **User Flow**: Step-by-step interaction sequence
- **shadcn Integration (Conditional)**: IF `components.json` exists in the project root, use `mcp__shadcn__search_items_in_registries` to find matching UI components for each page element. Include the shadcn component names (e.g., `@shadcn/button`, `@shadcn/card`) in the component hierarchy.

### 1.6 Prototype Generation
> **Goal**: Generate runnable HTML prototypes for each key page from Section 1.5.

1.  **For each key page** defined in Section 1.5, generate a single self-contained `.html` file:
    - **Tailwind CSS** via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
    - **Lucide Icons** via CDN: `<script src="https://unpkg.com/lucide@latest"></script>`
    - **Vanilla JavaScript** for interactions (click handlers, toggles, form validation)
    - No React, Vue, or any framework — zero build step required
2.  **Write** each prototype to `docs/prototypes/{page-name}.html` (create the directory if needed).
3.  **Content Requirements**:
    - Responsive layout (mobile-first with Tailwind breakpoints)
    - Realistic placeholder content (not "Lorem ipsum" — use domain-relevant text from Personas)
    - Interactive elements wired up (buttons show feedback, forms validate, modals open/close)
    - Call `lucide.createIcons()` at the end of `<body>` to render icons
4.  **Browser Preview (Conditional)**: IF `mcp__playwright__browser_navigate` tool is available, open each prototype in the browser for live preview. IF Playwright MCP is not available, print the file path for manual opening.

5.  **Edit**: Write Group B content (Sections 1.3-1.6) into `docs/product/prd.md`. Print checkpoint: "Group B written. Proceeding to Group C."

### Group C: Technical & Strategy (Sections 1.7-2.0)

### 1.7 API Design
- List endpoints: `METHOD /path → description`
- Define core data models (entity fields and relationships)
- Specify auth strategy (JWT, session, OAuth, API key)

### 1.8 Non-Functional Requirements
- **Performance**: Response time targets, throughput expectations
- **Security**: Auth model, data encryption, OWASP baseline
- **Scalability**: Expected user load, horizontal vs vertical scaling

### 1.9 Success Metrics
Define measurable KPIs per Epic:

| Epic | Metric | Target | How to Measure |
|------|--------|--------|----------------|
| ...  | ...    | ...    | ...            |

### 2.0 MVP Roadmap (Three-Horizon Framework)
Assign each Story to a horizon:

- **Now (Sprint 1-3)**: Core MVP — must-have features to validate the product
- **Next (Sprint 4-8)**: Differentiation — features that create competitive advantage
- **Later (Sprint 9+)**: Scale — platform expansion, optimization, advanced features

6.  **Edit**: Write Group C content (Sections 1.7-2.0) into `docs/product/prd.md`. Print checkpoint: "Group C written. PRD complete."

## 🎬 Phase 2: Architecture
1.  **Update HLD**: Write the architecture Mermaid diagram from Section 1.4 into `docs/architecture/graphs/system_design.mmd`.
2.  **Visualize** (if existing code): Run `{VISUALIZE_CMD} visualize`.

## 🎬 Phase 3: Story Decomposition
> **Goal**: Convert PRD Feature Breakdown into individual Specs.

1.  **Determine STORY IDs**: Run `pactkit next-id` to get the next available STORY-NNN number.
2.  **Sort**: Order stories by horizon (Now → Next → Later), then by Priority Score (descending).
3.  **For each Story**:
    - Run `{SCAFFOLD_CMD} create_spec "STORY-{NNN}" "{title}"`.
    - **Read the scaffolded file** before writing content (required — Write/Edit tools cannot modify unread files).
    - Fill in the Spec:
      - `## Requirements` — using RFC 2119 keywords (MUST/SHOULD/MAY)
      - `## Acceptance Criteria` — Given/When/Then scenarios
      - Add Priority Score to the spec header: `- **Priority**: {score} (Impact {I} / Effort {E})`
4.  **Security Scope**: After filling each Spec, run `pactkit sec-scope <changed-files>` to populate the `## Security Scope` section. If `pactkit sec-scope` is unavailable, manually fill SEC-1 through SEC-8.
5.  **Spec Lint Self-Check**: After each Spec is generated, run `pactkit spec-lint docs/specs/{STORY_ID}.md` (or `python3 -m pactkit spec-lint docs/specs/{STORY_ID}.md` if `pactkit` is not on `$PATH`). If ERRORs found, self-correct and re-run until clean. This prevents malformed Specs from blocking the Sprint pipeline at Act Phase 0.5.
5.  **Batch Checkpoint**: Every 3 Specs completed, print a progress checkpoint (e.g., "3/8 Specs created. Continuing."). This prevents unbounded continuous output.
6.  **Dependency Graph**: Add a Mermaid dependency graph at the end of the PRD showing Story execution order and critical path.

## 🎬 Phase 4: Board Setup
1.  **Add Stories**: For each Story (ordered by horizon → priority):
    - Run `{BOARD_CMD} add_story "STORY-{NNN}" "{title}" "{task list}"`.
2.  **Verify**: Read `docs/product/sprint_board.md` to confirm all stories are listed.

## 🎬 Phase 4.5: Session Context Update
1.  **Update Context**: Run `pactkit context` to regenerate `docs/product/context.md` with the newly created stories and board state.

## 🎬 Phase 5: Handover
1.  **Summary Table**: Output a table of all created artifacts:

| Artifact | Path | Count |
|----------|------|-------|
| PRD | `docs/product/prd.md` | 1 |
| Prototypes | `docs/prototypes/{page-name}.html` | M |
| Specs | `docs/specs/STORY-{NNN}.md` | N |
| Board Entries | `docs/product/sprint_board.md` | N |
| Architecture | `docs/architecture/graphs/system_design.mmd` | 1 |

2.  **Story Overview**: List stories grouped by horizon (Now/Next/Later) with priority scores.
3.  **Handover**: "PRD created. {N} stories ready for `/project-sprint`."

## ⚠️ What This Command Does NOT Do
- Does NOT write implementation code — only PRD, Specs, and architecture design
- Does NOT include market sizing (TAM/SAM/SOM) or pricing strategy — AI cannot produce reliable market data
- Does NOT generate production UI code (React/Vue/Svelte) — prototypes are HTML + Tailwind only, meant for design validation not deployment
- Does NOT enforce a specific tech stack — recommendations only, not mandates
- Does NOT depend on WebSearch — works entirely from user input
