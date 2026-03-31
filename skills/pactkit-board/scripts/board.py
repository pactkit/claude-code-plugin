import abc, re, os, sys, json, datetime, argparse, subprocess, shutil, ast
from collections import deque
from dataclasses import dataclass
from pathlib import Path

def nl(): return chr(10)

# Shared pattern for all recognized work item prefixes
ITEM_ID_RE = r"(?:STORY|HOTFIX|BUG)(?:-[a-z]+)?-\d+"

# Flexible story title pattern: matches ### or #### (tolerant) with [ID] or ID: or ID formats
# Group 1: story ID, Group 2: title text
# BUG-027: Support both ### and #### for backward compatibility
_TITLE_RE = rf"^#{{3,4}} \[?({ITEM_ID_RE})\]?:?\s*(.*)"

# Section markers
# STORY-slim-007: canonical values defined in src/pactkit/schemas.py BOARD_SECTION_*.
# This standalone script cannot import pactkit, so values are inlined here.
# When updating, also update src/pactkit/schemas.py.
_BACKLOG = "## 📋 Backlog"
_IN_PROGRESS = "## 🔄 In Progress"
_DONE = "## ✅ Done"


# --- BOARD ---
def add_story(sid, title, tasks):
    p = Path.cwd() / "docs/product/sprint_board.md"
    if not p.exists():
        return "❌ No Board"
    content = p.read_text(encoding="utf-8")
    # R6: Duplicate guard — check if story already exists on board
    existing_blocks = _parse_story_blocks(content)
    for block_sid, *_ in existing_blocks:
        if block_sid == sid:
            return f"❌ Story {sid} already on board"
    t_md = nl().join([f"- [ ] {t.strip()}" for t in tasks.split("|") if t.strip()])
    entry = f"{nl()}### [{sid}] {title}{nl()}> Spec: docs/specs/{sid}.md{nl()}{nl()}{t_md}{nl()}"
    # Insert before In Progress section
    idx = content.find(_IN_PROGRESS)
    if idx == -1:
        # Fallback: append (shouldn't happen with valid board)
        content += entry
    else:
        content = content[:idx] + entry + nl() + content[idx:]
    tmp = p.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, p)
    return f"✅ Story {sid} added"


def _parse_story_blocks(content):
    """Extract all ### [ID] or ### ID: blocks with their full text and positions.

    Returns list of (sid, block_text, start_pos, end_pos) tuples.
    """
    blocks = []
    story_pat = _TITLE_RE
    section_pat = r"^## "
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
        # R4 (STORY-slim-052): Trim trailing whitespace and adjust end to match,
        # so that len(block_text) == end - start for all callers.
        raw = content[start:end]
        trimmed = raw.rstrip()
        adjusted_end = start + len(trimmed)
        blocks.append((m.group(1), trimmed, start, adjusted_end))
    return blocks


def _classify_story(block_text):
    """Determine section for a story block based on task status."""
    done = len(re.findall(r"- \[x\]", block_text))
    todo = len(re.findall(r"- \[ \]", block_text))
    if done == 0:
        return "backlog"
    elif todo == 0:
        return "done"
    else:
        return "in_progress"


def fix_board():
    p = Path.cwd() / "docs/product/sprint_board.md"
    if not p.exists():
        return "❌ No Board"
    content = p.read_text(encoding="utf-8")
    # Find section boundaries
    bp = content.find(_BACKLOG)
    ip = content.find(_IN_PROGRESS)
    dp = content.find(_DONE)
    if bp == -1 or ip == -1 or dp == -1:
        return "❌ Board missing section headers"
    # Extract all story blocks (with positions)
    blocks = _parse_story_blocks(content)
    if not blocks:
        return "✅ No misplaced stories found."
    # Remove all story blocks from content using position-based removal (R5)
    clean = content
    offset = 0
    for _, block_text, start, end in blocks:
        span = end - start
        adj_start = start - offset
        clean = clean[:adj_start] + clean[adj_start + span:]
        offset += span
    # R2 (STORY-slim-052): Clean up trailing whitespace on otherwise-empty lines
    clean = nl().join(line.rstrip() for line in clean.split(nl()))
    # Clean up excessive blank lines
    clean = re.sub(r"\n{3,}", nl() + nl(), clean)
    # Classify stories into buckets
    backlog_items = []
    in_progress_items = []
    done_items = []
    for _, block_text, _, _ in blocks:
        cat = _classify_story(block_text)
        if cat == "backlog":
            backlog_items.append(block_text)
        elif cat == "in_progress":
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
    result = re.sub(r"\n{3,}", nl() + nl(), result)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(result, encoding="utf-8")
    os.replace(tmp, p)
    moved = len(blocks)
    return f"✅ Board fixed: {moved} stories relocated."


def _write_board(p, content):
    """Atomic write to board file."""
    tmp = p.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, p)


