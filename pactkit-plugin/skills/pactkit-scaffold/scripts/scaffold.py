import re, os, sys, json, datetime, argparse, subprocess, shutil, ast
from pathlib import Path

def nl(): return chr(10)

# --- GIT ---
_BRANCH_PREFIX_MAP = {
    'STORY': 'feature',
    'HOTFIX': 'fix',
    'BUG': 'fix',
}

def git_start(story_id):
    clean_id = story_id.replace('[', '').replace(']', '').upper()
    prefix = clean_id.split('-')[0] if '-' in clean_id else ''
    branch_type = _BRANCH_PREFIX_MAP.get(prefix, 'feature')
    b = f'{branch_type}/{clean_id}'
    try: subprocess.run(['git', 'checkout', '-b', b], check=True)
    except: pass
    return f'✅ Branch: {b}'

# --- TEST ---
def create_test_file(path):
    p = Path.cwd() / path
    t = Path.cwd() / 'tests/unit' / f'test_{p.name}'
    if not t.parent.exists(): t.parent.mkdir(parents=True, exist_ok=True)
    c = ['import pytest', f'# Test {p.name}', 'def test_basic(): assert True']
    t.write_text(nl().join(c), encoding='utf-8')
    return f'✅ Test: {t}'

def create_e2e(story, name):
    safe = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    p = Path.cwd() / f'tests/e2e/test_{story}_{safe}.py'
    if not p.parent.exists(): p.parent.mkdir(parents=True, exist_ok=True)
    c = ['import pytest', f'# E2E {story}', 'def test_e2e(): assert True']
    p.write_text(nl().join(c), encoding='utf-8')
    return f'✅ E2E: {p}'

# --- SPEC ---
def create_spec(i, t):
    p = Path.cwd() / f'docs/specs/{i}.md'
    if not p.parent.exists(): p.parent.mkdir(parents=True, exist_ok=True)
    c = nl().join([
        f'# Spec {i}: {t}',
        '- **Release**: TBD',
        '',
        '## Context',
        '> Background description',
        '',
        '## Requirements',
        '> Use RFC 2119 keywords (MUST/SHOULD/MAY)',
        '',
        '- The system MUST ...',
        '- The system SHOULD ...',
        '',
        '## Acceptance Criteria',
        '> Given/When/Then format',
        '',
        '### Scenario 1: [Name]',
        '- **Given** [precondition]',
        '- **When** [action]',
        '- **Then** [expected result]',
        '',
        '## Design',
        '> Technical approach',
        '',
        '## Target Call Chain',
        '> Call chain trace',
    ])
    p.write_text(c, encoding='utf-8')
    return '✅ Spec Created'

# --- SKILL ---
_SKILL_NAME_RE = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$')

def create_skill(name, desc, base_dir=None):
    if not _SKILL_NAME_RE.match(name):
        return '❌ Invalid skill name: must match [a-z0-9-]+'
    base = Path(base_dir) if base_dir else Path.home() / '.claude' / 'skills'
    root = base / name
    if root.exists():
        return f'❌ Skill already exists: {root}'
    clean = name.replace('-', '_')
    title = name.replace('-', ' ').title()
    # directories
    (root / 'scripts').mkdir(parents=True, exist_ok=True)
    (root / 'references').mkdir(parents=True, exist_ok=True)
    # SKILL.md
    skill_md = nl().join([
        '---',
        f'name: {name}',
        f'description: "{desc.replace(chr(34), chr(92)+chr(34))}"',
        '---',
        '',
        f'# {title}',
        '',
        f'{desc}',
        '',
        '## Prerequisites',
        '- [List prerequisites here]',
        '',
        '## Command Reference',
        '',
        '### [command_name] -- [Brief description]',
        '```',
        f'python3 scripts/{clean}.py [subcommand] [args]',
        '```',
        '',
        '## Usage Scenarios',
        '- [Describe when and how this skill is used]',
        '',
    ])
    (root / 'SKILL.md').write_text(skill_md, encoding='utf-8')
    # script skeleton
    script = nl().join([
        'import argparse',
        '',
        '# --- CLI ---',
        "if __name__ == '__main__':",
        '    parser = argparse.ArgumentParser()',
        "    sub = parser.add_subparsers(dest='cmd', required=True)",
        '    # Add subcommands here',
        '',
        '    a = parser.parse_args()',
        '',
    ])
    (root / 'scripts' / f'{clean}.py').write_text(script, encoding='utf-8')
    # references/.gitkeep
    (root / 'references' / '.gitkeep').write_text('', encoding='utf-8')
    return f'✅ Skill: {root}'

