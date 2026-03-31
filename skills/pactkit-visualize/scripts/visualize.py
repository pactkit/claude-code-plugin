import abc, re, os, sys, json, datetime, argparse, subprocess, shutil, ast
from collections import deque
from dataclasses import dataclass
from pathlib import Path

def nl(): return chr(10)


def _atomic_mmd_write(dest, content):
    """Write .mmd file atomically via tmp+rename to prevent partial writes."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp')
    try:
        tmp.write_text(content, encoding='utf-8')
        os.replace(tmp, dest)
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def _mermaid_escape(label: str) -> str:
    """Escape double quotes in Mermaid node labels using HTML entity."""
    return label.replace('"', '#quot;')


def _extract_node_id(line: str) -> str | None:
    """Extract node ID from a Mermaid node or click line. Returns None if not a node/click line."""
    stripped = line.strip()
    if stripped.startswith('click '):
        parts = stripped.split()
        return parts[1] if len(parts) >= 2 else None
    if '[' in stripped:
        return stripped.split('[')[0].strip()
    return None


def _best_match(candidates: list, consumer: 'Path') -> 'Path | None':
    """Pick the candidate closest to consumer's directory (same-package preference)."""
    if not candidates:
        return None
    consumer_parent = consumer.parent
    for c in candidates:
        if c.parent == consumer_parent:
            return c
    # Fallback: longest common prefix
    best = candidates[0]
    best_len = 0
    for c in candidates:
        common = len(os.path.commonpath([str(c), str(consumer)]))
        if common > best_len:
            best_len = common
            best = c
    return best

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
SCAN_EXCLUDES = {
    # Version control
    '.git', '.svn', '.hg',
    # IDE / editor
    '.idea', '.vscode',
    # Python
    'venv', '_venv', '.venv', '.env', 'env', '__pycache__',
    'site-packages', '.eggs', '.tox', '.mypy_cache', '.ruff_cache', '.pytest_cache',
    # Node / TypeScript
    'node_modules', '.next', '.nuxt', '.output', '.turbo', '.cache', 'coverage',
    # Go
    'vendor',
    # Java
    'target', '.gradle', '.mvn', 'out',
    # General build output
    'dist', 'build', 'bin',
    # Common non-source dirs
    'tests', 'docs',
    # PactKit-specific
    '.claude', '.opencode', '.codex',
    'skills', 'commands', 'rules', 'agents',  # PactKit marketplace dirs (BUG-006)
    'pactkit-plugin',  # STORY-slim-068: exclude deploy artifact dir
}

MAX_SCAN_FILES = 500   # STORY-060: file count ceiling to prevent hangs on large repos
MAX_WORKFLOW_NODES = 500  # STORY-slim-048: unified graph node ceiling
MAX_FILE_BYTES = 1_048_576  # STORY-slim-055: per-file size ceiling (1 MB) to prevent OOM