def _mark_done(content, story_match, story_block, old_task):
    """Replace one unchecked task with checked, return new content."""
    new_block = story_block.replace(f"- [ ] {old_task}", f"- [x] {old_task}", 1)
    return content[: story_match.start()] + new_block + content[story_match.end() :]


def update_task(sid, tasks_list):
    task_name = " ".join(tasks_list)
    p = Path.cwd() / "docs/product/sprint_board.md"
    if not p.exists():
        return "❌ No Board"
    content = p.read_text(encoding="utf-8")
    # Locate the story block (BUG-027: support ### and ####)
    story_pat = rf"(#{{3,4}} \[?{re.escape(sid)}\]?:?.*?)(?=\n#{{3,4}} |\Z)"
    story_match = re.search(story_pat, content, re.DOTALL)
    if not story_match:
        # Fallback: check if story exists as a bullet in the Done section
        done_pos = content.find(_DONE)
        if done_pos != -1 and re.search(rf"\*\*{re.escape(sid)}\*\*", content[done_pos:]):
            return f"✅ Already done: {sid} (all tasks complete)"
        return f"❌ Story {sid} not found"
    story_block = story_match.group(1)

    def _update_and_fix(content, matched_task):
        content = _mark_done(content, story_match, story_block, matched_task)
        _write_board(p, content)
        fix_board()  # Explicit call for auto-move (R4: not in _write_board)
        return f"✅ Task {sid} updated: {matched_task}"

    # Strategy 1: Exact match
    task_pat = rf"(- \[ \] {re.escape(task_name)})"
    if re.search(task_pat, story_block):
        return _update_and_fix(content, task_name)

    # Check if already done (exact)
    if re.search(rf"- \[x\] {re.escape(task_name)}", story_block):
        return f"✅ Already done: {task_name}"

    # Strategy 2: Fuzzy fallback — collect all unchecked tasks
    unchecked = re.findall(r"- \[ \] (.+)", story_block)
    if not unchecked:
        return f"✅ All tasks in {sid} already done"

    # 2a: Only one unchecked task — mark it done (most common case)
    if len(unchecked) == 1:
        return _update_and_fix(content, unchecked[0])

    # 2b: Substring match
    matches = [t for t in unchecked
               if task_name.lower() in t.lower() or t.lower() in task_name.lower()]
    if len(matches) == 1:
        return _update_and_fix(content, matches[0])

    # 2c: Numeric index (1-based)
    if task_name.isdigit():
        idx = int(task_name) - 1
        if 0 <= idx < len(unchecked):
            return _update_and_fix(content, unchecked[idx])

    remaining = ", ".join(unchecked)
    return f"❌ Task not found in {sid}: {task_name}. Unchecked: [{remaining}]"


def update_version(version):
    # STORY-072: Multi-path lookup (.claude/ then .opencode/)
    yaml_path = None
    for c in [".claude/pactkit.yaml", ".opencode/pactkit.yaml"]:
        p = Path.cwd() / c
        if p.exists():
            yaml_path = p
            break
    if yaml_path is None:
        return "⚠️ No pactkit.yaml found, skipping version update"
    content = yaml_path.read_text(encoding="utf-8")
    # R8: Only replace the first/top-level version: key, not nested ones
    content = re.sub(r"version:\s*\S+", f"version: {version}", content, count=1)
    # R5 (STORY-slim-052): Atomic write via tmp+rename
    tmp = yaml_path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, yaml_path)
    return f"✅ Version updated to {version}"


def snapshot_graph(version):
    graphs_dir = Path.cwd() / "docs/architecture/graphs"
    snap_dir = Path.cwd() / "docs/architecture/snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for name in ["code_graph.mmd", "class_graph.mmd", "call_graph.mmd"]:
        src = graphs_dir / name
        if src.exists():
            shutil.copy2(src, snap_dir / f"{version}_{name}")
            count += 1
    return f"✅ Snapshot {version}: {count} graphs saved"


# --- MOVE ---
def move_story(sid, target):
    """Move a story to the specified section regardless of checkbox state."""
    valid_targets = {"backlog": _BACKLOG, "in_progress": _IN_PROGRESS, "done": _DONE}
    if target not in valid_targets:
        return f"❌ Invalid target: {target}. Use: backlog, in_progress, done"
    p = Path.cwd() / "docs/product/sprint_board.md"
    if not p.exists():
        return "❌ No Board"
    content = p.read_text(encoding="utf-8")
    blocks = _parse_story_blocks(content)
    # Find the target story (with position)
    story_block = None
    block_start = None
    block_end = None
    for block_sid, block_text, start, end in blocks:
        if block_sid == sid:
            story_block = block_text
            block_start = start
            block_end = end
            break
    if story_block is None:
        return f"❌ Story {sid} not found on board"
    # Remove the story block using its known position (R5)
    content = content[:block_start] + content[block_end:]
    content = re.sub(r"\n{3,}", nl() + nl(), content)
    # Find target section and the next section after it
    target_header = valid_targets[target]
    section_order = [_BACKLOG, _IN_PROGRESS, _DONE]
    target_idx = content.find(target_header)
    if target_idx == -1:
        return f"❌ Section '{target_header}' not found"
    # Find the next section header after target
    next_section_idx = len(content)
    for sec in section_order:
        sec_idx = content.find(sec)
        if sec_idx > target_idx and sec_idx < next_section_idx:
            next_section_idx = sec_idx
    # Insert story block just before the next section (or at end)
    insert_point = next_section_idx
    entry = nl() + story_block + nl() + nl()
    content = content[:insert_point].rstrip() + entry + content[insert_point:]
    content = re.sub(r"\n{3,}", nl() + nl(), content)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, p)
    return f"✅ Moved {sid} to {target}"


