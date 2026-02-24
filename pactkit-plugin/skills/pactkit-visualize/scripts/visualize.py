import re, os, sys, json, datetime, argparse, subprocess, shutil, ast
from pathlib import Path

def nl(): return chr(10)

# --- ARCH ---
def init_architecture():
    root = Path.cwd() / 'docs/architecture'
    (root/'graphs').mkdir(parents=True, exist_ok=True)
    (root/'governance').mkdir(parents=True, exist_ok=True)
    hld = root / 'graphs/system_design.mmd'
    if not hld.exists(): hld.write_text('graph TD' + nl() + '    User --> System', encoding='utf-8')
    lld = root / 'graphs/code_graph.mmd'
    if not lld.exists(): lld.write_text('classDiagram' + nl() + '    %% Empty', encoding='utf-8')
    return '✅ Init: Structure Complete'

# --- SCAN HELPERS (shared across modes) ---
def _scan_files(root):
    excludes = {'venv', '_venv', '.venv', '.env', 'env', '__pycache__', '.git', '.claude', 'tests', 'docs', 'node_modules', 'site-packages', 'dist', 'build'}
    all_files = []
    module_index = {}
    file_to_node = {}

    for p in root.rglob('*.py'):
        if any(part in excludes for part in p.parts): continue
        all_files.append(p)
        node_id = str(p.relative_to(root)).replace(os.sep, '_').replace('.', '_').replace('-', '_')
        file_to_node[p] = node_id
        try:
            rel_path = p.relative_to(root)
            module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')
            module_index[module_name] = p
            if len(rel_path.parts) > 1 and rel_path.parts[0] == 'src':
                short_name = '.'.join(rel_path.parts[1:]).replace('.py', '')
                module_index[short_name] = p
            if p.name == '__init__.py':
                pkg_name = str(rel_path.parent).replace(os.sep, '.')
                module_index[pkg_name] = p
                if len(rel_path.parts) > 2 and rel_path.parts[0] == 'src':
                     short_pkg = '.'.join(rel_path.parts[1:-1])
                     module_index[short_pkg] = p
        except: pass
    return all_files, module_index, file_to_node

# --- MODE: FILE (original, v19.7) ---
def _build_file_graph(root, all_files, module_index, file_to_node, focus, depth=0, max_nodes=0):
    nodes = []
    edges = []
    for f in all_files:
        nid = file_to_node[f]
        rel_str = str(f.relative_to(root))
        nodes.append(f'    {nid}["{f.name}"]')
        nodes.append(f'    click {nid} href "{rel_str}"')
    seen_edges = set()
    adjacency = {}  # node -> set of neighbor nodes (for depth limiting)
    for p in all_files:
        consumer_id = file_to_node[p]
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'))
            for n in ast.walk(tree):
                imported_modules = []
                if isinstance(n, ast.Import):
                    for alias in n.names:
                        imported_modules.append(alias.name)
                elif isinstance(n, ast.ImportFrom):
                    if n.module: imported_modules.append(n.module)
                for imported_module in imported_modules:
                    tf = module_index.get(imported_module)
                    if not tf:
                        parts = imported_module.split('.')
                        for i in range(len(parts), 0, -1):
                            sub = '.'.join(parts[:i])
                            if sub in module_index: tf = module_index[sub]; break
                    if tf and tf != p:
                        pid = file_to_node.get(tf)
                        if pid:
                            edge = (consumer_id, pid)
                            if edge not in seen_edges:
                                seen_edges.add(edge)
                                edges.append(edge)
                            adjacency.setdefault(consumer_id, set()).add(pid)
                            adjacency.setdefault(pid, set()).add(consumer_id)
        except: pass

    final_lines = ['graph TD']
    if focus:
        target_ids = set()
        for f, nid in file_to_node.items():
            if focus in str(f.relative_to(root)): target_ids.add(nid)
        if not target_ids:
            return None, f"❌ Focus target '{focus}' not found. (Scanned {len(all_files)} files)"
        relevant_ids = set(target_ids)
        relevant_edges = []
        for src, dst in edges:
            if src in target_ids or dst in target_ids:
                relevant_edges.append(f'    {src} --> {dst}')
                relevant_ids.add(src); relevant_ids.add(dst)
        for line in nodes:
            if any(rid in line for rid in relevant_ids): final_lines.append(line)
        final_lines.extend(relevant_edges)
        dest = root / 'docs/architecture/graphs/focus_graph.mmd'
    else:
        # Apply depth limiting via BFS if depth > 0
        if depth > 0:
            # Find root nodes (nodes with no incoming edges)
            all_node_ids = set(file_to_node.values())
            has_incoming = set()
            for src, dst in edges:
                has_incoming.add(dst)
            root_nodes = all_node_ids - has_incoming
            if not root_nodes:
                root_nodes = all_node_ids  # fallback: use all

            # BFS from root nodes up to depth levels
            allowed = set()
            frontier = set(root_nodes)
            for _ in range(depth + 1):
                allowed |= frontier
                next_frontier = set()
                for nid in frontier:
                    for neighbor in adjacency.get(nid, set()):
                        if neighbor not in allowed:
                            next_frontier.add(neighbor)
                frontier = next_frontier

            # Filter nodes and edges
            for line in nodes:
                if any(nid in line for nid in allowed):
                    final_lines.append(line)
            for src, dst in edges:
                if src in allowed and dst in allowed:
                    final_lines.append(f'    {src} --> {dst}')
        else:
            final_lines.extend(nodes)
            for src, dst in edges: final_lines.append(f'    {src} --> {dst}')

        # Apply max_nodes truncation
        if max_nodes > 0:
            # Count actual node definition lines (contain "[" but not "click")
            node_lines = [line for line in final_lines[1:] if '[' in line and 'click' not in line]
            if len(node_lines) > max_nodes:
                truncated_count = len(node_lines) - max_nodes
                # Keep only the first max_nodes node IDs
                keep_ids = set()
                for line in node_lines[:max_nodes]:
                    nid = line.strip().split('[')[0].strip()
                    keep_ids.add(nid)
                filtered = ['graph TD']
                for line in final_lines[1:]:
                    if '[' in line or 'click' in line:
                        if any(nid in line for nid in keep_ids):
                            filtered.append(line)
                    elif '-->' in line:
                        parts = line.strip().split('-->')
                        src = parts[0].strip()
                        dst = parts[1].strip()
                        if src in keep_ids and dst in keep_ids:
                            filtered.append(line)
                filtered.append(f'    NOTE["... and {truncated_count} more nodes (use --max-nodes to adjust)"]')
                final_lines = filtered

        dest = root / 'docs/architecture/graphs/code_graph.mmd'
    return dest, nl().join(final_lines)