# Canonical: src/pactkit/cleaners.py _STACK_MARKERS
_STACK_MARKERS = [
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("setup.cfg", "python"),
    ("package.json", "node"),
    ("go.mod", "go"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
]

# Canonical: src/pactkit/prompts/workflows.py LANG_PROFILES[*].file_ext
_LANG_FILE_EXT = {
    "python": ".py",
    "node": ".ts",
    "go": ".go",
    "java": ".java",
}

# Canonical: src/pactkit/prompts/workflows.py LANG_PROFILES[*].test_map_pattern
_TEST_MAP_PATTERNS = {
    "python": "tests/unit/test_{module}.py",
    "node": "__tests__/{module}.test.ts",
    "go": "{package}/{module}_test.go",
    "java": "src/test/java/{package}/{module}Test.java",
}


def _load_scan_excludes(root):
    """Load scan_excludes from pactkit.yaml if present. Returns list or None.

    Searches all known config dirs for pactkit.yaml.
    R16: Logs visible warning on YAML parse failure instead of silent pass.
    """
    import sys as _sys
    candidates = [
        root / '.claude' / 'pactkit.yaml',
        root / '.opencode' / 'pactkit.yaml',
        root / '.codex' / 'pactkit.yaml',
    ]
    for path in candidates:
        if path.exists():
            try:
                import yaml as _yaml
                data = _yaml.safe_load(path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    viz = data.get('visualize', {})
                    if isinstance(viz, dict) and 'scan_excludes' in viz:
                        excludes = viz['scan_excludes']
                        if isinstance(excludes, list):
                            return excludes
            except ImportError:
                print(f"⚠️ Warning: pyyaml not installed, cannot read {path}", file=_sys.stderr)
            except Exception as e:
                print(f"⚠️ Warning: failed to parse {path}: {e}", file=_sys.stderr)
    return None


def _load_stub_edges(root):
    """Load stub_edges from pactkit.yaml visualize section. Returns list of (src, dst) tuples or empty list.

    STORY-slim-068 R4: Format in YAML: visualize.stub_edges: ["src -> dst"]
    """
    candidates = [
        root / '.claude' / 'pactkit.yaml',
        root / '.opencode' / 'pactkit.yaml',
        root / '.codex' / 'pactkit.yaml',
    ]
    for path in candidates:
        if path.exists():
            try:
                import yaml as _yaml
                data = _yaml.safe_load(path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    viz = data.get('visualize', {})
                    if isinstance(viz, dict) and 'stub_edges' in viz:
                        raw = viz['stub_edges']
                        if isinstance(raw, list):
                            edges = []
                            for entry in raw:
                                if isinstance(entry, str) and ' -> ' in entry:
                                    parts = entry.split(' -> ', 1)
                                    edges.append((parts[0].strip(), parts[1].strip()))
                            return edges
            except Exception:
                pass
    return []


def _detect_stack(root):
    """Detect the stack name for the project at root.

    Priority:
    1. pactkit.yaml 'stack' field (if not 'auto' and known in _LANG_FILE_EXT)
    2. Marker-file detection via _STACK_MARKERS
    3. Default: 'python'
    """
    import sys as _sys
    # 1. Try reading stack from pactkit.yaml
    candidates = [
        root / '.claude' / 'pactkit.yaml',
        root / '.opencode' / 'pactkit.yaml',
        root / '.codex' / 'pactkit.yaml',
    ]
    for path in candidates:
        if path.exists():
            try:
                import yaml as _yaml
                data = _yaml.safe_load(path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    stack = data.get('stack', 'auto')
                    if stack and stack != 'auto' and stack in _LANG_FILE_EXT:
                        return stack
            except ImportError:
                print(f"⚠️ Warning: pyyaml not installed, cannot read {path}", file=_sys.stderr)
            except Exception as e:
                print(f"⚠️ Warning: failed to parse {path}: {e}", file=_sys.stderr)

    # 2. Marker-file detection
    for marker, stack in _STACK_MARKERS:
        if (root / marker).exists():
            return stack

    # 3. Default
    return 'python'


def _detect_file_ext(root):
    """Detect the source file extension for the project at root.

    Thin wrapper around _detect_stack() that returns the file extension.
    """
    return _LANG_FILE_EXT.get(_detect_stack(root), '.py')


def _scan_files(root, scan_excludes=None, file_ext='.py', focus=None):
    import sys as _sys
    excludes = set(scan_excludes) if scan_excludes is not None else SCAN_EXCLUDES
    all_files = []
    module_index = {}
    file_to_node = {}

    # When focus is set, scan only under that subdirectory to avoid truncation
    scan_root = root
    if focus:
        candidate = root / focus
        if candidate.is_dir():
            scan_root = candidate

    for p in scan_root.rglob(f'*{file_ext}'):
        if any(part in excludes for part in p.parts): continue
        if len(all_files) >= MAX_SCAN_FILES:
            print(f"⚠️ Scan truncated at {MAX_SCAN_FILES} files. Use --focus <module> to narrow scope.", file=_sys.stderr)
            break
        all_files.append(p)
        node_id = str(p.relative_to(root)).replace(os.sep, '_').replace('.', '_').replace('-', '_')
        file_to_node[p] = node_id
        try:
            rel_path = p.relative_to(root)
            module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')
            module_index.setdefault(module_name, []).append(p)
            if len(rel_path.parts) > 1 and rel_path.parts[0] == 'src':
                short_name = '.'.join(rel_path.parts[1:]).replace('.py', '')
                module_index.setdefault(short_name, []).append(p)
            if p.name == '__init__.py':
                pkg_name = str(rel_path.parent).replace(os.sep, '.')
                module_index.setdefault(pkg_name, []).append(p)
                if len(rel_path.parts) > 2 and rel_path.parts[0] == 'src':
                     short_pkg = '.'.join(rel_path.parts[1:-1])
                     module_index.setdefault(short_pkg, []).append(p)
        except (SyntaxError, UnicodeDecodeError, ValueError): pass
    return all_files, module_index, file_to_node

# --- LANGUAGE ADAPTER (STORY-slim-030) ---
class LanguageAnalyzer(abc.ABC):
    @abc.abstractmethod
    def extract_imports(self, file_path) -> list:
        """Return list of imported module name strings."""
        ...

    @abc.abstractmethod
    def extract_functions_and_calls(self, file_path) -> tuple:
        """Return (func_registry, call_edges) for one file."""
        ...


class PythonAnalyzer(LanguageAnalyzer):
    def extract_imports(self, file_path):
        """Parse a Python file and return a list of imported module name strings."""
        try:
            if file_path.stat().st_size > MAX_FILE_BYTES:
                import sys as _sys
                print(f"⚠️ Skipping large file: {file_path} ({file_path.stat().st_size} bytes)", file=_sys.stderr)
                return []
            tree = ast.parse(file_path.read_text(encoding='utf-8'))
            imported_modules = []
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    for alias in n.names:
                        imported_modules.append(alias.name)
                elif isinstance(n, ast.ImportFrom):
                    if n.module:
                        imported_modules.append(n.module)
            return imported_modules
        except (SyntaxError, UnicodeDecodeError, ValueError):
            return []

    def extract_functions_and_calls(self, file_path):
        """Parse a Python file and return (func_registry, call_edges) for that file."""
        try:
            if file_path.stat().st_size > MAX_FILE_BYTES:
                import sys as _sys
                print(f"⚠️ Skipping large file: {file_path} ({file_path.stat().st_size} bytes)", file=_sys.stderr)
                return {}, {}
            source_text = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source_text)
            rel = file_path.stem
            func_registry = {}
            call_edges = {}
            # STORY-slim-068 R3: Track class definitions for inheritance edge linking
            class_defs = {}  # {class_name: ast.ClassDef}
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qname = node.name
                    func_registry[qname] = rel
                    call_edges[qname] = _extract_calls(node, current_class=None, source_text=source_text)
                elif isinstance(node, ast.ClassDef):
                    class_defs[node.name] = node
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            qname = f'{node.name}.{item.name}'
                            func_registry[qname] = rel
                            call_edges[qname] = _extract_calls(item, current_class=node.name, source_text=source_text)
            # STORY-slim-068 R3: Add virtual edges for inheritance overrides
            for cls_name, cls_node in class_defs.items():
                sub_methods = {item.name for item in cls_node.body
                               if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
                for base in cls_node.bases:
                    base_name = None
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr
                    if base_name and base_name in class_defs:
                        base_methods = {item.name for item in class_defs[base_name].body
                                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
                        for method in sub_methods & base_methods:
                            base_qname = f'{base_name}.{method}'
                            sub_qname = f'{cls_name}.{method}'
                            if base_qname in call_edges:
                                call_edges[base_qname].append(sub_qname)
                            else:
                                call_edges[base_qname] = [sub_qname]
            return func_registry, call_edges
        except (SyntaxError, UnicodeDecodeError, ValueError):
            return {}, {}


# --- TREE-SITTER ADAPTER (STORY-slim-032) ---
# Guard imports: tree-sitter is a core dependency but guard for standalone script usage
try:
    from tree_sitter import Language as _TSLanguage, Parser as _TSParser, Query as _TSQuery, QueryCursor as _TSQueryCursor
    _HAS_TREE_SITTER = True
except ImportError:
    _HAS_TREE_SITTER = False


class TreeSitterAnalyzer(LanguageAnalyzer):
    """Base class for tree-sitter-based language analyzers.

    Subclasses provide language grammar and queries; this base class handles
    parser init, file reading, error handling, and query execution.
    """
    def __init__(self, language, import_query, func_query, call_query, method_query=None):
        import re as _re
        self._re = _re
        self._lang = _TSLanguage(language)
        self._parser = _TSParser(self._lang)
        self._import_query = _TSQuery(self._lang, import_query)
        self._func_query = _TSQuery(self._lang, func_query)
        self._call_query = _TSQuery(self._lang, call_query)
        self._method_query = _TSQuery(self._lang, method_query) if method_query else None

    def _captures(self, query, node):
        """Run a query against a node, return dict[str, list[Node]]."""
        cursor = _TSQueryCursor(query)
        return cursor.captures(node)

    def _matches(self, query, node):
        """Run a query against a node, return list[tuple[int, dict[str, list[Node]]]]."""
        cursor = _TSQueryCursor(query)
        return cursor.matches(node)

    def extract_imports(self, file_path):
        try:
            source = file_path.read_bytes()
            tree = self._parser.parse(source)
            captures = self._captures(self._import_query, tree.root_node)
            return [n.text.decode().strip('"\'') for n in captures.get('import', [])]
        except Exception:
            return []

    def extract_functions_and_calls(self, file_path):
        try:
            source = file_path.read_bytes()
            tree = self._parser.parse(source)
            return self._extract_funcs_and_calls(tree, file_path.stem)
        except Exception:
            return {}, {}

    def _extract_funcs_and_calls(self, tree, stem):
        """Override in subclasses for language-specific extraction logic."""
        return {}, {}

    def _extract_calls_from_body(self, body_node):
        """Extract call targets from a function/method body node."""
        calls = []
        captures = self._captures(self._call_query, body_node)
        callees = [n.text.decode() for n in captures.get('callee', [])]
        calls.extend(callees)

        objs = [n.text.decode() for n in captures.get('obj', [])]
        methods = [n.text.decode() for n in captures.get('method', [])]
        for obj, method in zip(objs, methods):
            calls.append(f'{obj}.{method}')

        # STORY-slim-069 R1: Parse dispatch hint comments in body
        comment_query = getattr(self, '_comment_query', None)
        if comment_query:
            try:
                comment_captures = self._captures(comment_query, body_node)
                for node in comment_captures.get('comment', []):
                    text = node.text.decode().strip()
                    # Strip comment prefix (// or /* */)
                    if text.startswith('//'):
                        text = text[2:].strip()
                    elif text.startswith('/*') and text.endswith('*/'):
                        text = text[2:-2].strip()
                    if text.startswith('pactkit-trace: dispatches_to '):
                        targets = text[len('pactkit-trace: dispatches_to '):]
                        for t in targets.split(','):
                            t = t.strip()
                            if t:
                                calls.append(t)
            except Exception:
                pass

        return calls


# Go tree-sitter queries
_GO_IMPORT_QUERY = '(import_spec path: (interpreted_string_literal) @import)'

_GO_FUNC_QUERY = '(function_declaration name: (identifier) @name body: (block) @body)'

_GO_METHOD_QUERY = '''(method_declaration
    receiver: (parameter_list (parameter_declaration type: (_) @receiver_type))
    name: (field_identifier) @name
    body: (block) @body)'''

_GO_CALL_QUERY = '''[
  (call_expression function: (identifier) @callee)
  (call_expression function: (selector_expression
    operand: (_) @obj
    field: (field_identifier) @method))
]'''


class GoAnalyzer(TreeSitterAnalyzer):
    """Go language analyzer using tree-sitter-go."""
    def __init__(self):
        import tree_sitter_go as _tsg
        import re as _re
        self._re = _re
        self._lang = _TSLanguage(_tsg.language())
        self._parser = _TSParser(self._lang)
        self._import_query = _TSQuery(self._lang, _GO_IMPORT_QUERY)
        self._func_query = _TSQuery(self._lang, _GO_FUNC_QUERY)
        self._method_query = _TSQuery(self._lang, _GO_METHOD_QUERY)
        self._call_query = _TSQuery(self._lang, _GO_CALL_QUERY)
        self._comment_query = _TSQuery(self._lang, '(comment) @comment')  # STORY-slim-069 R1

    def _extract_funcs_and_calls(self, tree, stem):
        func_registry = {}
        call_edges = {}

        # Extract top-level functions
        for _, match_dict in self._matches(self._func_query, tree.root_node):
            names = match_dict.get('name', [])
            bodies = match_dict.get('body', [])
            if names and bodies:
                qname = names[0].text.decode()
                func_registry[qname] = stem
                call_edges[qname] = self._extract_calls_from_body(bodies[0])

        # Extract method declarations
        for _, match_dict in self._matches(self._method_query, tree.root_node):
            names = match_dict.get('name', [])
            receivers = match_dict.get('receiver_type', [])
            bodies = match_dict.get('body', [])
            if names and bodies:
                receiver_type = ''
                if receivers:
                    raw = receivers[0].text.decode()
                    # Strip pointer (*), spaces, interface {}
                    receiver_type = self._re.sub(r'[*& \[\]]', '', raw).strip()
                func_name = names[0].text.decode()
                qname = f'{receiver_type}.{func_name}' if receiver_type else func_name
                func_registry[qname] = stem
                call_edges[qname] = self._extract_calls_from_body(bodies[0])

        # STORY-slim-069 R2: Detect struct embedding and add inheritance edges
        # Build struct_name → set_of_embedded_type_names
        struct_bases = {}  # {struct_name: [embedded_type_name, ...]}
        for node in tree.root_node.children:
            if node.type == 'type_declaration':
                for child in node.children:
                    if child.type == 'type_spec':
                        name_node = child.child_by_field_name('name')
                        type_node = child.child_by_field_name('type')
                        if name_node and type_node and type_node.type == 'struct_type':
                            struct_name = name_node.text.decode()
                            embedded = []
                            for field_list in type_node.children:
                                if field_list.type == 'field_declaration_list':
                                    for field in field_list.children:
                                        if field.type == 'field_declaration':
                                            has_field_id = any(
                                                c.type == 'field_identifier' for c in field.children
                                            )
                                            if not has_field_id:
                                                for c in field.children:
                                                    if c.type == 'type_identifier':
                                                        embedded.append(c.text.decode())
                                                    elif c.type == 'pointer_type':
                                                        for pc in c.children:
                                                            if pc.type == 'type_identifier':
                                                                embedded.append(pc.text.decode())
                            if embedded:
                                struct_bases[struct_name] = embedded

        # Add virtual edges: Base.method → Sub.method for shared methods
        for sub_name, bases in struct_bases.items():
            sub_methods = {k.split('.', 1)[1] for k in func_registry if k.startswith(f'{sub_name}.')}
            for base_name in bases:
                base_methods = {k.split('.', 1)[1] for k in func_registry if k.startswith(f'{base_name}.')}
                for method in sub_methods & base_methods:
                    base_qname = f'{base_name}.{method}'
                    sub_qname = f'{sub_name}.{method}'
                    if base_qname in call_edges:
                        call_edges[base_qname].append(sub_qname)
                    else:
                        call_edges[base_qname] = [sub_qname]

        return func_registry, call_edges


# Java tree-sitter queries (STORY-slim-033)
_JAVA_IMPORT_QUERY = '(import_declaration (scoped_identifier) @import)'

_JAVA_FUNC_QUERY = '(method_declaration name: (identifier) @name body: (block) @body)'

_JAVA_CONSTRUCTOR_QUERY = '(constructor_declaration name: (identifier) @name body: (constructor_body) @body)'

_JAVA_CALL_QUERY = '''[
  (method_invocation name: (identifier) @callee)
  (method_invocation object: (_) @obj name: (identifier) @method)
]'''


def _find_enclosing_class(node):
    """Walk up the tree to find the enclosing class_declaration name."""
    current = node
    while current:
        if current.type == 'class_declaration':
            name_node = current.child_by_field_name('name')
            if name_node:
                return name_node.text.decode()
        current = current.parent
    return None


class JavaAnalyzer(TreeSitterAnalyzer):
    """Java language analyzer using tree-sitter-java (STORY-slim-033)."""
    def __init__(self):
        import tree_sitter_java as _tsj
        import re as _re
        self._re = _re
        self._lang = _TSLanguage(_tsj.language())
        self._parser = _TSParser(self._lang)
        self._import_query = _TSQuery(self._lang, _JAVA_IMPORT_QUERY)
        self._func_query = _TSQuery(self._lang, _JAVA_FUNC_QUERY)
        self._constructor_query = _TSQuery(self._lang, _JAVA_CONSTRUCTOR_QUERY)
        self._call_query = _TSQuery(self._lang, _JAVA_CALL_QUERY)
        self._method_query = None  # Java uses _func_query + _constructor_query
        self._comment_query = _TSQuery(self._lang, '[(line_comment)(block_comment)] @comment')  # STORY-slim-069 R1

    def _extract_funcs_and_calls(self, tree, stem):
        func_registry = {}
        call_edges = {}

        # Extract instance and static methods
        for _, match_dict in self._matches(self._func_query, tree.root_node):
            names = match_dict.get('name', [])
            bodies = match_dict.get('body', [])
            if names and bodies:
                name_node = names[0]
                func_name = name_node.text.decode()
                class_name = _find_enclosing_class(name_node)
                qname = f'{class_name}.{func_name}' if class_name else func_name
                func_registry[qname] = stem
                call_edges[qname] = self._extract_calls_from_body(bodies[0])

        # Extract constructors (ClassName.ClassName pattern)
        for _, match_dict in self._matches(self._constructor_query, tree.root_node):
            names = match_dict.get('name', [])
            bodies = match_dict.get('body', [])
            if names and bodies:
                name_node = names[0]
                ctor_name = name_node.text.decode()
                qname = f'{ctor_name}.{ctor_name}'
                func_registry[qname] = stem
                call_edges[qname] = self._extract_calls_from_body(bodies[0])

        # STORY-slim-069 R3: Detect extends/implements and add inheritance edges
        class_bases = {}  # {class_name: [base_names]}
        for node in tree.root_node.children:
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if not name_node:
                    continue
                cls_name = name_node.text.decode()
                bases = []
                # superclass (extends)
                superclass = node.child_by_field_name('superclass')
                if superclass:
                    for c in superclass.children:
                        if c.type == 'type_identifier':
                            bases.append(c.text.decode())
                # super_interfaces (implements)
                for child in node.children:
                    if child.type == 'super_interfaces':
                        for c in child.children:
                            if c.type == 'type_list':
                                for ti in c.children:
                                    if ti.type == 'type_identifier':
                                        bases.append(ti.text.decode())
                if bases:
                    class_bases[cls_name] = bases

        for sub_name, bases in class_bases.items():
            sub_methods = {k.split('.', 1)[1] for k in func_registry if k.startswith(f'{sub_name}.')}
            for base_name in bases:
                base_methods = {k.split('.', 1)[1] for k in func_registry if k.startswith(f'{base_name}.')}
                for method in sub_methods & base_methods:
                    base_qname = f'{base_name}.{method}'
                    sub_qname = f'{sub_name}.{method}'
                    if base_qname in call_edges:
                        call_edges[base_qname].append(sub_qname)
                    else:
                        call_edges[base_qname] = [sub_qname]

        return func_registry, call_edges


# TS/JS tree-sitter queries (STORY-slim-034)
_TS_IMPORT_QUERY = '''[
  (import_statement source: (string) @import)
  (export_statement source: (string) @import)
  (call_expression
    function: (identifier) @_func (#eq? @_func "require")
    arguments: (arguments (string) @import))
]'''

_TS_FUNC_QUERY = '''[
  (function_declaration name: (identifier) @name body: (statement_block) @body)
  (method_definition name: (property_identifier) @name body: (statement_block) @body)
  (lexical_declaration
    (variable_declarator
      name: (identifier) @name
      value: [(arrow_function body: (_) @body) (function_expression body: (statement_block) @body)]))
]'''

_TS_CALL_QUERY = '''[
  (call_expression function: (identifier) @callee)
  (call_expression function: (member_expression
    object: (_) @obj
    property: (property_identifier) @method))
]'''


class TSAnalyzer(TreeSitterAnalyzer):
    """TypeScript/JavaScript language analyzer using tree-sitter-typescript (STORY-slim-034)."""
    def __init__(self):
        import tree_sitter_typescript as _tsts
        self._lang = _TSLanguage(_tsts.language_typescript())
        self._parser = _TSParser(self._lang)
        self._import_query = _TSQuery(self._lang, _TS_IMPORT_QUERY)
        self._func_query = _TSQuery(self._lang, _TS_FUNC_QUERY)
        self._call_query = _TSQuery(self._lang, _TS_CALL_QUERY)
        self._method_query = None
        self._comment_query = _TSQuery(self._lang, '(comment) @comment')  # STORY-slim-069 R1

    def _extract_funcs_and_calls(self, tree, stem):
        func_registry = {}
        call_edges = {}

        for _, match_dict in self._matches(self._func_query, tree.root_node):
            names = match_dict.get('name', [])
            bodies = match_dict.get('body', [])
            if names and bodies:
                name_node = names[0]
                func_name = name_node.text.decode()
                class_name = _find_enclosing_class(name_node)
                qname = f'{class_name}.{func_name}' if class_name else func_name
                func_registry[qname] = stem
                call_edges[qname] = self._extract_calls_from_body(bodies[0])

        # STORY-slim-069 R4: Detect class extends and add inheritance edges
        class_bases = {}  # {class_name: [base_names]}
        for node in tree.root_node.children:
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if not name_node:
                    continue
                cls_name = name_node.text.decode()
                bases = []
                for child in node.children:
                    if child.type == 'class_heritage':
                        for hc in child.children:
                            if hc.type == 'extends_clause':
                                for ec in hc.children:
                                    if ec.type in ('type_identifier', 'identifier'):
                                        bases.append(ec.text.decode())
                if bases:
                    class_bases[cls_name] = bases

        for sub_name, bases in class_bases.items():
            sub_methods = {k.split('.', 1)[1] for k in func_registry if k.startswith(f'{sub_name}.')}
            for base_name in bases:
                base_methods = {k.split('.', 1)[1] for k in func_registry if k.startswith(f'{base_name}.')}
                for method in sub_methods & base_methods:
                    base_qname = f'{base_name}.{method}'
                    sub_qname = f'{sub_name}.{method}'
                    if base_qname in call_edges:
                        call_edges[base_qname].append(sub_qname)
                    else:
                        call_edges[base_qname] = [sub_qname]

        return func_registry, call_edges


def _select_analyzer(stack):
    """Return the appropriate LanguageAnalyzer for the given stack.

    Falls back to PythonAnalyzer if tree-sitter is not installed or
    the language-specific grammar package is missing.
    """
    import sys as _sys
    if stack == 'python':
        return PythonAnalyzer()
    if not _HAS_TREE_SITTER:
        print(f"tree-sitter not installed; falling back to PythonAnalyzer for {stack}", file=_sys.stderr)
        return PythonAnalyzer()
    try:
        if stack == 'go':
            return GoAnalyzer()
        if stack == 'java':
            return JavaAnalyzer()
        if stack == 'node':
            return TSAnalyzer()
    except ImportError:
        print(f"tree-sitter-{stack} not installed; falling back to PythonAnalyzer for {stack}", file=_sys.stderr)
    return PythonAnalyzer()


# --- MODE: FILE (v1.3.0) ---
def _build_file_graph(root, all_files, module_index, file_to_node, focus, depth=0, max_nodes=0, analyzer=None):
    if analyzer is None:
        analyzer = PythonAnalyzer()
    nodes = []
    edges = []
    for f in all_files:
        nid = file_to_node[f]
        rel_str = str(f.relative_to(root))
        nodes.append(f'    {nid}["{_mermaid_escape(f.name)}"]')
        nodes.append(f'    click {nid} href "{rel_str}"')
    seen_edges = set()
    adjacency = {}  # node -> set of neighbor nodes (for depth limiting)
    for p in all_files:
        consumer_id = file_to_node[p]
        for imported_module in analyzer.extract_imports(p):
            candidates = module_index.get(imported_module, [])
            if not candidates:
                parts = imported_module.split('.')
                for i in range(len(parts), 0, -1):
                    sub = '.'.join(parts[:i])
                    if sub in module_index:
                        candidates = module_index[sub]
                        break
            tf = _best_match(candidates, p) if len(candidates) > 1 else (candidates[0] if candidates else None)
            if tf and tf != p:
                pid = file_to_node.get(tf)
                if pid:
                    edge = (consumer_id, pid)
                    if edge not in seen_edges:
                        seen_edges.add(edge)
                        edges.append(edge)
                    adjacency.setdefault(consumer_id, set()).add(pid)
                    adjacency.setdefault(pid, set()).add(consumer_id)

    final_lines = ['graph TD']
    if focus:
        target_ids = set()
        for f, nid in file_to_node.items():
            rel = str(f.relative_to(root))
            if rel == focus or rel.endswith('/' + focus) or f.stem == focus:
                target_ids.add(nid)
        if not target_ids:
            return None, f"❌ Focus target '{focus}' not found. (Scanned {len(all_files)} files)"
        relevant_ids = set(target_ids)
        relevant_edges = []
        for src, dst in edges:
            if src in target_ids or dst in target_ids:
                relevant_edges.append(f'    {src} --> {dst}')
                relevant_ids.add(src); relevant_ids.add(dst)
        for line in nodes:
            nid_in_line = _extract_node_id(line)
            if nid_in_line in relevant_ids:
                final_lines.append(line)
        final_lines.extend(relevant_edges)
        dest = root / 'docs/architecture/graphs/focus_file_graph.mmd'
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
                nid_in_line = _extract_node_id(line)
                if nid_in_line in allowed:
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
                        nid_in_line = _extract_node_id(line)
                        if nid_in_line in keep_ids:
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
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
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
        except (SyntaxError, UnicodeDecodeError, ValueError): pass

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
    if focus: dest = root / 'docs/architecture/graphs/focus_class_graph.mmd'
    return dest, nl().join(lines)

# --- MODE: CALL (function-level call graph) ---
def _build_call_graph(root, all_files, focus, entry, analyzer=None):
    if analyzer is None:
        analyzer = PythonAnalyzer()
    func_registry = {}  # {qualified_name: file}
    call_edges = {}  # {caller_qualified: [callee_qualified]}

    for p in all_files:
        fr, ce = analyzer.extract_functions_and_calls(p)
        func_registry.update(fr)
        # STORY-slim-068 R1: extend-merge to avoid last-wins overwrite on same-name functions
        for caller, callees in ce.items():
            if caller in call_edges:
                call_edges[caller].extend(callees)
            else:
                call_edges[caller] = callees

    # STORY-slim-068 R4: Inject stub edges from pactkit.yaml
    for stub_src, stub_dst in _load_stub_edges(root):
        func_registry.setdefault(stub_dst, '_stub')
        if stub_src in call_edges:
            call_edges[stub_src].append(stub_dst)
        else:
            call_edges[stub_src] = [stub_dst]

    # Pass 3: Resolve short names to qualified names where possible
    all_func_names = set(func_registry.keys())
    suffix_index = _build_suffix_index(all_func_names)

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

        # BFS — only follow edges to project-defined functions (BUG-012)
        visited = set()
        queue = deque([start])
        reachable_edges = []
        while queue:
            current = queue.popleft()
            if current in visited: continue
            visited.add(current)
            for callee in call_edges.get(current, []):
                resolved = _resolve_callee(callee, all_func_names, suffix_index)
                if resolved:
                    reachable_edges.append((current, resolved))
                    if resolved not in visited: queue.append(resolved)

        # STORY-slim-067: Nested subgraph rendering with fan-in/fan-out
        content = _render_nested_call_graph(
            visited, reachable_edges, entry=start,
            call_edges=call_edges, func_registry=func_registry,
        )
        dest = root / 'docs/architecture/graphs/call_graph.mmd'
        if focus: dest = root / 'docs/architecture/graphs/focus_call_graph.mmd'
        return dest, content
    else:
        # Full call graph — only edges where both endpoints are in func_registry (BUG-012)
        lines = ['graph TD']
        safe = lambda s: s.replace('.', '_')
        relevant = set()
        rel_edges = []

        for caller, callees in call_edges.items():
            if focus and focus not in func_registry.get(caller, ''): continue
            for callee in callees:
                resolved = _resolve_callee(callee, all_func_names, suffix_index)
                if resolved:
                    relevant.add(caller)
                    relevant.add(resolved)
                    rel_edges.append((caller, resolved))

        for fn in sorted(relevant): lines.append(f'    {safe(fn)}["{_mermaid_escape(fn)}"]')
        for src, dst in rel_edges: lines.append(f'    {safe(src)} --> {safe(dst)}')

    dest = root / 'docs/architecture/graphs/call_graph.mmd'
    if focus: dest = root / 'docs/architecture/graphs/focus_call_graph.mmd'
    return dest, nl().join(lines)

_BUILTIN_CALLEES = {
    'isinstance', 'len', 'sorted', 'set', 'dict', 'type', 'print', 'any',
    'str', 'int', 'float', 'bool', 'list', 'tuple', 'range', 'enumerate',
    'zip', 'map', 'filter', 'super', 'hasattr', 'getattr', 'setattr',
    'repr', 'min', 'max', 'abs', 'round', 'open', 'all', 'id', 'hash',
    'callable', 'vars', 'dir', 'hex', 'oct', 'bin', 'ord', 'chr', 'iter',
    'next', 'reversed', 'slice', 'frozenset', 'bytes', 'bytearray',
    'memoryview', 'property', 'staticmethod', 'classmethod', 'input',
    'breakpoint', 'compile', 'eval', 'exec', 'format', 'globals', 'locals',
    'object', 'issubclass', 'pow', 'divmod', 'sum', 'complex', 'delattr',
    'NotImplementedError', 'ValueError', 'TypeError', 'KeyError',
    'AttributeError', 'IndexError', 'RuntimeError', 'FileNotFoundError',
    'OSError', 'IOError', 'StopIteration', 'Exception', 'ImportError',
}

_DISPATCH_HINT_PREFIX = '# pactkit-trace: dispatches_to '

def _extract_calls(func_node, current_class=None, source_text=None):
    # Extract function/method calls from a function body (BUG-012: filtered).
    callees = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name not in _BUILTIN_CALLEES:
                    callees.append(name)
            elif isinstance(node.func, ast.Attribute):
                # self.method() → ClassName.method (retain)
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'self' and current_class:
                        callees.append(f'{current_class}.{node.func.attr}')
                    # Skip non-self local variable method calls (e.g., lines.append)
    # STORY-slim-068 R2: Parse dispatch hint comments from source text
    if source_text:
        try:
            segment = ast.get_source_segment(source_text, func_node)
            if segment:
                for line in segment.splitlines():
                    stripped = line.strip()
                    if stripped.startswith(_DISPATCH_HINT_PREFIX):
                        targets = stripped[len(_DISPATCH_HINT_PREFIX):]
                        for t in targets.split(','):
                            t = t.strip()
                            if t:
                                callees.append(t)
        except Exception:
            pass
    return callees

def _build_suffix_index(all_func_names):
    """Build a suffix index for O(1) callee resolution."""
    suffix_index = {}
    for fn in all_func_names:
        short = fn.rsplit('.', 1)[-1]
        suffix_index.setdefault(short, []).append(fn)
    return suffix_index


def _resolve_callee(callee, all_func_names, suffix_index=None):
    """Resolve a callee string to a known qualified function name. O(1) with suffix_index."""
    if callee in all_func_names:
        return callee
    if suffix_index is not None:
        candidates = suffix_index.get(callee, [])
        return candidates[0] if candidates else None
    # Fallback: linear scan (legacy, only if suffix_index not provided)
    for fn in all_func_names:
        if fn.endswith(f'.{callee}') or fn == callee:
            return fn
    return None


def _render_nested_call_graph(visited, edges, entry, call_edges, func_registry, reverse=False):
    """Render a call graph as depth-based nested Mermaid subgraphs with fan-in/fan-out (STORY-slim-067).

    Args:
        visited: set of function names in the reachable graph
        edges: list of (source, target) tuples
        entry: the entry function name (depth 0)
        call_edges: full call_edges dict from scan (for fan-out calculation)
        func_registry: full func_registry dict from scan
        reverse: if True, edges point toward entry (caller→callee)
    """
    safe = lambda s: s.replace('.', '_')

    # Build adjacency for BFS depth calculation
    adj: dict[str, list[str]] = {}
    for src, dst in edges:
        if reverse:
            adj.setdefault(dst, []).append(src)
        else:
            adj.setdefault(src, []).append(dst)

    # BFS to assign depths
    depth_map: dict[str, int] = {}
    queue = deque([entry])
    depth_map[entry] = 0
    while queue:
        current = queue.popleft()
        for neighbor in adj.get(current, []):
            if neighbor not in depth_map:
                depth_map[neighbor] = depth_map[current] + 1
                queue.append(neighbor)

    # Deduplicate edges and count occurrences (HOTFIX-slim-069)
    from collections import Counter
    edge_counts = Counter(edges)
    unique_edges = list(edge_counts.keys())

    # Compute fan-in and fan-out from unique edges within the reachable set
    fan_in: dict[str, int] = {fn: 0 for fn in visited}
    fan_out: dict[str, int] = {fn: 0 for fn in visited}
    for src, dst in unique_edges:
        if src in visited and dst in visited:
            fan_in[dst] = fan_in.get(dst, 0) + 1
            fan_out[src] = fan_out.get(src, 0) + 1

    # Detect true cycle edges: only when target is an ancestor of source in BFS tree
    # (i.e., target has strictly lower depth AND source is reachable from target).
    # Same-depth calls to shared helpers (e.g., nl()) are NOT cycles. (HOTFIX-slim-069)
    parent_map: dict[str, str | None] = {entry: None}
    bfs_q = deque([entry])
    while bfs_q:
        cur = bfs_q.popleft()
        for nb in adj.get(cur, []):
            if nb not in parent_map:
                parent_map[nb] = cur
                bfs_q.append(nb)

    def _is_ancestor(ancestor, descendant):
        """Check if ancestor is on the BFS-tree path from root to descendant."""
        node = descendant
        while node is not None:
            if node == ancestor:
                return True
            node = parent_map.get(node)
        return False

    cycle_edges = set()
    for src, dst in unique_edges:
        if reverse:
            parent, child = dst, src
        else:
            parent, child = src, dst
        if child in depth_map and parent in depth_map and depth_map[child] < depth_map[parent]:
            if _is_ancestor(child, parent):
                cycle_edges.add((src, dst))

    # Group nodes by depth into nested subgraphs
    max_depth = max(depth_map.values()) if depth_map else 0
    lines = ['graph TD']
    for d in range(max_depth + 1):
        nodes_at_depth = sorted(fn for fn, dep in depth_map.items() if dep == d)
        if not nodes_at_depth:
            continue
        lines.append(f'    subgraph "Depth {d}"')
        for fn in nodes_at_depth:
            fi = fan_in.get(fn, 0)
            fo = fan_out.get(fn, 0)
            label = f'{_mermaid_escape(fn)} [↑{fi} ↓{fo}]'
            lines.append(f'        {safe(fn)}["{label}"]')
        lines.append('    end')

    # Render deduplicated edges with count and cycle detection (HOTFIX-slim-069)
    for (src, dst), count in edge_counts.items():
        s, d = safe(src), safe(dst)
        if (src, dst) in cycle_edges:
            label = f'↻ ×{count}' if count > 1 else '↻'
            lines.append(f'    {s} -.->|{label}| {d}')
        elif count > 1:
            lines.append(f'    {s} -->|×{count}| {d}')
        else:
            lines.append(f'    {s} --> {d}')

    return nl().join(lines)


# --- MODE: REVERSE CALLER BFS (STORY-053) ---
def _scan_call_edges(root, all_files, analyzer=None):
    """Shared helper: build func_registry and call_edges from source. Used by forward and reverse BFS."""
    if analyzer is None:
        analyzer = PythonAnalyzer()
    func_registry = {}  # {qualified_name: stem}
    call_edges = {}  # {caller: [callees]}
    for p in all_files:
        fr, ce = analyzer.extract_functions_and_calls(p)
        func_registry.update(fr)
        # STORY-slim-068 R1: extend-merge to avoid last-wins overwrite
        for caller, callees in ce.items():
            if caller in call_edges:
                call_edges[caller].extend(callees)
            else:
                call_edges[caller] = callees
    return func_registry, call_edges


def _find_entry_func(entry, all_func_names):
    """Find the entry function by exact match, suffix match, or substring match."""
    if not entry: return None
    for fn in all_func_names:
        if fn == entry or fn.endswith(f'.{entry}'): return fn
    for fn in all_func_names:
        if entry in fn: return fn
    return None


def _build_reverse_graph(func_registry, call_edges, entry):
    """BFS backwards through caller graph from entry. Returns (visited_funcs, reverse_edges)."""
    all_func_names = set(func_registry.keys())
    suffix_index = _build_suffix_index(all_func_names)
    # Build reverse map: {callee: [callers]}
    reverse_map = {}
    for caller, callees in call_edges.items():
        for callee in callees:
            resolved = _resolve_callee(callee, all_func_names, suffix_index)
            if resolved:
                reverse_map.setdefault(resolved, []).append(caller)

    start = _find_entry_func(entry, all_func_names)
    if not start: return set(), []

    visited = set()
    queue = deque([start])
    reverse_edges = []
    while queue:
        current = queue.popleft()
        if current in visited: continue
        visited.add(current)
        for caller in reverse_map.get(current, []):
            reverse_edges.append((caller, current))
            if caller not in visited: queue.append(caller)
    return visited, reverse_edges


def _resolve_test_path(root, stem, source_file, stack):
    """Resolve the test file path for a given source file using _TEST_MAP_PATTERNS.

    Returns a Path if the resolved test file exists, or None otherwise.
    """
    pattern = _TEST_MAP_PATTERNS.get(stack, "tests/unit/test_{module}.py")
    module = stem
    package = str(source_file.parent.relative_to(root)).replace(os.sep, '/')
    resolved = pattern.replace("{module}", module).replace("{package}", package)
    test_path = root / resolved
    return test_path if test_path.exists() else None


# --- impact() subcommand (STORY-053, STORY-slim-031) ---
def impact(target='.', entry=None):
    """Find test files impacted by a changed function (reverse BFS + test mapping).
    Returns a space-separated list of test file paths, or empty string if none found.
    """
    if not entry: return ''
    root = Path(target).resolve()
    scan_excludes = _load_scan_excludes(root)
    stack = _detect_stack(root)
    # Multi-extension scanning for Node projects (STORY-slim-034 R5)
    if stack == 'node':
        files_ts, mi_ts, ftn_ts = _scan_files(root, scan_excludes=scan_excludes, file_ext='.ts')
        files_js, mi_js, ftn_js = _scan_files(root, scan_excludes=scan_excludes, file_ext='.js')
        all_files = files_ts + files_js
        module_index = {**mi_ts, **mi_js}
        file_to_node = {**ftn_ts, **ftn_js}
    else:
        file_ext = _detect_file_ext(root)
        all_files, module_index, file_to_node = _scan_files(root, scan_excludes=scan_excludes, file_ext=file_ext)
    analyzer = _select_analyzer(stack)
    func_registry, call_edges = _scan_call_edges(root, all_files, analyzer=analyzer)

    # Build stem → source_file index for {package} resolution
    stem_to_file = {}
    for f in all_files:
        stem_to_file.setdefault(f.stem, f)

    visited, _ = _build_reverse_graph(func_registry, call_edges, entry)
    if not visited: return ''

    test_files = set()
    for func_name in visited:
        stem = func_registry.get(func_name)
        if not stem:
            continue
        source_file = stem_to_file.get(stem)
        if source_file:
            # Try pattern-based resolution first
            test_path = _resolve_test_path(root, stem, source_file, stack)
            if test_path:
                test_files.add(str(test_path.relative_to(root)))
                continue
        # Fallback: hardcoded Python convention
        fallback_path = root / 'tests' / 'unit' / f'test_{stem}.py'
        if fallback_path.exists():
            test_files.add(str(fallback_path.relative_to(root)))
    return ' '.join(sorted(test_files))


# --- MAIN VISUALIZE (v1.3.0 Multi-Mode) ---
def visualize(target='.', focus=None, mode='file', entry=None, depth=0, max_nodes=0, reverse=False, lazy=False, split=False):
    root = Path(target).resolve()

    # --- Unified mode (STORY-slim-049) ---
    if mode == 'unified':
        graph = build_unified_graph(root)
        graphs_dir = root / 'docs' / 'architecture' / 'graphs'
        graphs_dir.mkdir(parents=True, exist_ok=True)
        dest = graphs_dir / 'unified_graph.mmd'
        _atomic_mmd_write(dest, graph.to_mermaid())
        result = f'✅ Graph: {dest}'
        # HOTFIX-slim-050: auto-split only for large graphs; --split forces it
        if split or len(graph.nodes) > MAX_WORKFLOW_NODES:
            focus_dir = graphs_dir / 'focus'
            written = export_focus_graphs(graph, focus_dir)
            result += f' + {len(written)} focus graphs in {focus_dir}'
        return result

    # --- Workflow mode (STORY-slim-036) ---
    if mode == 'workflow':
        dest = root / 'docs' / 'architecture' / 'graphs' / 'workflow_graph.mmd'
        if lazy and dest.exists():
            # Check staleness: compare mmd mtime against command/skill/rule files
            mmd_mtime = dest.stat().st_mtime
            stale = False
            for check_dir_name in ['.claude/commands', '.claude/skills', '.claude/rules',
                                   'commands', 'skills', 'rules']:
                check_dir = root / check_dir_name
                if check_dir.is_dir():
                    for f in check_dir.rglob('*'):
                        if f.is_file() and f.stat().st_mtime > mmd_mtime:
                            stale = True
                            break
                if stale:
                    break
            if not stale:
                return f'Workflow graph up-to-date — skip regeneration: {dest}'
        graph = build_workflow_graph(root=root)
        content = graph.to_mermaid()
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
        _atomic_mmd_write(dest, content)
        return f'✅ Graph: {dest}'

    scan_excludes = _load_scan_excludes(root)
    stack = _detect_stack(root)
    # Multi-extension scanning for Node projects (STORY-slim-034 R5)
    if stack == 'node':
        files_ts, mi_ts, ftn_ts = _scan_files(root, scan_excludes=scan_excludes, file_ext='.ts', focus=focus)
        files_js, mi_js, ftn_js = _scan_files(root, scan_excludes=scan_excludes, file_ext='.js', focus=focus)
        all_files = files_ts + files_js
        module_index = {**mi_ts, **mi_js}
        file_to_node = {**ftn_ts, **ftn_js}
    else:
        file_ext = _detect_file_ext(root)
        all_files, module_index, file_to_node = _scan_files(root, scan_excludes=scan_excludes, file_ext=file_ext, focus=focus)
    analyzer = _select_analyzer(stack)

    if mode == 'class':
        dest, content = _build_class_graph(root, all_files, focus)
    elif mode == 'call':
        if entry and reverse:
            # Reverse BFS: find all callers of the entry function
            func_registry, call_edges = _scan_call_edges(root, all_files, analyzer=analyzer)
            visited, reverse_edges = _build_reverse_graph(func_registry, call_edges, entry)
            # STORY-slim-067: Nested subgraph rendering for reverse graph
            from pactkit.skills.visualize import _find_entry_func
            start = _find_entry_func(entry, set(func_registry.keys()))
            content = _render_nested_call_graph(
                visited, reverse_edges, entry=start or entry,
                call_edges=call_edges, func_registry=func_registry, reverse=True,
            )
            # R14: Write to reverse_call_graph.mmd to avoid overwriting call_graph.mmd
            dest = root / 'docs/architecture/graphs/reverse_call_graph.mmd'
            if focus: dest = root / 'docs/architecture/graphs/focus_reverse_call_graph.mmd'
        else:
            dest, content = _build_call_graph(root, all_files, focus, entry, analyzer=analyzer)
    else:
        dest, content = _build_file_graph(root, all_files, module_index, file_to_node, focus, depth=depth, max_nodes=max_nodes, analyzer=analyzer)
        if dest is None: return content  # error message

    if not dest.parent.exists(): dest.parent.mkdir(parents=True, exist_ok=True)
    _atomic_mmd_write(dest, content)
    return f'✅ Graph: {dest}'

def list_rules(): return 'Rules defined in ~/.claude/CLAUDE.md'


# --- WORKFLOW GRAPH (STORY-slim-035) ---


@dataclass
class WorkflowNode:
    id: str
    kind: str   # 'command', 'agent', 'skill', 'file'
    label: str


@dataclass
class WorkflowEdge:
    source: str
    target: str
    relation: str  # 'invokes', 'depends_on', 'reads', 'writes', 'contains'



# STORY-slim-048: Map node kind to display dimension for layered to_mermaid()
_KIND_TO_DIMENSION: dict[str, str] = {
    'function': 'Code Dimension',
    'class': 'Code Dimension',
    'command': 'PDCA Topology',
    'agent': 'PDCA Topology',
    'skill': 'PDCA Topology',
    'file': 'PDCA Topology',
    'service': 'Service Topology',
    'api': 'Service Topology',
    'topic': 'Service Topology',
    'page': 'Frontend Topology',
    'component': 'Frontend Topology',
    'hook': 'Frontend Topology',
    'store': 'Frontend Topology',
    'api_call': 'API Topology',
    'agent_def': 'Agent Topology',
}


class WorkflowGraph:
    def __init__(self):
        self.nodes: dict[str, WorkflowNode] = {}
        self.edges: list[WorkflowEdge] = []
        self._edge_keys: set[tuple] = set()  # R18 (STORY-slim-052): init in __init__, not lazily
        self.layered: bool = False  # STORY-slim-048: set True by build_unified_graph

    def add_node(self, node: WorkflowNode):
        if node.id not in self.nodes:
            self.nodes[node.id] = node

    def add_edge(self, edge: WorkflowEdge):
        key = (edge.source, edge.target, edge.relation)
        if key not in self._edge_keys:
            self._edge_keys.add(key)
            self.edges.append(edge)

    @staticmethod
    def _sanitize_id(raw: str) -> str:
        """Sanitize a string for use as a Mermaid node ID."""
        return re.sub(r'[^a-zA-Z0-9_]', '_', raw)

    def to_mermaid(self, max_render_nodes: int = 0) -> str:
        lines = ['graph TD']
        if self.layered:
            # STORY-slim-048 R3: Group by dimension for unified/layered graphs
            _dim_order = ['Code Dimension', 'PDCA Topology', 'Service Topology', 'Frontend Topology']
            dimension_nodes: dict[str, list[WorkflowNode]] = {}
            for n in self.nodes.values():
                dim = _KIND_TO_DIMENSION.get(n.kind, n.kind.title() + ' Topology')
                dimension_nodes.setdefault(dim, []).append(n)
            all_dims = sorted(dimension_nodes.keys())
            dim_order = [d for d in _dim_order if d in dimension_nodes] + [
                d for d in all_dims if d not in _dim_order
            ]
            for dim in dim_order:
                nodes = dimension_nodes.get(dim, [])
                if not nodes:
                    continue
                lines.append(f'    subgraph "{dim}"')
                for n in sorted(nodes, key=lambda x: x.id):
                    sid = self._sanitize_id(n.id)
                    lines.append(f'        {sid}["{_mermaid_escape(n.label)}"]')
                lines.append('    end')
        else:
            # STORY-slim-041 R6: Dynamic kind discovery — known PDCA kinds first, then any new kinds
            _known_order = ['command', 'agent', 'skill', 'file']
            _known_labels = {'command': 'Commands', 'agent': 'Agents', 'skill': 'Skills', 'file': 'Files'}
            all_kinds = sorted({n.kind for n in self.nodes.values()})
            kind_order = [k for k in _known_order if k in all_kinds] + [k for k in all_kinds if k not in _known_order]
            kind_labels = {**_known_labels, **{k: k.title() + 's' for k in all_kinds if k not in _known_labels}}
            for kind in kind_order:
                nodes_of_kind = [n for n in self.nodes.values() if n.kind == kind]
                if not nodes_of_kind:
                    continue
                lines.append(f'    subgraph {kind_labels[kind]}')
                for n in sorted(nodes_of_kind, key=lambda x: x.id):
                    sid = self._sanitize_id(n.id)
                    lines.append(f'        {sid}["{_mermaid_escape(n.label)}"]')
                lines.append('    end')
        # STORY-slim-049 R3: max_render_nodes truncation for human-readable output
        if max_render_nodes > 0:
            node_lines = [ln for ln in lines[1:] if '[' in ln and 'NOTE' not in ln]
            if len(node_lines) > max_render_nodes:
                truncated_count = len(node_lines) - max_render_nodes
                keep_ids = set()
                for ln in node_lines[:max_render_nodes]:
                    nid = ln.strip().split('[')[0].strip()
                    keep_ids.add(nid)
                filtered = ['graph TD']
                for ln in lines[1:]:
                    if '[' in ln:
                        line_id = ln.strip().split('[')[0].strip()
                        if line_id in keep_ids:
                            filtered.append(ln)
                    elif 'subgraph' in ln or 'end' == ln.strip():
                        filtered.append(ln)
                filtered.append(f'    NOTE["... and {truncated_count} more nodes"]')
                lines = filtered

        for e in self.edges:
            src = self._sanitize_id(e.source)
            dst = self._sanitize_id(e.target)
            arrow = '-.->' if e.relation == 'sequence' else '-->'
            if max_render_nodes > 0 and len(lines) > 1:
                rendered_ids = {ln.strip().split('[')[0].strip() for ln in lines if '[' in ln and 'NOTE' not in ln}
                if src not in rendered_ids or dst not in rendered_ids:
                    continue
            lines.append(f'    {src} {arrow}|{e.relation}| {dst}')
        return nl().join(lines)

    def forward_reach(self, entry_id: str) -> set[str]:
        """Forward BFS from entry_id — follow edges forward (source→target)."""
        forward_map: dict[str, list[str]] = {}
        for e in self.edges:
            forward_map.setdefault(e.source, []).append(e.target)
        visited: set[str] = set()
        queue = deque([entry_id])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for dst in forward_map.get(current, []):
                if dst not in visited:
                    queue.append(dst)
        return visited

    def reverse_reach(self, entry_id: str) -> set[str]:
        """Reverse BFS from entry_id — follow edges backward (target→source)."""
        reverse_map: dict[str, list[str]] = {}
        for e in self.edges:
            reverse_map.setdefault(e.target, []).append(e.source)
        visited: set[str] = set()
        queue = deque([entry_id])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for src in reverse_map.get(current, []):
                if src not in visited:
                    queue.append(src)
        return visited


class TopologyParser(abc.ABC):
    """Abstract base class for topology-specific workflow parsers (STORY-slim-040 R1).

    Subclasses declare `markers` and implement `parse()`.
    The default `detect()` checks if any marker file/dir exists under root,
    then checks immediate subdirectories for monorepo layouts (e.g., web/, frontend/).
    """
    markers: list[str] = []

    def detect(self, root) -> bool:
        root = Path(root)
        for marker in self.markers:
            if (root / marker).exists():
                return True
        # Monorepo: check immediate subdirectories (e.g., web/, frontend/, client/)
        try:
            subdirs = [d for d in root.iterdir()
                       if d.is_dir() and not d.name.startswith('.') and d.name != 'node_modules']
        except OSError:
            return False
        for subdir in subdirs:
            for marker in self.markers:
                if (subdir / marker).exists():
                    return True
        return False

    @abc.abstractmethod
    def parse(self, root) -> WorkflowGraph:
        ...


# STORY-slim-040 R2: Topology marker lists for auto-detection
_TOPOLOGY_MARKERS: dict[str, list[str]] = {
    'pdca': ['.claude/commands/', '.opencode/commands/', '.codex/commands/', 'commands/', '.claude/pactkit.yaml', '.opencode/pactkit.yaml', '.codex/pactkit.yaml', 'pactkit.yaml'],
    'service': ['docker-compose.yml', 'docker-compose.yaml', 'kubernetes/', 'k8s/', 'openapi.yaml', 'swagger.json'],
    'frontend': ['next.config.js', 'next.config.ts', 'nuxt.config.ts', 'vite.config.ts', 'app/layout.tsx', 'pages/_app.tsx', 'src/router/', 'src/store/'],
}


def detect_topology(root) -> list[str]:
    """Scan project root using registered parser detect() methods (STORY-slim-040 R3).

    Delegates to _TOPOLOGY_PARSERS registry so each parser uses its own canonical markers.
    Falls back to _TOPOLOGY_MARKERS for any topology not yet registered.
    """
    root = Path(root)
    matched = []
    checked = set()
    # First pass: use registered parsers (most accurate — uses each parser's own markers)
    for name, parser in _TOPOLOGY_PARSERS.items():
        if parser.detect(root):
            matched.append(name)
        checked.add(name)
    # Second pass: fall back to _TOPOLOGY_MARKERS for unregistered topologies
    try:
        subdirs = [d for d in root.iterdir()
                   if d.is_dir() and not d.name.startswith('.') and d.name != 'node_modules']
    except OSError:
        subdirs = []
    for name, markers in _TOPOLOGY_MARKERS.items():
        if name in checked:
            continue
        found = False
        for marker in markers:
            if (root / marker).exists():
                found = True
                break
            # Monorepo: check subdirectories
            for subdir in subdirs:
                if (subdir / marker).exists():
                    found = True
                    break
            if found:
                break
        if found:
            matched.append(name)
    return matched


# STORY-slim-040 R4: Registry — populated by subclass stories (041, 042, 045)
_TOPOLOGY_PARSERS: dict[str, TopologyParser] = {}


class PdcaParser(TopologyParser):
    """PDCA topology parser — wraps existing command/routing/skill parsers (STORY-slim-041 R1).

    Declared kind_order and kind_labels for PDCA topology.
    """
    markers = ['.claude/commands/', '.opencode/commands/', '.codex/commands/', 'commands/', '.claude/pactkit.yaml', '.opencode/pactkit.yaml', '.codex/pactkit.yaml']
    kind_order = ['command', 'agent', 'skill', 'file']
    kind_labels = {'command': 'Commands', 'agent': 'Agents', 'skill': 'Skills', 'file': 'Files'}

    def detect(self, root) -> bool:
        root = Path(root)
        for marker in self.markers:
            if (root / marker).exists():
                return True
        return False

    def parse(self, root, commands_dir=None, rules_dir=None, skills_dir=None) -> WorkflowGraph:
        root = Path(root)
        # Directory discovery (moved from build_workflow_graph per R3)
        if commands_dir is None:
            for candidate in [root / '.claude' / 'commands', root / 'commands']:
                if candidate.is_dir():
                    commands_dir = candidate
                    break
            if commands_dir is None:
                home_cmd = Path.home() / '.claude' / 'commands'
                if home_cmd.is_dir():
                    commands_dir = home_cmd
        if rules_dir is None:
            for candidate in [root / '.claude' / 'rules', root / 'rules']:
                if candidate.is_dir():
                    rules_dir = candidate
                    break
            if rules_dir is None:
                home_rules = Path.home() / '.claude' / 'rules'
                if home_rules.is_dir():
                    rules_dir = home_rules
        if skills_dir is None:
            for candidate in [root / '.claude' / 'skills', root / 'skills']:
                if candidate.is_dir():
                    skills_dir = candidate
                    break
            if skills_dir is None:
                home_skills = Path.home() / '.claude' / 'skills'
                if home_skills.is_dir():
                    skills_dir = home_skills

        graph = WorkflowGraph()
        if commands_dir:
            _parse_commands(commands_dir, graph)
        if rules_dir:
            _parse_routing_table(rules_dir, graph)
        if skills_dir:
            _scan_skill_files(skills_dir, graph)
        if commands_dir:
            _parse_pdca_sequence(commands_dir, graph)
        return graph


# STORY-slim-041 R2: Register PdcaParser
_TOPOLOGY_PARSERS['pdca'] = PdcaParser()


def _parse_docker_compose(root, graph: WorkflowGraph):
    """Parse docker-compose.yml/yaml for service nodes and depends_on/links edges (STORY-slim-042 R2)."""
    try:
        import yaml
    except ImportError:
        return
    for name in ('docker-compose.yml', 'docker-compose.yaml'):
        dc_path = Path(root) / name
        if dc_path.exists():
            try:
                data = yaml.safe_load(dc_path.read_text(encoding='utf-8'))
            except Exception:
                return
            if not isinstance(data, dict):
                return
            services = data.get('services') or {}
            for svc_name, svc_conf in services.items():
                graph.add_node(WorkflowNode(id=svc_name, kind='service', label=svc_name))
                if not isinstance(svc_conf, dict):
                    continue
                # depends_on — list or dict form
                deps = svc_conf.get('depends_on', [])
                if isinstance(deps, dict):
                    deps = list(deps.keys())
                for dep in deps:
                    graph.add_node(WorkflowNode(id=dep, kind='service', label=dep))
                    graph.add_edge(WorkflowEdge(source=svc_name, target=dep, relation='depends_on'))
                # links
                for link in svc_conf.get('links', []):
                    link_name = link.split(':')[0]
                    graph.add_node(WorkflowNode(id=link_name, kind='service', label=link_name))
                    graph.add_edge(WorkflowEdge(source=svc_name, target=link_name, relation='depends_on'))
            return  # only parse first found


def _parse_openapi(root, graph: WorkflowGraph):
    """Parse openapi.yaml or swagger.json for API path nodes (STORY-slim-042 R3)."""
    root = Path(root)
    data = None
    for name in ('openapi.yaml', 'openapi.yml'):
        p = root / name
        if p.exists():
            try:
                import yaml
                data = yaml.safe_load(p.read_text(encoding='utf-8'))
            except Exception:
                pass
            break
    if data is None:
        swagger_path = root / 'swagger.json'
        if swagger_path.exists():
            try:
                import json as _json
                data = _json.loads(swagger_path.read_text(encoding='utf-8'))
            except Exception:
                pass
    if not isinstance(data, dict):
        return
    # Extract service name from info.title
    info = data.get('info', {})
    svc_title = info.get('title', 'UnknownService')
    svc_id = re.sub(r'[^a-zA-Z0-9]', '-', svc_title).strip('-').lower()
    graph.add_node(WorkflowNode(id=svc_id, kind='service', label=svc_title))
    # Extract paths
    for path_str, methods in (data.get('paths') or {}).items():
        if not isinstance(methods, dict):
            continue
        for method in methods:
            if method.lower() in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options'):
                api_label = f'{method.upper()} {path_str}'
                api_id = re.sub(r'[^a-zA-Z0-9]', '_', api_label).strip('_').lower()
                graph.add_node(WorkflowNode(id=api_id, kind='api', label=api_label))
                graph.add_edge(WorkflowEdge(source=svc_id, target=api_id, relation='calls_api'))


def _parse_proto_files(root, graph: WorkflowGraph):
    """Scan *.proto files for service/rpc declarations (STORY-slim-042 R4)."""
    root = Path(root)
    svc_pattern = re.compile(r'service\s+(\w+)\s*\{')
    rpc_pattern = re.compile(r'rpc\s+(\w+)\s*\(')
    for proto in sorted(root.glob('**/*.proto')):
        content = proto.read_text(encoding='utf-8')
        current_svc = None
        for line in content.split('\n'):
            svc_m = svc_pattern.search(line)
            if svc_m:
                current_svc = svc_m.group(1)
                graph.add_node(WorkflowNode(id=current_svc, kind='service', label=current_svc))
            rpc_m = rpc_pattern.search(line)
            if rpc_m and current_svc:
                rpc_name = rpc_m.group(1)
                rpc_id = f'{current_svc}/{rpc_name}'
                graph.add_node(WorkflowNode(id=rpc_id, kind='api', label=rpc_name))
                graph.add_edge(WorkflowEdge(source=current_svc, target=rpc_id, relation='calls_api'))


def _parse_mq_config(root, graph: WorkflowGraph):
    """Detect MQ topics from docker-compose environment variables (STORY-slim-044 R3).

    Scans for KAFKA_TOPIC, *_QUEUE_URL, *_TOPIC_ARN patterns in service environment blocks.
    Services with KAFKA_CONSUMER_GROUP are treated as subscribers; others as publishers.
    """
    try:
        import yaml
    except ImportError:
        return
    root = Path(root)
    for name in ('docker-compose.yml', 'docker-compose.yaml'):
        dc_path = root / name
        if dc_path.exists():
            try:
                data = yaml.safe_load(dc_path.read_text(encoding='utf-8'))
            except Exception:
                return
            if not isinstance(data, dict):
                return
            services = data.get('services') or {}
            topic_env_pattern = re.compile(r'(?:KAFKA_TOPIC|(\w+)_QUEUE_URL|(\w+)_TOPIC_ARN)')
            for svc_name, svc_conf in services.items():
                if not isinstance(svc_conf, dict):
                    continue
                env = svc_conf.get('environment', [])
                # Normalize env: list of "K=V" or dict
                env_pairs = {}
                if isinstance(env, list):
                    for item in env:
                        if '=' in str(item):
                            k, v = str(item).split('=', 1)
                            env_pairs[k.strip()] = v.strip()
                elif isinstance(env, dict):
                    env_pairs = {str(k): str(v) for k, v in env.items()}
                has_consumer_group = any('CONSUMER_GROUP' in k for k in env_pairs)
                for key, val in env_pairs.items():
                    if 'CONSUMER_GROUP' in key:
                        continue
                    m = topic_env_pattern.match(key)
                    if m:
                        if key == 'KAFKA_TOPIC':
                            topic_name = val
                        elif m.group(1):  # _QUEUE_URL
                            topic_name = key.rsplit('_QUEUE_URL', 1)[0].lower().replace('_', '-')
                        elif m.group(2):  # _TOPIC_ARN
                            topic_name = key.rsplit('_TOPIC_ARN', 1)[0].lower().replace('_', '-')
                        else:
                            continue
                        graph.add_node(WorkflowNode(id=topic_name, kind='topic', label=topic_name))
                        graph.add_node(WorkflowNode(id=svc_name, kind='service', label=svc_name))
                        if has_consumer_group:
                            graph.add_edge(WorkflowEdge(source=topic_name, target=svc_name, relation='subscribes'))
                        else:
                            graph.add_edge(WorkflowEdge(source=svc_name, target=topic_name, relation='publishes'))
            return


def _scan_mq_source_patterns(root, graph: WorkflowGraph):
    """Scan source code for MQ producer/consumer patterns (STORY-slim-044 R4).

    Detects: producer.send("topic"), @KafkaListener(topics="topic"),
    channel.publish/consume, KafkaTemplate.send().
    """
    root = Path(root)
    patterns = [
        re.compile(r'producer\.send\(\s*["\']([^"\']+)["\']\s*'),          # Python/generic
        re.compile(r'KafkaTemplate\.send\(\s*["\']([^"\']+)["\']\s*'),     # Java Spring
        re.compile(r'@KafkaListener\(\s*topics\s*=\s*["\']([^"\']+)["\']\s*'),  # Java Spring
        re.compile(r'channel\.publish\(\s*["\']([^"\']+)["\']\s*'),        # Node.js
        re.compile(r'channel\.consume\(\s*["\']([^"\']+)["\']\s*'),        # Node.js
        re.compile(r'@app\.task\(\s*name\s*=\s*["\']([^"\']+)["\']\s*'),   # Celery
    ]
    consumer_keywords = {'KafkaListener', 'consume', 'subscribe'}
    # Find service dirs by looking at docker-compose build contexts
    service_dirs = {}
    try:
        import yaml
        for name in ('docker-compose.yml', 'docker-compose.yaml'):
            dc_path = root / name
            if dc_path.exists():
                data = yaml.safe_load(dc_path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    for svc_name, svc_conf in (data.get('services') or {}).items():
                        if isinstance(svc_conf, dict) and svc_conf.get('build'):
                            build_ctx = svc_conf['build']
                            if isinstance(build_ctx, dict):
                                build_ctx = build_ctx.get('context', '.')
                            service_dirs[str(root / build_ctx)] = svc_name
                break
    except Exception:
        pass
    if not service_dirs:
        return
    for svc_dir_str, svc_name in service_dirs.items():
        svc_dir = Path(svc_dir_str)
        if not svc_dir.is_dir():
            continue
        for ext in ('**/*.py', '**/*.java', '**/*.js', '**/*.ts', '**/*.go'):
            for src_file in svc_dir.glob(ext):
                try:
                    content = src_file.read_text(encoding='utf-8', errors='replace')
                except Exception:
                    continue
                for pat in patterns:
                    for m in pat.finditer(content):
                        topic_name = m.group(1)
                        graph.add_node(WorkflowNode(id=topic_name, kind='topic', label=topic_name))
                        graph.add_node(WorkflowNode(id=svc_name, kind='service', label=svc_name))
                        is_consumer = any(kw in pat.pattern for kw in consumer_keywords)
                        if is_consumer:
                            graph.add_edge(WorkflowEdge(source=topic_name, target=svc_name, relation='subscribes'))
                        else:
                            graph.add_edge(WorkflowEdge(source=svc_name, target=topic_name, relation='publishes'))


class ServiceParser(TopologyParser):
    """Service topology parser for microservice architectures (STORY-slim-042 R1)."""
    markers = ['docker-compose.yml', 'docker-compose.yaml', 'openapi.yaml', 'swagger.json']
    kind_order = ['service', 'api', 'topic']
    kind_labels = {'service': 'Services', 'api': 'APIs', 'topic': 'Topics'}

    def parse(self, root) -> WorkflowGraph:
        graph = WorkflowGraph()
        _parse_docker_compose(root, graph)
        _parse_openapi(root, graph)
        _parse_proto_files(root, graph)
        _parse_mq_config(root, graph)
        _scan_mq_source_patterns(root, graph)
        return graph


# STORY-slim-042 R5: Register ServiceParser
_TOPOLOGY_PARSERS['service'] = ServiceParser()


# --- Frontend Topology (STORY-slim-045, 046) ---

def _is_local_import(src: str) -> bool:
    """Returns True if the import source is a local project path (not an npm package)."""
    return src.startswith('./') or src.startswith('../') or src.startswith('@/')


def _parse_app_router_pages(root, graph: WorkflowGraph) -> list:
    """Parse Next.js App Router pages (app/**/page.tsx|jsx) (STORY-slim-045 R2).

    Returns list of (route_id, file_path) tuples for downstream import analysis.
    """
    root = Path(root)
    app_dir = root / 'app'
    if not app_dir.is_dir():
        return []
    page_files = []
    for ext in ('page.tsx', 'page.jsx'):
        for p in sorted(app_dir.rglob(ext)):
            rel = p.parent.relative_to(app_dir)
            route = '/' + rel.as_posix() if rel.parts else '/'
            graph.add_node(WorkflowNode(id=route, kind='page', label=route))
            page_files.append((route, p))
    return page_files


def _parse_pages_router(root, graph: WorkflowGraph) -> list:
    """Parse Next.js Pages Router (pages/**/*.tsx) (STORY-slim-045 R3).

    Returns list of (route_id, file_path) tuples.
    Excludes _app.tsx and _document.tsx.
    """
    root = Path(root)
    pages_dir = root / 'pages'
    if not pages_dir.is_dir():
        return []
    page_files = []
    for p in sorted(pages_dir.rglob('*.tsx')):
        if p.name.startswith('_'):
            continue
        rel = p.relative_to(pages_dir)
        route_name = rel.with_suffix('').as_posix()
        if route_name == 'index':
            route = '/'
        elif route_name.endswith('/index'):
            route = '/' + route_name[:-len('/index')]
        else:
            route = '/' + route_name
        graph.add_node(WorkflowNode(id=route, kind='page', label=route))
        page_files.append((route, p))
    return page_files


def _parse_vue_routes(root, graph: WorkflowGraph) -> list:
    """Parse Vue Router route definitions from src/router/index.ts (STORY-slim-045 R4).

    Returns list of (route_id, None) tuples (no file_path since imports are inline).
    """
    root = Path(root)
    router_path = None
    for candidate in [root / 'src/router/index.ts', root / 'src/router/index.js']:
        if candidate.exists():
            router_path = candidate
            break
    if router_path is None:
        return []
    try:
        content = router_path.read_text(encoding='utf-8')
    except Exception:
        return []
    _skip_keywords = {'createRouter', 'createWebHistory', 'createWebHashHistory', 'Vue', 'defineComponent'}
    path_pattern = re.compile(r"path:\s*['\"]([^'\"]+)['\"]")
    comp_pattern = re.compile(r"component:\s*(\w+)")
    path_matches = list(path_pattern.finditer(content))
    comp_matches = list(comp_pattern.finditer(content))
    page_files = []
    for pm in path_matches:
        route = pm.group(1)
        graph.add_node(WorkflowNode(id=route, kind='page', label=route))
        for cm in comp_matches:
            if cm.start() > pm.start():
                comp_name = cm.group(1)
                if comp_name not in _skip_keywords:
                    graph.add_node(WorkflowNode(id=comp_name, kind='component', label=comp_name))
                    graph.add_edge(WorkflowEdge(source=route, target=comp_name, relation='renders'))
                break
        page_files.append((route, None))
    return page_files


def _parse_component_imports(page_files: list, graph: WorkflowGraph) -> None:
    """Parse import statements from page files to create component nodes and renders edges (STORY-slim-045 R5).

    Only tracks local project imports (not npm packages).
    page_files: list of (page_id, file_path) tuples.
    """
    default_import = re.compile(r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]")
    named_import = re.compile(r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]")
    for page_id, file_path in page_files:
        if file_path is None:
            continue
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        # Default imports: import ComponentName from './path'
        for m in default_import.finditer(content):
            name, src = m.group(1), m.group(2)
            if _is_local_import(src):
                graph.add_node(WorkflowNode(id=name, kind='component', label=name))
                graph.add_edge(WorkflowEdge(source=page_id, target=name, relation='renders'))
        # Named imports: import { Button, Card } from './path'
        for m in named_import.finditer(content):
            names_str, src = m.group(1), m.group(2)
            if _is_local_import(src):
                for n in names_str.split(','):
                    n = n.strip().split(' as ')[0].strip()
                    if n and n[0].isupper():  # convention: components are PascalCase
                        graph.add_node(WorkflowNode(id=n, kind='component', label=n))
                        graph.add_edge(WorkflowEdge(source=page_id, target=n, relation='renders'))


def _scan_hooks(root, graph: WorkflowGraph) -> list:
    """Scan hook directories and add hook nodes to the graph (STORY-slim-046 R1, R3).

    Returns list of (hook_id, file_path) tuples for downstream import analysis.
    Scans: src/hooks/, composables/, src/composables/.
    Only files with 'use' prefix are treated as hooks.
    """
    root = Path(root)
    hook_dirs = [root / 'src/hooks', root / 'composables', root / 'src/composables']
    result = []
    for hook_dir in hook_dirs:
        if not hook_dir.is_dir():
            continue
        for f in sorted(list(hook_dir.glob('*.ts')) + list(hook_dir.glob('*.js'))):
            stem = f.stem
            if stem.startswith('use'):
                graph.add_node(WorkflowNode(id=stem, kind='hook', label=stem))
                result.append((stem, f))
    return result


def _scan_stores(root, graph: WorkflowGraph) -> list:
    """Scan store directories and add store nodes to the graph (STORY-slim-046 R2, R4).

    Returns list of (store_id, file_path) tuples for downstream import analysis.
    Scans: src/store/, src/stores/, src/slices/.
    Files using createSlice/create/defineStore are treated as stores.
    """
    root = Path(root)
    store_dirs = [root / 'src/store', root / 'src/stores', root / 'src/slices']
    store_patterns = [
        re.compile(r'createSlice\('),   # Redux
        re.compile(r'\bcreate\('),      # Zustand
        re.compile(r'defineStore\('),   # Pinia
    ]
    result = []
    for store_dir in store_dirs:
        if not store_dir.is_dir():
            continue
        for f in sorted(list(store_dir.glob('*.ts')) + list(store_dir.glob('*.js'))):
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            stem = f.stem
            if any(pat.search(content) for pat in store_patterns):
                graph.add_node(WorkflowNode(id=stem, kind='store', label=stem))
                result.append((stem, f))
    return result


def _parse_hook_store_imports(node_files: list, graph: WorkflowGraph) -> None:
    """Parse imports to create uses_hook and reads_store edges (STORY-slim-046 R3-R5).

    node_files: list of (any, node_id, file_path) tuples.
    Creates:
    - component/page → hook: uses_hook edge
    - hook → store: reads_store edge
    """
    default_import = re.compile(r"import\s+\{?(\w+)\}?\s+from\s+['\"]([^'\"]+)['\"]")
    named_import = re.compile(r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]")
    hook_ids = {nid for nid, n in graph.nodes.items() if n.kind == 'hook'}
    store_ids = {nid for nid, n in graph.nodes.items() if n.kind == 'store'}
    for _, node_id, file_path in node_files:
        if file_path is None:
            continue
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        imported = set()
        for m in default_import.finditer(content):
            name, src = m.group(1), m.group(2)
            if _is_local_import(src):
                imported.add(name)
        for m in named_import.finditer(content):
            names_str, src = m.group(1), m.group(2)
            if _is_local_import(src):
                for n in names_str.split(','):
                    imported.add(n.strip().split(' as ')[0].strip())
        for imported_name in imported:
            if imported_name in hook_ids:
                graph.add_edge(WorkflowEdge(source=node_id, target=imported_name, relation='uses_hook'))
            elif imported_name in store_ids:
                graph.add_edge(WorkflowEdge(source=node_id, target=imported_name, relation='reads_store'))


class FrontendParser(TopologyParser):
    """Frontend topology parser for Next.js/Nuxt/Vue projects (STORY-slim-045 R1).

    Phase 1 (STORY-slim-045): page nodes, component nodes, renders edges.
    Phase 2 (STORY-slim-046): hook nodes, store nodes, uses_hook/reads_store edges.
    """
    markers = [
        'next.config.js', 'next.config.ts', 'nuxt.config.ts', 'vite.config.ts',
        'app/layout.tsx', 'pages/_app.tsx', 'src/router/',
    ]

    def parse(self, root) -> WorkflowGraph:
        graph = WorkflowGraph()
        root = Path(root)
        # Phase 1: pages, routes, and component import edges (STORY-slim-045)
        page_files = []
        page_files.extend(_parse_app_router_pages(root, graph))
        page_files.extend(_parse_pages_router(root, graph))
        page_files.extend(_parse_vue_routes(root, graph))
        _parse_component_imports(page_files, graph)
        # Phase 2: hooks and stores (STORY-slim-046)
        hook_files = _scan_hooks(root, graph)
        _scan_stores(root, graph)
        # Phase 3: hook→store import edges
        _parse_hook_store_imports(
            [(None, hid, fp) for hid, fp in hook_files],
            graph,
        )
        return graph


# STORY-slim-045 R6: Register FrontendParser
_TOPOLOGY_PARSERS['frontend'] = FrontendParser()


# ---------------------------------------------------------------------------
# STORY-slim-066: ApiCallParser — tree-sitter-based API call extraction (R1)
# ---------------------------------------------------------------------------

_DEFAULT_FETCH_FUNCTIONS = ["fetch", "apiFetch", "axios", "useQuery", "useSWR", "useMutation"]

# tree-sitter queries for API call extraction
_API_CALL_QUERY_SRC = '''[
  (call_expression
    function: (identifier) @callee
    arguments: (arguments . (string) @api_path))
  (call_expression
    function: (identifier) @callee
    arguments: (arguments . (template_string) @dynamic_path))
  (call_expression
    function: (member_expression
      object: (identifier) @obj
      property: (property_identifier) @method)
    arguments: (arguments . (string) @api_path))
  (call_expression
    function: (member_expression
      object: (identifier) @obj
      property: (property_identifier) @method)
    arguments: (arguments . (template_string) @dynamic_path))
]'''


def _find_enclosing_func_name(node):
    """Walk tree-sitter parents to find the enclosing function/component name."""
    current = node.parent
    while current:
        if current.type in ('function_declaration', 'method_definition'):
            for child in current.children:
                if child.type == 'identifier':
                    return child.text.decode()
                if child.type == 'property_identifier':
                    return child.text.decode()
        if current.type in ('lexical_declaration', 'variable_declaration'):
            for child in current.children:
                if child.type == 'variable_declarator':
                    name_node = child.child_by_field_name('name')
                    if name_node:
                        return name_node.text.decode()
        if current.type == 'export_default_declaration':
            for child in current.children:
                if child.type == 'function_declaration':
                    for sub in child.children:
                        if sub.type == 'identifier':
                            return sub.text.decode()
        current = current.parent
    return None


class ApiCallParser(TopologyParser):
    """Extract API call topology from frontend source files (STORY-slim-066 R1).

    Uses tree-sitter-typescript for AST-accurate call extraction.
    Falls back gracefully when tree-sitter is not installed.
    """
    markers = FrontendParser.markers  # same detection as frontend

    def __init__(self, fetch_functions=None):
        self._fetch_functions = fetch_functions or list(_DEFAULT_FETCH_FUNCTIONS)
        self._ts_parser = None
        self._api_query = None
        if _HAS_TREE_SITTER:
            try:
                import tree_sitter_typescript as _tsts
                lang = _TSLanguage(_tsts.language_tsx())
                self._ts_parser = _TSParser(lang)
                self._api_query = _TSQuery(lang, _API_CALL_QUERY_SRC)
            except (ImportError, Exception):
                pass

    def detect(self, root) -> bool:
        if self._ts_parser is None:
            return False
        return super().detect(root)

    def parse(self, root) -> WorkflowGraph:
        graph = WorkflowGraph()
        if self._ts_parser is None:
            return graph
        root = Path(root)
        ts_files = []
        for ext in ('*.ts', '*.tsx', '*.js', '*.jsx'):
            ts_files.extend(root.rglob(ext))
        fetch_set = set(self._fetch_functions)
        for fpath in sorted(ts_files):
            # Skip node_modules, .git, etc.
            parts = fpath.parts
            if any(p.startswith('.') or p == 'node_modules' for p in parts):
                continue
            try:
                source = fpath.read_bytes()
                tree = self._ts_parser.parse(source)
            except Exception:
                continue
            cursor = _TSQueryCursor(self._api_query)
            matches = cursor.matches(tree.root_node)
            for _, match_dict in matches:
                callee_nodes = match_dict.get('callee', [])
                obj_nodes = match_dict.get('obj', [])
                method_nodes = match_dict.get('method', [])
                path_nodes = match_dict.get('api_path', [])
                dynamic_nodes = match_dict.get('dynamic_path', [])
                # Determine the fetch function name
                func_name = None
                call_node = None
                if callee_nodes:
                    func_name = callee_nodes[0].text.decode()
                    call_node = callee_nodes[0]
                elif obj_nodes and method_nodes:
                    func_name = obj_nodes[0].text.decode()
                    call_node = obj_nodes[0]
                if func_name not in fetch_set:
                    continue
                # Extract path
                is_dynamic = False
                api_path = None
                if path_nodes:
                    raw = path_nodes[0].text.decode().strip('"\'')
                    api_path = raw
                elif dynamic_nodes:
                    is_dynamic = True
                    raw = dynamic_nodes[0].text.decode()
                    api_path = raw
                if api_path is None:
                    continue
                # Build label
                label = f"[dynamic] {api_path}" if is_dynamic else api_path
                node_id = f"api:{label}"
                graph.add_node(WorkflowNode(id=node_id, kind='api_call', label=label))
                # Find enclosing function for edge source
                enclosing = _find_enclosing_func_name(call_node)
                if enclosing:
                    graph.add_edge(WorkflowEdge(source=enclosing, target=node_id, relation='fetches'))
        return graph


_TOPOLOGY_PARSERS['api_call'] = ApiCallParser()


# ---------------------------------------------------------------------------
# STORY-slim-066: AgentParser — multi-strategy agent topology (R2)
# ---------------------------------------------------------------------------

def _parse_langgraph_ast(filepath):
    """Strategy 1: Parse LangGraph StateGraph patterns using stdlib ast."""
    import ast as _ast
    try:
        source = filepath.read_text(encoding='utf-8', errors='replace')
        tree = _ast.parse(source)
    except Exception:
        return [], []
    nodes = []
    edges = []
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Expr) and not isinstance(node, _ast.Assign):
            if isinstance(node, _ast.Call):
                _langgraph_process_call(node, nodes, edges)
            continue
        # For Expr and Assign, check value
        value = node.value if isinstance(node, _ast.Expr) else node.value if isinstance(node, _ast.Assign) else None
        if isinstance(value, _ast.Call):
            _langgraph_process_call(value, nodes, edges)
    return nodes, edges


def _langgraph_process_call(call_node, nodes, edges):
    """Extract add_node / add_edge / add_conditional_edges from a Call AST node."""
    import ast as _ast
    func = call_node.func
    method_name = None
    if isinstance(func, _ast.Attribute):
        method_name = func.attr
    elif isinstance(func, _ast.Name):
        method_name = func.id
    if method_name == 'add_node' and len(call_node.args) >= 1:
        arg = call_node.args[0]
        if isinstance(arg, _ast.Constant) and isinstance(arg.value, str):
            nodes.append(arg.value)
    elif method_name == 'add_edge' and len(call_node.args) >= 2:
        src_arg, tgt_arg = call_node.args[0], call_node.args[1]
        if isinstance(src_arg, _ast.Constant) and isinstance(tgt_arg, _ast.Constant):
            if isinstance(src_arg.value, str) and isinstance(tgt_arg.value, str):
                edges.append((src_arg.value, tgt_arg.value))
    elif method_name == 'add_conditional_edges' and len(call_node.args) >= 3:
        src_arg = call_node.args[0]
        mapping_arg = call_node.args[2] if len(call_node.args) >= 3 else None
        if isinstance(src_arg, _ast.Constant) and isinstance(src_arg.value, str):
            src_name = src_arg.value
            if isinstance(mapping_arg, _ast.Dict):
                for val in mapping_arg.values:
                    if isinstance(val, _ast.Constant) and isinstance(val.value, str):
                        if val.value not in ('__end__', 'END'):
                            edges.append((src_name, val.value))


def _parse_yaml_agents(agents_dir):
    """Strategy 2: Parse YAML agent definitions from agents/ directory."""
    import yaml
    nodes = []
    edges = []
    if not agents_dir.is_dir():
        return nodes, edges
    for yf in sorted(agents_dir.glob('*.yaml')):
        try:
            data = yaml.safe_load(yf.read_text(encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        agent = data.get('agent', data)
        name = agent.get('name')
        if name:
            nodes.append(name)
            delegates = agent.get('delegates_to', [])
            if isinstance(delegates, list):
                for target in delegates:
                    edges.append((name, target))
    return nodes, edges


def _parse_mcp_settings(settings_path):
    """Strategy 3: Parse MCP server definitions from settings JSON."""
    import json
    nodes = []
    try:
        data = json.loads(settings_path.read_text(encoding='utf-8'))
    except Exception:
        return nodes
    servers = data.get('mcpServers', {})
    if isinstance(servers, dict):
        for name in servers:
            nodes.append(name)
    return nodes


class AgentParser(TopologyParser):
    """Multi-strategy agent topology parser (STORY-slim-066 R2).

    Strategy priority:
    1. LangGraph/LangChain (stdlib ast) — highest precision
    2. Declarative YAML configs (agents/ dir)
    3. MCP config (.claude/settings.json)
    4. A2A Agent Card (local files only) — future
    """
    markers = [
        'agents/', 'crew.yaml', 'AGENTS.md',
        '.claude/settings.json', 'mcp.json',
    ]

    def detect(self, root) -> bool:
        root = Path(root)
        # Check standard markers
        if super().detect(root):
            return True
        # Check for LangGraph imports in Python files
        for py in root.rglob('*.py'):
            parts = py.parts
            if any(p.startswith('.') or p in ('node_modules', '__pycache__', '.venv', 'venv') for p in parts):
                continue
            try:
                content = py.read_text(encoding='utf-8', errors='replace')
                if 'StateGraph' in content or 'from langgraph' in content:
                    return True
            except Exception:
                continue
        return False

    def parse(self, root) -> WorkflowGraph:
        graph = WorkflowGraph()
        root = Path(root)
        seen_agents = set()

        # Strategy 1: LangGraph (ast)
        for py in sorted(root.rglob('*.py')):
            parts = py.parts
            if any(p.startswith('.') or p in ('node_modules', '__pycache__', '.venv', 'venv') for p in parts):
                continue
            try:
                content = py.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            if 'StateGraph' not in content and 'add_node' not in content:
                continue
            lg_nodes, lg_edges = _parse_langgraph_ast(py)
            for name in lg_nodes:
                if name not in seen_agents:
                    seen_agents.add(name)
                    graph.add_node(WorkflowNode(id=name, kind='agent_def', label=name))
            for src, tgt in lg_edges:
                graph.add_edge(WorkflowEdge(source=src, target=tgt, relation='orchestrates'))

        # Strategy 2: Declarative YAML
        agents_dir = root / 'agents'
        if not agents_dir.is_dir():
            agents_dir = root / 'agents_dir'  # fixture compat
        yaml_nodes, yaml_edges = _parse_yaml_agents(agents_dir)
        for name in yaml_nodes:
            if name not in seen_agents:
                seen_agents.add(name)
                graph.add_node(WorkflowNode(id=name, kind='agent_def', label=name))
        for src, tgt in yaml_edges:
            graph.add_edge(WorkflowEdge(source=src, target=tgt, relation='orchestrates'))

        # Strategy 3: MCP config
        mcp_paths = [root / '.claude' / 'settings.json', root / 'mcp.json']
        for mcp_path in mcp_paths:
            if mcp_path.exists():
                mcp_nodes = _parse_mcp_settings(mcp_path)
                for name in mcp_nodes:
                    if name not in seen_agents:
                        seen_agents.add(name)
                        graph.add_node(WorkflowNode(id=name, kind='agent_def', label=name))

        # Strategy 4: A2A (future — local file parsing only)

        return graph


_TOPOLOGY_PARSERS['agent'] = AgentParser()


# ---------------------------------------------------------------------------
# STORY-slim-066: API Convention Summary (R4)
# ---------------------------------------------------------------------------

def api_convention_summary(root):
    """Analyze API call patterns and return convention summary.

    Returns dict with: prefixes (set), fetch_functions (set), total_calls (int).
    """
    parser = ApiCallParser()
    graph = parser.parse(root)
    prefixes = set()
    functions = set()
    total = 0
    for node in graph.nodes.values():
        if node.kind != 'api_call':
            continue
        total += 1
        label = node.label.replace('[dynamic] ', '')
        # Extract prefix: everything up to and including the Nth /
        parts = label.strip('"\'`').split('/')
        if len(parts) >= 3:
            prefix = '/'.join(parts[:3]) + '/'
            prefixes.add(prefix)
    for edge in graph.edges:
        if edge.relation == 'fetches':
            # The source is the function name; we want the fetch function
            # Look at the node label for the target
            pass
    # Extract fetch function names from the parse
    functions = set(parser._fetch_functions) & _get_used_fetch_functions(root, parser)
    return {
        'prefixes': prefixes,
        'fetch_functions': functions,
        'total_calls': total,
    }


def _get_used_fetch_functions(root, parser):
    """Scan files to determine which fetch functions are actually used."""
    root = Path(root)
    used = set()
    for ext in ('*.ts', '*.tsx', '*.js', '*.jsx'):
        for fpath in root.rglob(ext):
            parts = fpath.parts
            if any(p.startswith('.') or p == 'node_modules' for p in parts):
                continue
            try:
                content = fpath.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            for fn in parser._fetch_functions:
                if fn in content:
                    used.add(fn)
    return used


def _parse_commands(commands_dir, graph: WorkflowGraph):
    """Parse command markdown files and extract command→agent, command→skill edges (R2)."""
    if not commands_dir.is_dir():
        return
    agent_pattern = re.compile(r'\*\*Agent\*\*:\s*(.+)')
    role_pattern = re.compile(r'\*\*Role\*\*:\s*(.+)')
    skill_pattern = re.compile(r'pactkit-(\w+)')
    for md in sorted(commands_dir.glob('*.md')):
        cmd_name = md.stem  # e.g. 'project-act'
        content = md.read_text(encoding='utf-8')
        graph.add_node(WorkflowNode(id=cmd_name, kind='command', label=cmd_name))
        # Extract agent role
        for pat in (agent_pattern, role_pattern):
            m = pat.search(content)
            if m:
                agent_label = m.group(1).strip()
                agent_id = re.sub(r'[^a-zA-Z0-9]', '-', agent_label).strip('-').lower()
                graph.add_node(WorkflowNode(id=agent_id, kind='agent', label=agent_label))
                graph.add_edge(WorkflowEdge(source=cmd_name, target=agent_id, relation='invokes'))
                break
        # Extract skill references
        seen_skills = set()
        for m in skill_pattern.finditer(content):
            skill_name = f'pactkit-{m.group(1)}'
            if skill_name not in seen_skills:
                seen_skills.add(skill_name)
                graph.add_node(WorkflowNode(id=skill_name, kind='skill', label=skill_name))
                graph.add_edge(WorkflowEdge(source=cmd_name, target=skill_name, relation='depends_on'))


def _parse_routing_table(rules_dir, graph: WorkflowGraph):
    """Parse rules/04-routing-table.md to extract command→agent→playbook mappings (R3)."""
    rt_path = rules_dir / '04-routing-table.md' if rules_dir.is_dir() else None
    if not rt_path or not rt_path.exists():
        return
    content = rt_path.read_text(encoding='utf-8')
    # Pattern: ### Name (`/project-xxx`) \n - **Role**: Agent Role \n - **Playbook**: `path`
    block_pattern = re.compile(
        r'###\s+\w+[^(]*\(`/([^)]+)`\)\s*\n'
        r'(?:.*?\n)*?'
        r'-\s*\*\*Role\*\*:\s*(.+)',
        re.MULTILINE
    )
    for m in block_pattern.finditer(content):
        cmd_name = m.group(1).strip()
        agent_label = m.group(2).strip()
        agent_id = re.sub(r'[^a-zA-Z0-9]', '-', agent_label).strip('-').lower()
        graph.add_node(WorkflowNode(id=cmd_name, kind='command', label=cmd_name))
        graph.add_node(WorkflowNode(id=agent_id, kind='agent', label=agent_label))
        graph.add_edge(WorkflowEdge(source=cmd_name, target=agent_id, relation='invokes'))


def _scan_skill_files(skills_dir, graph: WorkflowGraph):
    """Discover skill directories and their script files (R4)."""
    if not skills_dir.is_dir():
        return
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_name = skill_dir.name
        graph.add_node(WorkflowNode(id=skill_name, kind='skill', label=skill_name))
        scripts_dir = skill_dir / 'scripts'
        if scripts_dir.is_dir():
            for script in sorted(scripts_dir.iterdir()):
                if script.is_file():
                    file_id = f'{skill_name}/{script.name}'
                    graph.add_node(WorkflowNode(id=file_id, kind='file', label=script.name))
                    graph.add_edge(WorkflowEdge(source=skill_name, target=file_id, relation='contains'))


def _parse_pdca_sequence(commands_dir, graph: WorkflowGraph):
    """Parse project-sprint.md to extract PDCA command→command sequence edges (STORY-slim-039 R1).

    Looks for 'commands/project-*.md' references in execution order and creates
    'sequence' edges between consecutive commands that exist in the graph.
    """
    commands_dir = Path(commands_dir)
    if not commands_dir.is_dir():
        return
    sprint_path = commands_dir / 'project-sprint.md'
    if not sprint_path.exists():
        return
    content = sprint_path.read_text(encoding='utf-8')
    # Extract ordered command references: commands/project-xxx.md
    cmd_ref_pattern = re.compile(r'commands/(project-\w+)\.md')
    ordered_cmds = []
    seen = set()
    for m in cmd_ref_pattern.finditer(content):
        cmd_name = m.group(1)
        if cmd_name != 'project-sprint' and cmd_name not in seen:
            seen.add(cmd_name)
            ordered_cmds.append(cmd_name)
    # Create sequence edges between consecutive commands that exist in the graph
    for i in range(len(ordered_cmds) - 1):
        src, dst = ordered_cmds[i], ordered_cmds[i + 1]
        if src in graph.nodes and dst in graph.nodes:
            graph.add_edge(WorkflowEdge(source=src, target=dst, relation='sequence'))


def regression_workflow_impact(target='.', changed_files=None):
    """Workflow impact for regression gate — informational only (STORY-slim-038 R1-R4).

    Returns a list of impact description strings. Empty list if no matches or on failure.
    """
    if not changed_files:
        return []
    try:
        root = Path(target).resolve()
        graph = build_workflow_graph(root=root)
        if not graph.nodes:
            return []

        # Match changed files against graph nodes (file, skill, service nodes)
        file_nodes = {n.id: n for n in graph.nodes.values() if n.kind == 'file'}
        matched_entries = set()
        for cf in changed_files:
            cf_basename = cf.rsplit('/', 1)[-1] if '/' in cf else cf
            for fid, fnode in file_nodes.items():
                if cf_basename == fnode.label or cf_basename in fid:
                    matched_entries.add(fid)
            # Also check skill names
            for nid, node in graph.nodes.items():
                if node.kind == 'skill' and node.label in cf:
                    matched_entries.add(nid)
            # STORY-slim-043 R3: Match service nodes by name in file path
            for nid, node in graph.nodes.items():
                if node.kind == 'service' and node.id in cf:
                    matched_entries.add(nid)
            # STORY-slim-047 R4: Match hook/store nodes by name in file path
            for nid, node in graph.nodes.items():
                if node.kind in ('hook', 'store') and node.id in cf:
                    matched_entries.add(nid)

        if not matched_entries:
            return []

        lines = []
        # Determine which kinds to report as "affected"
        # (commands for PDCA, services for microservice, pages for frontend)
        report_kinds = {'command', 'service', 'page'}
        for entry_id in sorted(matched_entries):
            reached = graph.reverse_reach(entry_id)
            affected = sorted(
                n.label for nid, n in graph.nodes.items()
                if nid in reached and n.kind in report_kinds and nid != entry_id
            )
            if affected:
                entry_label = graph.nodes.get(entry_id, WorkflowNode(id=entry_id, kind='file', label=entry_id)).label
                lines.append(f'Workflow Impact: {entry_label} changed → affects: {", ".join(affected)}')
        return lines
    except Exception as exc:
        # R19 (STORY-slim-052): Log unexpected errors instead of silently swallowing
        import sys as _sys
        print(f"⚠️ regression_workflow_impact failed: {type(exc).__name__}: {exc}", file=_sys.stderr)
        return []


def workflow_impact(target='.', entry=None, entries=None):
    """Find workflow nodes affected by a changed skill/file (STORY-slim-037).

    Returns a formatted string showing affected commands/agents/skills/files.
    """
    root = Path(target).resolve()
    graph = build_workflow_graph(root=root)

    # Collect all entry points
    entry_ids = []
    if entries:
        entry_ids.extend(entries)
    elif entry:
        entry_ids.append(entry)
    if not entry_ids:
        return 'Error: no entry point specified'

    # Validate entries
    all_node_ids = set(graph.nodes.keys())
    for eid in entry_ids:
        if eid not in all_node_ids:
            # R15: Show all available nodes (not truncated to 20)
            available = ', '.join(sorted(all_node_ids))
            return f'Error: "{eid}" not found in workflow graph. Available nodes: {available}'

    # Union of reverse reach for all entries
    all_reached = set()
    for eid in entry_ids:
        all_reached |= graph.reverse_reach(eid)

    # Group by kind
    grouped: dict[str, list[str]] = {}
    for nid in sorted(all_reached):
        node = graph.nodes.get(nid)
        if node:
            grouped.setdefault(node.kind, []).append(node.label)

    # Format output — STORY-slim-041 R6: dynamic kind_labels
    lines = [f'Workflow Impact for "{", ".join(entry_ids)}":']
    _known_order = ['command', 'agent', 'skill', 'file']
    _known_labels = {'command': 'Commands', 'agent': 'Agents', 'skill': 'Skills', 'file': 'Files'}
    all_kinds = sorted(grouped.keys())
    kind_order = [k for k in _known_order if k in all_kinds] + [k for k in all_kinds if k not in _known_order]
    kind_labels = {**_known_labels, **{k: k.title() + 's' for k in all_kinds if k not in _known_labels}}
    for kind in kind_order:
        items = grouped.get(kind, [])
        if items:
            lines.append(f'  {kind_labels[kind]}: {", ".join(items)}')
    return nl().join(lines)


def build_workflow_graph(root=None, commands_dir=None, rules_dir=None, skills_dir=None):
    """Build a complete WorkflowGraph via topology detection + parser registry (STORY-slim-041 R3).

    Accepts explicit dirs for testing (bypasses auto-detect, uses PdcaParser directly).
    """
    # R4: Explicit dirs bypass auto-detection — delegate directly to PdcaParser
    if commands_dir is not None or rules_dir is not None or skills_dir is not None:
        pdca = PdcaParser()
        return pdca.parse(root or '.', commands_dir=commands_dir, rules_dir=rules_dir, skills_dir=skills_dir)

    if root is None:
        return WorkflowGraph()

    root = Path(root).resolve()
    # Auto-detect topologies and merge results (STORY-slim-040 R3, R6)
    detected = detect_topology(root)
    merged = WorkflowGraph()
    for topo_name in detected:
        parser = _TOPOLOGY_PARSERS.get(topo_name)
        if parser:
            sub = parser.parse(root)
            for node in sub.nodes.values():
                merged.add_node(node)
            for edge in sub.edges:
                merged.add_edge(edge)
    return merged


# --- Unified Layered Graph (STORY-slim-048) ---

def _load_code_graph(root) -> tuple:
    """Build a code-level WorkflowGraph from source files (STORY-slim-048 R1).

    Uses the existing LanguageAnalyzer pipeline to extract function-level nodes.
    Returns (WorkflowGraph with 'function' kind nodes, func_registry dict).
    func_registry: {func_name: file_path_string}
    """
    root = Path(root)
    graph = WorkflowGraph()
    func_registry: dict[str, str] = {}

    stack = _detect_stack(root)
    analyzer = _select_analyzer(stack)
    scan_excludes = _load_scan_excludes(root)
    file_ext = _LANG_FILE_EXT.get(stack, '.py')

    try:
        all_files, _, _ = _scan_files(root, scan_excludes=scan_excludes, file_ext=file_ext)
    except Exception:
        return graph, func_registry

    call_edges_all: dict[str, list] = {}
    for f in all_files:
        fr, ce = analyzer.extract_functions_and_calls(f)
        for fname, fpath in fr.items():
            func_registry[fname] = str(fpath)
        call_edges_all.update(ce)

    all_funcs = set(func_registry.keys())
    suffix_idx = _build_suffix_index(all_funcs)
    for func_name in all_funcs:
        graph.add_node(WorkflowNode(id=func_name, kind='function', label=func_name))
    for caller, callees in call_edges_all.items():
        if caller not in all_funcs:
            continue
        for callee in callees:
            resolved = _resolve_callee(callee, all_funcs, suffix_idx)
            if resolved:
                graph.add_edge(WorkflowEdge(source=caller, target=resolved, relation='calls'))

    return graph, func_registry


def _build_bridge_edges(func_registry: dict, topology_graph: 'WorkflowGraph', unified_graph: 'WorkflowGraph') -> None:
    """Create cross-dimension bridge edges linking code-level to topology-level nodes (STORY-slim-048 R2).

    R13: Uses exact node-ID matching (word-boundary or path-suffix) instead of
    substring to prevent false positives (e.g., "auth" matching "oauth2_client").
    """
    skill_nodes = {nid for nid, n in topology_graph.nodes.items() if n.kind == 'skill'}
    service_nodes = {nid for nid, n in topology_graph.nodes.items() if n.kind == 'service'}

    # Pre-compile word-boundary patterns for exact matching
    _skill_patterns = {sid: re.compile(r'(?:^|[_/\\])' + re.escape(sid) + r'(?:$|[_/\\])') for sid in skill_nodes}
    _svc_patterns = {sid: re.compile(r'(?:^|[_/\\])' + re.escape(sid) + r'(?:$|[_/\\])') for sid in service_nodes}

    for func_name, file_path_str in func_registry.items():
        for skill_id, pat in _skill_patterns.items():
            if pat.search(file_path_str):
                unified_graph.add_edge(WorkflowEdge(source=func_name, target=skill_id, relation='implements'))
        for svc_id, pat in _svc_patterns.items():
            if pat.search(file_path_str):
                unified_graph.add_edge(WorkflowEdge(source=func_name, target=svc_id, relation='belongs_to'))


def build_unified_graph(root) -> 'WorkflowGraph':
    """Build a unified layered graph merging all topology dimensions with code-level graph (STORY-slim-048 R1).

    Returns WorkflowGraph with layered=True.
    STORY-slim-049 R1: No truncation — full graph for accurate reverse_reach() impact analysis.
    """
    root = Path(root).resolve()
    unified = WorkflowGraph()
    unified.layered = True

    # Topology graph (PDCA + Service + Frontend)
    topology_graph = build_workflow_graph(root=root)
    for node in topology_graph.nodes.values():
        unified.add_node(node)
    for edge in topology_graph.edges:
        unified.add_edge(edge)

    # Code graph (function/calls)
    code_graph, func_registry = _load_code_graph(root)
    for node in code_graph.nodes.values():
        unified.add_node(node)
    for edge in code_graph.edges:
        unified.add_edge(edge)

    # Bridge edges across dimensions
    _build_bridge_edges(func_registry, topology_graph, unified)

    # STORY-slim-049 R1: No truncation — full graph for accurate reverse_reach() impact analysis.
    # MAX_WORKFLOW_NODES constant retained for backward compatibility but not enforced here.

    return unified


# --- STORY-slim-049: Focused Sub-Graph Export ---

_ENTRY_POINT_KINDS = {'command', 'service', 'page'}


def export_focus_graphs(graph: WorkflowGraph, output_dir) -> list:
    """Export per-entry-point focused sub-graph .mmd files (STORY-slim-049 R2).

    Identifies first-level entry points (command/service/page), extracts
    reachable sub-graphs via reverse_reach(), writes each as a standalone .mmd.
    Returns list of Path objects for written files.
    """
    output_dir = Path(output_dir)
    entry_points = [n for n in graph.nodes.values() if n.kind in _ENTRY_POINT_KINDS]
    if not entry_points:
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for entry in sorted(entry_points, key=lambda n: n.id):
        reached_ids = graph.forward_reach(entry.id)
        # Build sub-graph
        sub = WorkflowGraph()
        for nid in reached_ids:
            node = graph.nodes.get(nid)
            if node:
                sub.add_node(node)
        for edge in graph.edges:
            if edge.source in reached_ids and edge.target in reached_ids:
                sub.add_edge(edge)
        # Write .mmd
        sanitized = WorkflowGraph._sanitize_id(entry.id)
        dest = output_dir / f'focus_{sanitized}.mmd'
        _atomic_mmd_write(dest, sub.to_mermaid())
        written.append(dest)
    return written


# --- CLI ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init_arch')
    sub.add_parser('list_rules')
    p_viz = sub.add_parser('visualize')
    p_viz.add_argument('--focus')
    p_viz.add_argument('--mode', choices=['file', 'class', 'call', 'workflow', 'unified'], default='file')
    p_viz.add_argument('--entry')
    p_viz.add_argument('--depth', type=int, default=0, help='Limit graph traversal to N levels (0=unlimited)')
    p_viz.add_argument('--max-nodes', type=int, default=0, help='Truncate graph to N nodes (0=unlimited)')
    p_viz.add_argument('--reverse', action='store_true', default=False, help='Reverse BFS: find callers of entry function (STORY-053)')
    p_viz.add_argument('--lazy', action='store_true', default=False, help='Skip regeneration if graph is up-to-date')
    p_viz.add_argument('--split', action='store_true', default=False, help='Generate per-entry-point focus graphs (unified mode only)')
    p_impact = sub.add_parser('impact', help='Find test files impacted by a changed function (STORY-053)')
    p_impact.add_argument('--entry', required=True, help='Changed function name')

    a = parser.parse_args()
    if a.cmd == 'init_arch': print(init_architecture())
    elif a.cmd == 'visualize': print(visualize('.', a.focus, a.mode, a.entry, depth=a.depth, max_nodes=a.max_nodes, reverse=a.reverse, lazy=a.lazy, split=a.split))
    elif a.cmd == 'impact': print(impact('.', a.entry))
    elif a.cmd == 'list_rules': print(list_rules())
