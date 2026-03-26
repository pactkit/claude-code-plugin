# PactKit — Claude Code Plugin

Spec-driven agentic DevOps toolkit for [Claude Code](https://claude.com/claude-code). This repository contains the **plugin format** distribution of [PactKit](https://github.com/pactkit/pactkit-public).

## What is PactKit?

PactKit compiles development workflows, role-based agents, and behavioral governance into executable "constitutions" and "playbooks" for Claude Code. It enforces a PDCA (Plan → Do → Check → Act) cycle with strict TDD, spec-driven development, and multi-agent orchestration.

## Installation

### Option A: Claude Code Plugin (this repo)

Copy the `pactkit-plugin/` directory into your project:

```bash
cp -r pactkit-plugin/.claude-plugin /path/to/your/project/
cp pactkit-plugin/CLAUDE.md /path/to/your/project/.claude/
cp -r pactkit-plugin/agents /path/to/your/project/.claude/
cp -r pactkit-plugin/commands /path/to/your/project/.claude/
cp -r pactkit-plugin/skills /path/to/your/project/.claude/
```

### Option B: PyPI (recommended)

Install via pip and let PactKit deploy automatically:

```bash
pip install pactkit
pactkit init
```

See the [main repository](https://github.com/pactkit/pactkit-public) for full documentation.

## What's Included

| Directory | Contents | Count |
|-----------|----------|-------|
| `agents/` | Role-based AI agent definitions | 9 |
| `commands/` | PDCA command playbooks | 11 |
| `skills/` | Specialized skill modules | 10 |
| `CLAUDE.md` | Global constitution (behavioral rules) | 1 |

### Commands

| Command | Description |
|---------|-------------|
| `/project-plan` | Analyze requirements, create Spec and Story |
| `/project-act` | Implement code per Spec with strict TDD |
| `/project-check` | QA verification: security scan, code quality |
| `/project-done` | Code cleanup, board update, Git commit |
| `/project-sprint` | Automated PDCA orchestration via subagent team |
| `/project-hotfix` | Lightweight fast-fix path |
| `/project-design` | Greenfield product design and PRD generation |
| `/project-release` | Version release: snapshot, archive, Git tag |
| `/project-pr` | Push branch and create pull request |
| `/project-init` | Initialize project scaffolding |
| `/project-clarify` | Standalone requirement clarification |

### Agents

| Agent | Role |
|-------|------|
| `system-architect` | High-level design and planning |
| `senior-developer` | TDD implementation specialist |
| `qa-engineer` | Quality assurance and test cases |
| `repo-maintainer` | Release engineering and housekeeping |
| `product-designer` | PRD and story decomposition |
| `code-explorer` | Deep code analysis and tracing |
| `security-auditor` | OWASP security review |
| `visual-architect` | Draw.io diagram generation |
| `system-medic` | Project health diagnostics |

## Links

- [PactKit Main Repo](https://github.com/pactkit/pactkit-public)
- [PyPI](https://pypi.org/project/pactkit/)
- [Documentation](https://pactkit.dev)

## License

MIT
