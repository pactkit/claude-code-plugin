import re, os, sys, json, datetime, argparse, subprocess, shutil, ast
from pathlib import Path

def nl(): return chr(10)

# Shared pattern for all recognized work item prefixes
ITEM_ID_RE = r'(?:STORY|HOTFIX|BUG)-\d+'

# Section markers
_BACKLOG = '## 📋 Backlog'
_IN_PROGRESS = '## 🔄 In Progress'
_DONE = '## ✅ Done'

# --- BOARD ---
def add_story(sid, title, tasks):
    p = Path.cwd() / 'docs/product/sprint_board.md'
    if not p.exists(): return '❌ No Board'
    content = p.read_text(encoding='utf-8')
    t_md = nl().join([f'- [ ] {t.strip()}' for t in tasks.split('|') if t.strip()])
    entry = f'{nl()}### [{sid}] {title}{nl()}> Spec: docs/specs/{sid}.md{nl()}{nl()}{t_md}{nl()}'
    # Insert before In Progress section
    idx = content.find(_IN_PROGRESS)
    if idx == -1:
        # Fallback: append (shouldn't happen with valid board)
        content += entry
    else:
        content = content[:idx] + entry + nl() + content[idx:]
    tmp = p.with_suffix('.tmp')
    tmp.write_text(content, encoding='utf-8')
    os.replace(tmp, p)
    return f'✅ Story {sid} added'


def _parse_story_blocks(content):
    """Extract all ### [ID] blocks with their full text."""
    blocks = []
    story_pat = rf'^### \[({ITEM_ID_RE})\].*'
    section_pat = r'^## '
    matches = list(re.finditer(story_pat, content, re.MULTILINE))
    # Find all section header positions to use as boundaries
    section_starts = [m.start() for m in re.finditer(section_pat, content, re.MULTILINE)]
    for i, m in enumerate(matches):
        start = m.start()
        # End at the next story header, next section header, or EOF
        next_story = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        next_section = len(content)
        for sp in section_starts:
            if sp > start:
                next_section = sp
                break
        end = min(next_story, next_section)
        blocks.append((m.group(1), content[start:end].rstrip()))
    return blocks


def _classify_story(block_text):
    """Determine section for a story block based on task status."""
    done = len(re.findall(r'- \[x\]', block_text))
    todo = len(re.findall(r'- \[ \]', block_text))
    if done == 0:
        return 'backlog'
    elif todo == 0:
        return 'done'
    else:
        return 'in_progress'


def fix_board():
    p = Path.cwd() / 'docs/product/sprint_board.md'
    if not p.exists(): return '❌ No Board'
    content = p.read_text(encoding='utf-8')
    # Find section boundaries
    bp = content.find(_BACKLOG)
    ip = content.find(_IN_PROGRESS)
    dp = content.find(_DONE)
    if bp == -1 or ip == -1 or dp == -1:
        return '❌ Board missing section headers'
    # Extract all story blocks
    blocks = _parse_story_blocks(content)
    if not blocks:
        return '✅ No misplaced stories found.'
    # Remove all story blocks from content
    clean = content
    for sid, block_text in reversed(blocks):
        idx = clean.find(block_text)
        if idx != -1:
            clean = clean[:idx] + clean[idx + len(block_text):]
    # Clean up excessive blank lines
    clean = re.sub(r'\n{3,}', nl() + nl(), clean)
    # Classify stories into buckets
    backlog_items = []
    in_progress_items = []
    done_items = []
    for sid, block_text in blocks:
        cat = _classify_story(block_text)
        if cat == 'backlog':
            backlog_items.append(block_text)
        elif cat == 'in_progress':
            in_progress_items.append(block_text)
        else:
            done_items.append(block_text)
    # Rebuild: insert stories into correct sections
    # Find section positions in cleaned content
    bp = clean.find(_BACKLOG)
    ip = clean.find(_IN_PROGRESS)
    dp = clean.find(_DONE)
    result = clean[:ip]
    if backlog_items:
        # Ensure proper spacing before In Progress
        result = result.rstrip() + nl() + nl()
        result += (nl() + nl()).join(backlog_items) + nl() + nl()
    result += clean[ip:dp]
    if in_progress_items:
        result = result.rstrip() + nl() + nl()
        result += (nl() + nl()).join(in_progress_items) + nl() + nl()
    result += clean[dp:]
    if done_items:
        result = result.rstrip() + nl() + nl()
        result += (nl() + nl()).join(done_items) + nl()
    # Final cleanup
    result = re.sub(r'\n{3,}', nl() + nl(), result)
    tmp = p.with_suffix('.tmp')
    tmp.write_text(result, encoding='utf-8')
    os.replace(tmp, p)
    moved = len(blocks)
    return f'✅ Board fixed: {moved} stories relocated.'