# --- MODE: CLASS (classDiagram) ---
def _build_class_graph(root, all_files, focus):
    classes = []  # (file, class_name, bases, methods)

    for p in all_files:
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'))
            rel = str(p.relative_to(root))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = []
                    for b in node.bases:
                        if isinstance(b, ast.Name): bases.append(b.id)
                        elif isinstance(b, ast.Attribute): bases.append(b.attr)
                    methods = []
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            prefix = '+' if not item.name.startswith('_') else '-'
                            args = [a.arg for a in item.args.args if a.arg != 'self']
                            sig = f"{prefix}{item.name}({', '.join(args)})"
                            methods.append(sig)
                    classes.append((rel, node.name, bases, methods))
        except: pass

    # Filter by focus
    if focus:
        classes = [(f, cn, bases, ms) for f, cn, bases, ms in classes if focus in f]

    lines = ['classDiagram']
    seen_classes = set()
    for rel, cname, bases, methods in classes:
        if cname in seen_classes: continue
        seen_classes.add(cname)
        lines.append(f'    class {cname} {{')
        for m in methods: lines.append(f'        {m}')
        lines.append('    }')
        for b in bases:
            lines.append(f'    {b} <|-- {cname}')

    dest = root / 'docs/architecture/graphs/class_graph.mmd'
    if focus: dest = root / 'docs/architecture/graphs/focus_graph.mmd'
    return dest, nl().join(lines)