# --- LIST ---
def list_stories():
    p = Path.cwd() / "docs/product/sprint_board.md"
    if not p.exists():
        return "❌ No Board"
    content = p.read_text(encoding="utf-8")
    headers = list(re.finditer(_TITLE_RE, content, re.MULTILINE))
    if not headers:
        return "No stories on board."
    lines = []
    for i, m in enumerate(headers):
        sid, title = m.group(1), m.group(2)
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        block = content[start:end]
        done = len(re.findall(r"- \[x\]", block))
        total = done + len(re.findall(r"- \[ \]", block))
        if total == 0:
            status = "BACKLOG"
        elif done == total:
            status = "DONE"
        elif done > 0:
            status = "IN_PROGRESS"
        else:
            status = "BACKLOG"
        lines.append((sid, title, done, total, status))
    lines.sort(key=lambda r: r[0])
    return nl().join(f"{s[0]} | {s[1]} | {s[2]}/{s[3]} | {s[4]}" for s in lines)


# --- ARCHIVE ---
def archive_stories():
    board_path = Path.cwd() / "docs/product/sprint_board.md"
    archive_dir = Path.cwd() / "docs/product/archive"
    if not board_path.exists():
        return "❌ No Board"
    content = board_path.read_text(encoding="utf-8")
    # BUG-027: Support both ### and #### for backward compatibility
    # R7: Use ITEM_ID_RE instead of hardcoded prefix list
    parts = re.split(rf"(?=^#{{3,4}} \[?(?:{ITEM_ID_RE})\]?)", content, flags=re.MULTILINE)
    active_parts = [parts[0]]
    archived_parts = []
    for part in parts[1:]:
        has_done = "- [x]" in part
        has_todo = "- [ ]" in part
        if has_todo or not has_done:
            active_parts.append(part)
        else:
            archived_parts.append(part)
    if not archived_parts:
        return "✅ No completed stories to archive."
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m")
    af = archive_dir / f"archive_{ts}.md"
    with open(af, "a", encoding="utf-8") as f:
        for part in archived_parts:
            f.write(nl() + part.strip() + nl())
    new_content = "".join(active_parts)
    new_content = re.sub(r"\n{3,}", nl() + nl(), new_content)
    # Ensure required section headers survive after archiving stories
    for section in (_BACKLOG, _IN_PROGRESS, _DONE):
        if section not in new_content:
            new_content = new_content.rstrip() + nl() + nl() + section + nl()
    tmp = board_path.with_suffix(".tmp")
    tmp.write_text(new_content, encoding="utf-8")
    os.replace(tmp, board_path)
    return f"✅ Archived {len(archived_parts)} stories to {af}"


# --- CLI ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add_story")
    p_add.add_argument("story_id")
    p_add.add_argument("title")
    p_add.add_argument("tasks")
    p_upd = sub.add_parser("update_task")
    p_upd.add_argument("story_id")
    p_upd.add_argument("task_name", nargs="+")
    p_ver = sub.add_parser("update_version")
    p_ver.add_argument("version")
    p_snap = sub.add_parser("snapshot")
    p_snap.add_argument("version")
    p_move = sub.add_parser("move_story")
    p_move.add_argument("story_id")
    p_move.add_argument("target", choices=["backlog", "in_progress", "done"])
    sub.add_parser("archive")
    sub.add_parser("list_stories")
    sub.add_parser("fix_board")

    a = parser.parse_args()
    if a.cmd == "add_story":
        print(add_story(a.story_id, a.title, a.tasks))
    elif a.cmd == "update_task":
        print(update_task(a.story_id, a.task_name))
    elif a.cmd == "update_version":
        print(update_version(a.version))
    elif a.cmd == "snapshot":
        print(snapshot_graph(a.version))
    elif a.cmd == "archive":
        print(archive_stories())
    elif a.cmd == "list_stories":
        print(list_stories())
    elif a.cmd == "move_story":
        print(move_story(a.story_id, a.target))
    elif a.cmd == "fix_board":
        print(fix_board())
