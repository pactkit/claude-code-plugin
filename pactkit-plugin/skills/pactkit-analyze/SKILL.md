---
name: pactkit-analyze
description: "Cross-artifact consistency check: Spec ↔ Board ↔ Test Cases"
---
# Skill: pactkit-analyze

Run a consistency check between Spec, Sprint Board, and Test Cases for a given Story.

## Usage
```
/pactkit-analyze STORY-XXX
```

## What It Checks
1. **Spec ↔ Board**: Every Requirement (`R{N}`) has a matching Board Task, and every Task traces to a Requirement.
2. **Spec AC ↔ Test Case**: Every Acceptance Criteria item has a corresponding Scenario in the Test Case file.

## Output
Prints an alignment matrix and coverage report. Non-blocking — advisory only.