# --- MODE: CALL (function-level call graph) ---
def _build_call_graph(root, all_files, focus, entry):
    # Pass 1: Register all functions/methods
    func_registry = {}  # {qualified_name: file}
    # Pass 2: Build call edges
    call_edges = {}  # {caller_qualified: [callee_qualified]}

    for p in all_files:
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'))
            rel = p.stem

            for node in ast.iter_child_nodes(tree):
                # Top-level functions
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qname = node.name
                    func_registry[qname] = rel
                    callees = _extract_calls(node, current_class=None)
                    call_edges[qname] = callees

                # Class methods
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            qname = f'{node.name}.{item.name}'
                            func_registry[qname] = rel
                            callees = _extract_calls(item, current_class=node.name)
                            call_edges[qname] = callees
        except: pass

    # Pass 3: Resolve short names to qualified names where possible
    all_func_names = set(func_registry.keys())

    # Pass 4: If --entry, do BFS for transitive closure
    if entry:
        # Find the entry function (try exact match, then partial)
        start = None
        for fn in all_func_names:
            if fn == entry or fn.endswith(f'.{entry}'): start = fn; break
        if not start:
            for fn in all_func_names:
                if entry in fn: start = fn; break
        if not start:
            return root / 'docs/architecture/graphs/call_graph.mmd', f'graph TD{nl()}    ❌_not_found["{entry} not found"]'

        # BFS
        visited = set()
        queue = [start]
        reachable_edges = []
        while queue:
            current = queue.pop(0)
            if current in visited: continue
            visited.add(current)
            for callee in call_edges.get(current, []):
                # Resolve callee to qualified name
                resolved = _resolve_callee(callee, all_func_names)
                if resolved:
                    reachable_edges.append((current, resolved))
                    if resolved not in visited: queue.append(resolved)
                else:
                    # Keep unresolved as leaf node
                    reachable_edges.append((current, callee))
                    visited.add(callee)

        lines = ['graph TD']
        safe = lambda s: s.replace('.', '_')
        for fn in visited:
            lines.append(f'    {safe(fn)}["{fn}"]')
        for src, dst in reachable_edges:
            lines.append(f'    {safe(src)} --> {safe(dst)}')
    else:
        # Full call graph (optionally filtered by focus)
        lines = ['graph TD']
        safe = lambda s: s.replace('.', '_')
        relevant = set()
        rel_edges = []

        for caller, callees in call_edges.items():
            if focus and focus not in func_registry.get(caller, ''): continue
            for callee in callees:
                resolved = _resolve_callee(callee, all_func_names) or callee
                relevant.add(caller)
                relevant.add(resolved)
                rel_edges.append((caller, resolved))

        # If no focus, include all
        if not focus:
            relevant = set(func_registry.keys())
            for callees in call_edges.values():
                for c in callees:
                    resolved = _resolve_callee(c, all_func_names) or c
                    relevant.add(resolved)

        for fn in sorted(relevant): lines.append(f'    {safe(fn)}["{fn}"]')
        for src, dst in rel_edges: lines.append(f'    {safe(src)} --> {safe(dst)}')
        if not rel_edges:
            for caller, callees in call_edges.items():
                for callee in callees:
                    resolved = _resolve_callee(callee, all_func_names) or callee
                    lines.append(f'    {safe(caller)} --> {safe(resolved)}')

    dest = root / 'docs/architecture/graphs/call_graph.mmd'
    if focus: dest = root / 'docs/architecture/graphs/focus_graph.mmd'
    return dest, nl().join(lines)

def _extract_calls(func_node, current_class=None):
    # Extract function/method calls from a function body.
    callees = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                callees.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # self.method() → ClassName.method
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'self' and current_class:
                        callees.append(f'{current_class}.{node.func.attr}')
                    else:
                        callees.append(f'{node.func.value.id}.{node.func.attr}')
    return callees

def _resolve_callee(callee, all_func_names):
    # Try to resolve a callee string to a known qualified function name.
    if callee in all_func_names: return callee
    # Try matching by suffix
    for fn in all_func_names:
        if fn.endswith(f'.{callee}') or fn == callee: return fn
    return None

# --- MAIN VISUALIZE (v20.0 Multi-Mode) ---
def visualize(target='.', focus=None, mode='file', entry=None, depth=0, max_nodes=0):
    root = Path(target).resolve()
    all_files, module_index, file_to_node = _scan_files(root)

    if mode == 'class':
        dest, content = _build_class_graph(root, all_files, focus)
    elif mode == 'call':
        dest, content = _build_call_graph(root, all_files, focus, entry)
    else:
        dest, content = _build_file_graph(root, all_files, module_index, file_to_node, focus, depth=depth, max_nodes=max_nodes)
        if dest is None: return content  # error message

    if not dest.parent.exists(): dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding='utf-8')
    return f'✅ Graph: {dest}'

def list_rules(): return 'Rules defined in ~/.claude/CLAUDE.md'

# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init_arch')
    sub.add_parser('list_rules')
    p_viz = sub.add_parser('visualize')
    p_viz.add_argument('--focus')
    p_viz.add_argument('--mode', choices=['file', 'class', 'call'], default='file')
    p_viz.add_argument('--entry')
    p_viz.add_argument('--depth', type=int, default=0, help='Limit graph traversal to N levels (0=unlimited)')
    p_viz.add_argument('--max-nodes', type=int, default=0, help='Truncate graph to N nodes (0=unlimited)')

    a = parser.parse_args()
    if a.cmd == 'init_arch': print(init_architecture())
    elif a.cmd == 'visualize': print(visualize('.', a.focus, a.mode, a.entry, depth=a.depth, max_nodes=a.max_nodes))
    elif a.cmd == 'list_rules': print(list_rules())