def update_task(sid, tasks_list):
    task_name = ' '.join(tasks_list)
    p = Path.cwd() / 'docs/product/sprint_board.md'
    if not p.exists():
        return '❌ No Board'
    content = p.read_text(encoding='utf-8')
    # Locate the story block
    story_pat = rf'(### \[{re.escape(sid)}\].*?)(?=\n### |\Z)'
    story_match = re.search(story_pat, content, re.DOTALL)
    if not story_match:
        return f'❌ Story {sid} not found'
    story_block = story_match.group(1)
    # Check if task exists as unchecked
    task_pat = rf'(- \[ \] {re.escape(task_name)})'
    if re.search(task_pat, story_block):
        new_block = re.sub(task_pat, f'- [x] {task_name}', story_block, count=1)
        new_content = content[:story_match.start()] + new_block + content[story_match.end():]
        tmp = p.with_suffix('.tmp')
        tmp.write_text(new_content, encoding='utf-8')
        os.replace(tmp, p)
        fix_board()
        return f'✅ Task {sid} updated: {task_name}'
    # Check if already done
    if re.search(rf'- \[x\] {re.escape(task_name)}', story_block):
        return f'✅ Already done: {task_name}'
    return f'❌ Task not found in {sid}: {task_name}'

def update_version(version):
    yaml_path = Path.cwd() / '.claude' / 'pactkit.yaml'
    if not yaml_path.exists():
        return '⚠️ No pactkit.yaml found, skipping version update'
    content = yaml_path.read_text(encoding='utf-8')
    content = re.sub(r'version:\s*\S+', f'version: {version}', content)
    yaml_path.write_text(content, encoding='utf-8')
    return f'✅ Version updated to {version}'

def snapshot_graph(version):
    graphs_dir = Path.cwd() / 'docs/architecture/graphs'
    snap_dir = Path.cwd() / 'docs/architecture/snapshots'
    snap_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for name in ['code_graph.mmd', 'class_graph.mmd', 'call_graph.mmd']:
        src = graphs_dir / name
        if src.exists():
            shutil.copy2(src, snap_dir / f'{version}_{name}')
            count += 1
    return f'✅ Snapshot {version}: {count} graphs saved'

# --- LIST ---
def list_stories():
    p = Path.cwd() / 'docs/product/sprint_board.md'
    if not p.exists():
        return '❌ No Board'
    content = p.read_text(encoding='utf-8')
    headers = list(re.finditer(rf'^### \[({ITEM_ID_RE})\] (.+)$', content, re.MULTILINE))
    if not headers:
        return 'No stories on board.'
    lines = []
    for i, m in enumerate(headers):
        sid, title = m.group(1), m.group(2)
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        block = content[start:end]
        done = len(re.findall(r'- \[x\]', block))
        total = done + len(re.findall(r'- \[ \]', block))
        if total == 0:
            status = 'BACKLOG'
        elif done == total:
            status = 'DONE'
        elif done > 0:
            status = 'IN_PROGRESS'
        else:
            status = 'BACKLOG'
        lines.append((sid, title, done, total, status))
    lines.sort(key=lambda r: r[0])
    return nl().join(f'{s[0]} | {s[1]} | {s[2]}/{s[3]} | {s[4]}' for s in lines)


# --- ARCHIVE ---
def archive_stories():
    board_path = Path.cwd() / 'docs/product/sprint_board.md'
    archive_dir = Path.cwd() / 'docs/product/archive'
    if not board_path.exists(): return '❌ No Board'
    content = board_path.read_text(encoding='utf-8')
    parts = re.split(r'(?=^### \[(?:STORY|HOTFIX|BUG)-)', content, flags=re.MULTILINE)
    active_parts = [parts[0]]
    archived_parts = []
    for part in parts[1:]:
        if '- [ ]' in part:
            active_parts.append(part)
        else:
            archived_parts.append(part)
    if not archived_parts: return '✅ No completed stories to archive.'
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m')
    af = archive_dir / f'archive_{ts}.md'
    with open(af, 'a', encoding='utf-8') as f:
        for part in archived_parts:
            f.write(nl() + part.strip() + nl())
    new_content = ''.join(active_parts)
    new_content = re.sub(r'\n{3,}', nl()+nl(), new_content)
    tmp = board_path.with_suffix('.tmp')
    tmp.write_text(new_content, encoding='utf-8')
    os.replace(tmp, board_path)
    return f'✅ Archived {len(archived_parts)} stories to {af}'

# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p_add = sub.add_parser('add_story'); p_add.add_argument('story_id'); p_add.add_argument('title'); p_add.add_argument('tasks')
    p_upd = sub.add_parser('update_task'); p_upd.add_argument('story_id'); p_upd.add_argument('task_name', nargs='+')
    p_ver = sub.add_parser('update_version'); p_ver.add_argument('version')
    p_snap = sub.add_parser('snapshot'); p_snap.add_argument('version')
    sub.add_parser('archive')
    sub.add_parser('list_stories')
    sub.add_parser('fix_board')

    a = parser.parse_args()
    if a.cmd == 'add_story': print(add_story(a.story_id, a.title, a.tasks))
    elif a.cmd == 'update_task': print(update_task(a.story_id, a.task_name))
    elif a.cmd == 'update_version': print(update_version(a.version))
    elif a.cmd == 'snapshot': print(snapshot_graph(a.version))
    elif a.cmd == 'archive': print(archive_stories())
    elif a.cmd == 'list_stories': print(list_stories())
    elif a.cmd == 'fix_board': print(fix_board())