# --- PRD ---
def create_prd(product_name):
    p = Path.cwd() / 'docs' / 'product' / 'prd.md'
    if not p.parent.exists(): p.parent.mkdir(parents=True, exist_ok=True)
    c = nl().join([
        f'# Product Requirements Document: {product_name}',
        '- **Version**: 1.0',
        f'- **Date**: {datetime.date.today().isoformat()}',
        '',
        '---',
        '',
        '## 1. Product Overview',
        '',
        '### 1.1 Vision',
        '> One-sentence product vision statement.',
        '',
        '### 1.2 Problem Statement',
        '> What pain point does this solve? For whom?',
        '',
        '### 1.3 Target Users',
        '- **Primary**: [user segment]',
        '- **Secondary**: [user segment]',
        '',
        '---',
        '',
        '## 2. User Personas',
        '',
        '### Persona 1: [Name]',
        '- **Role**: [Job title or archetype]',
        '- **Goals**: [What they want to achieve]',
        '- **Pain Points**: [Current frustrations]',
        '- **Jobs-to-be-Done**:',
        '  - *Functional*: [What task are they trying to accomplish?]',
        '  - *Emotional*: [How do they want to feel?]',
        '  - *Social*: [How do they want to be perceived?]',
        '',
        '### Persona 2: [Name]',
        '- **Role**: [Job title or archetype]',
        '- **Goals**: [What they want to achieve]',
        '- **Pain Points**: [Current frustrations]',
        '- **Jobs-to-be-Done**:',
        '  - *Functional*: [What task are they trying to accomplish?]',
        '  - *Emotional*: [How do they want to feel?]',
        '  - *Social*: [How do they want to be perceived?]',
        '',
        '---',
        '',
        '## 3. Feature Breakdown',
        '',
        '### Epic 1: [Name]',
        '',
        '| Story | Description | Impact (1-5) | Effort (1-5) | Priority (I/E) | Horizon |',
        '|-------|-------------|:------------:|:------------:|:--------------:|---------|',
        '| S1    | ...         | ?            | ?            | ?              | Now     |',
        '| S2    | ...         | ?            | ?            | ?              | Next    |',
        '',
        '### Epic 2: [Name]',
        '',
        '| Story | Description | Impact (1-5) | Effort (1-5) | Priority (I/E) | Horizon |',
        '|-------|-------------|:------------:|:------------:|:--------------:|---------|',
        '| S3    | ...         | ?            | ?            | ?              | Later   |',
        '',
        '---',
        '',
        '## 4. Architecture Design',
        '',
        '```mermaid',
        'graph TD',
        '    Client[Client / Browser] --> API[API Gateway]',
        '    API --> Service[Business Logic]',
        '    Service --> DB[(Database)]',
        '```',
        '',
        '### Tech Stack Recommendations',
        '- **Frontend**: [framework]',
        '- **Backend**: [language/framework]',
        '- **Database**: [type]',
        '- **Infrastructure**: [hosting]',
        '',
        '---',
        '',
        '## 5. Page/Screen Design',
        '',
        '### Page: [Name]',
        '- **Purpose**: [What user goal does this screen serve?]',
        '- **Components**: [UI component hierarchy]',
        '- **User Flow**: [Step-by-step interaction sequence]',
        '',
        '---',
        '',
        '## 6. API Design',
        '',
        '### Endpoints',
        '| Method | Path | Description |',
        '|--------|------|-------------|',
        '| GET    | /api/... | ... |',
        '| POST   | /api/... | ... |',
        '',
        '### Data Models',
        '> Define core entities, fields, and relationships.',
        '',
        '### Auth Strategy',
        '> JWT / Session / OAuth / API Key',
        '',
        '---',
        '',
        '## 7. Non-Functional Requirements',
        '',
        '- **Performance**: [response time targets, throughput]',
        '- **Security**: [auth model, encryption, OWASP baseline]',
        '- **Scalability**: [expected load, scaling strategy]',
        '',
        '---',
        '',
        '## 8. Success Metrics',
        '',
        '| Epic | Metric | Target | How to Measure |',
        '|------|--------|--------|----------------|',
        '| Epic 1 | [KPI] | [target value] | [measurement method] |',
        '| Epic 2 | [KPI] | [target value] | [measurement method] |',
        '',
        '---',
        '',
        '## 9. MVP Roadmap',
        '',
        '### Now (Sprint 1-3): Core MVP',
        '> Must-have features to validate the product.',
        '- [ ] STORY-NNN: ...',
        '',
        '### Next (Sprint 4-8): Differentiation',
        '> Features that create competitive advantage.',
        '- [ ] STORY-NNN: ...',
        '',
        '### Later (Sprint 9+): Scale',
        '> Platform expansion, optimization, advanced features.',
        '- [ ] STORY-NNN: ...',
        '',
        '---',
        '',
        '## 10. Story Dependency Graph',
        '',
        '```mermaid',
        'graph LR',
        '    STORY-NNN --> STORY-NNN',
        '```',
    ])
    p.write_text(c, encoding='utf-8')
    return f'✅ PRD Created: {p}'


# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p_test = sub.add_parser('create_test_file'); p_test.add_argument('file_path')
    p_e2e = sub.add_parser('create_e2e_test'); p_e2e.add_argument('story_id'); p_e2e.add_argument('scenario_name')
    p_git = sub.add_parser('git_start'); p_git.add_argument('story_id')
    p_spec = sub.add_parser('create_spec'); p_spec.add_argument('story_id'); p_spec.add_argument('title')
    p_prd = sub.add_parser('create_prd'); p_prd.add_argument('product_name')
    p_skill = sub.add_parser('create_skill'); p_skill.add_argument('skill_name'); p_skill.add_argument('description')

    a = parser.parse_args()
    if a.cmd == 'create_test_file': print(create_test_file(a.file_path))
    elif a.cmd == 'create_e2e_test': print(create_e2e(a.story_id, a.scenario_name))
    elif a.cmd == 'git_start': print(git_start(a.story_id))
    elif a.cmd == 'create_spec': print(create_spec(a.story_id, a.title))
    elif a.cmd == 'create_prd': print(create_prd(a.product_name))
    elif a.cmd == 'create_skill': print(create_skill(a.skill_name, a.description))
