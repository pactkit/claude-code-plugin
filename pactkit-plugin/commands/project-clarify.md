---
description: "Standalone requirement clarification before planning"
allowed-tools: [Read, Bash, Glob, Grep]
---

# Command: Clarify (v1.1.0)
- **Usage**: `/project-clarify "$ARGUMENTS"`
- **Agent**: System Architect

> **PURPOSE**: Standalone requirement clarification. Run before `/project-plan` to surface ambiguities and assess risks upfront.

## Phase 1: Ambiguity Analysis
1.  Analyze `$ARGUMENTS` against the AMBIGUITY_SIGNALS checklist (same as Plan Phase 0.7).
2.  Generate 3–6 structured questions (Scope, Users, Constraints, Scale, Edge Cases, Non-Goals).
3.  Ask questions in the user's language.

## Phase 2: Pre-mortem Risk Probe
> **PURPOSE**: Reverse thinking — identify how the plan could fail before it starts.
1.  Based on `$ARGUMENTS` and Phase 1 findings, generate 1–2 pre-mortem questions (pick the most relevant):
    - "If this feature is deemed a failure 1 month after launch, what is the most likely reason?"
    - "What assumptions does this plan rely on? Which assumption is the most fragile?"
    - "What will the person maintaining this code in 6 months complain about the most?"
    - "What is the most likely integration point to break?"
2.  Ask in the user's language, together with Phase 1 questions.
3.  Total questions across Phase 1 + Phase 2 MUST NOT exceed 6. If Phase 1 already has 5–6, pick only 1 pre-mortem question. If Phase 1 has ≤ 4, pick up to 2.

## Phase 3: Clarified Brief Output
1.  After user responses, produce a **Clarified Brief**:
    ```markdown
    ## Clarified Brief: {feature name}
    - **Scope**: {confirmed operations}
    - **Users**: {confirmed target users / roles}
    - **Constraints**: {technical constraints}
    - **Scale**: {performance expectations}
    - **Edge Cases**: {failure scenarios and expected behavior}
    - **Non-Goals**: {explicitly excluded}
    - **Risks**: {top 1-2 identified risks from pre-mortem}
    ```
2.  Output: "Ready for Plan. Run: `/project-plan \"{clarified brief summary}\"`"
