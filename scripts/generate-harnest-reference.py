"""Refresh public Python API pages from a trusted Harnest source checkout.

Run with Harnest's development Python environment (including bundled packages):
  /path/to/Harnest/.venv/bin/python scripts/generate-harnest-reference.py /path/to/Harnest
Use --check to detect stale pages without writing them. Handwritten usage notes
live in harnest/reference/api-notes/<module>.md and survive regeneration.

Each symbol keeps its original signature, description, and fields. A collapsed
"Parameters and example" section adds a parameter table and a minimal example:
the import plus one use of the symbol, derived from the signature (`...` marks a
value you supply). Parameter descriptions come from Google-style docstrings
(Args:/Attributes:), Pydantic field descriptions, or
harnest/reference/api-details/<module>.yaml, which can also replace an example.
Curated keys, parameters, and fields are validated against the real signatures,
and every example must parse and import real public names.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import dataclasses
import enum
import importlib
import importlib.util
import inspect
import json
import keyword
from pathlib import Path
import re
import sys
import textwrap
import types
import typing

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / 'harnest/reference/api'
NOTES = ROOT / 'harnest/reference/api-notes'
DETAILS = ROOT / 'harnest/reference/api-details'
EXTRA_EXPORTS = {
    'harnest.bundle': ['BundleError', 'BundleConventionError', 'BundleImportError',
        'BundleExportError', 'BundleDuplicateError', 'BundleSkillError', 'BundleEvalError',
        'EvalSuite', 'compile_agent', 'compile_app', 'compile_application',
        'compile_artifact', 'bundle_agent', 'discover_evals'],
    'harnest.orchestrator': ['AgentSource', 'Orchestrator', 'define_orchestrator'],
}
PUBLIC_NAMES: dict[str, str] = {}
# Dataclasses with only optional private fields that the guides construct directly.
# Their signatures hide the private parameters instead of hiding the constructor.
CONSTRUCTIBLE = {'harnest.agent.Agent', 'harnest.agent.AgentDefinition', 'harnest.graph.Graph', 'harnest.skills.DecisionSkillSelector'}
# These facades are reached through public objects, not imported from internal modules.
NESTED_APIS = {
    'harnest.authoring': {
        'ProjectContext.files': ('harnest.authoring.context', 'ProjectFiles'),
        'ProjectContext.yaml': ('harnest.authoring.context', 'ProjectYAML'),
    },
    'harnest.context': {
        'SandboxHandle': ('harnest.context_sandboxes', 'SandboxHandle'),
    },
}



def slug(module: str) -> str:
    """Keep module routes stable independently of their display titles."""
    return module.removeprefix('harnest.').replace('.', '-')


def anchor(name: str) -> str:
    """Match Mintlify headings, which preserve underscores in Python names."""
    # Cron and its decorator need distinct IDs; dotted members use hyphens,
    # but replacing underscores would make links miss the rendered headings.
    return 'cron-decorator' if name == 'cron' else re.sub(r'[^a-z0-9_]+', '-', name.lower()).strip('-')


def prose(value: str) -> str:
    """Render Python docstrings as literal prose without interpreting MDX."""
    value = re.sub(r'``([^`]+)``', r'`\1`', value)
    value = re.sub(r':(?:class|func|meth|mod):`([^`]+)`', r'`\1`', value)
    parts = re.split(r'(```[\s\S]*?```|`[^`]*`)', value)
    # Code spans already protect MDX syntax; escaping them would show literal entities.
    return ''.join(part if part.startswith('`') else part.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('{', '&#123;').replace('}', '&#125;') for part in parts)


def display(value: object) -> str:
    """Normalize annotations and defaults without unstable object addresses."""
    # Forward annotations are already source expressions, not string defaults.
    if isinstance(value, str):
        return value
    # Sets have hash-dependent repr ordering; sorted literals make regeneration stable.
    if isinstance(value, frozenset):
        return 'frozenset(' + repr(sorted(value)) + ')'
    text = repr(value)
    text = re.sub(r"<class '([^']+)'>", r'\1', text)
    text = re.sub(r'<function ([\w.]+) at 0x[\da-f]+>', r'\1', text)
    text = re.sub(r'<[^>]* at 0x[\da-f]+>', '...', text)
    text = text.replace('typing.', '').replace('NoneType', 'None').replace('<factory>', '...')
    text = re.sub(r'<built-in function (\w+)>', r'\1', text)
    text = re.sub(r'<([\w.]+): [^>]+>', r'\1', text)
    for original, public in sorted(PUBLIC_NAMES.items(), key=lambda item: -len(item[0])):
        text = text.replace(original, public)
    return text


def signature(value: object, name: str) -> str | None:
    """Format exact public parameters, hiding receiver and runtime internals."""
    try:
        sig = inspect.signature(value)
    # Some native exception and typing classes do not expose a signature.
    except (ValueError, TypeError):
        return None
    parts = []
    keyword_marker = False
    for param in sig.parameters.values():
        # Receivers and private runtime handles are not caller-supplied API options.
        if param.name in {'self', 'cls'} or param.name.startswith('_'):
            continue
        # Preserve keyword-only boundaries so examples cannot imply positional support.
        if param.kind == param.KEYWORD_ONLY and not keyword_marker:
            parts.append('*')
            keyword_marker = True
        prefix = {param.VAR_POSITIONAL: '*', param.VAR_KEYWORD: '**'}.get(param.kind, '')
        # A variadic positional argument already establishes the keyword-only boundary.
        if param.kind == param.VAR_POSITIONAL:
            keyword_marker = True
        item = prefix + param.name
        # Empty annotations must stay absent rather than becoming invented Any contracts.
        if param.annotation is not param.empty:
            item += ': ' + display(param.annotation)
        # String defaults need quotes, unlike string-valued forward annotations.
        if param.default is not param.empty:
            item += ' = ' + (repr(param.default) if isinstance(param.default, str) else display(param.default))
        parts.append(item)
        # Positional-only markers preserve the source call contract.
        if param.kind == param.POSITIONAL_ONLY:
            next_params = list(sig.parameters.values())
            index = next_params.index(param)
            if index + 1 == len(next_params) or next_params[index + 1].kind != param.POSITIONAL_ONLY:
                parts.append('/')
    result = name + '(' + ', '.join(parts) + ')'
    # Multi-line signatures stay readable on narrow reference panels.
    if len(result) > 100:
        result = name + '(\n    ' + ',\n    '.join(parts) + ',\n)'
    if sig.return_annotation is not sig.empty:
        result += ' -> ' + display(sig.return_annotation)
    if inspect.iscoroutinefunction(value):
        result = 'async ' + result
    return result


def owned_type(value: object) -> bool:
    """Limit recursive inspection to Harnest-owned types and namespaces."""
    return getattr(value, '__module__', '').startswith('harnest')


SECTION = re.compile(r'^(Args|Arguments|Parameters|Returns|Yields|Example|Examples|Attributes|Raises):\s*$')
SECTION_NAMES = {'Arguments': 'Args', 'Parameters': 'Args', 'Yields': 'Returns', 'Examples': 'Example'}


def parse_doc(value: object) -> tuple[str, dict[str, str]]:
    """Split a Google-style docstring into prose and its structured sections."""
    text = inspect.cleandoc(getattr(value, '__doc__', '') or '')
    prose_lines: list[str] = []
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        match = SECTION.match(line)
        if match:
            current = SECTION_NAMES.get(match.group(1), match.group(1))
            sections[current] = []
            continue
        # A section continues through indented and blank lines; unindented text resumes prose.
        if current and (not line.strip() or line.startswith((' ', '\t'))):
            sections[current].append(line)
            continue
        current = None
        prose_lines.append(line)
    return '\n'.join(prose_lines).strip(), {k: textwrap.dedent('\n'.join(v)).strip() for k, v in sections.items()}


def doc_items(section: str) -> dict[str, str]:
    """Read `name: description` items, joining indented continuation lines."""
    items: dict[str, str] = {}
    name = None
    for line in section.splitlines():
        match = re.match(r'^\*{0,2}(\w+)(?:\s*\([^)]*\))?:\s*(.*)$', line)
        if match and not line.startswith((' ', '\t')):
            name = match.group(1)
            items[name] = match.group(2).strip()
        elif name and line.strip():
            items[name] = (items[name] + ' ' + line.strip()).strip()
    return items


def doc_example(section: str) -> str:
    """Accept fenced or indented example code from a docstring section."""
    fenced = re.search(r'```(?:python|py)?\n([\s\S]*?)```', section)
    return textwrap.dedent(fenced.group(1)).strip() if fenced else section.strip()


def description(value: object) -> str:
    """Avoid inherited built-in help masquerading as Harnest documentation."""
    return prose(parse_doc(value)[0])


def cell(value: str) -> str:
    """Keep table cells on one line without breaking the Markdown table."""
    return prose(' '.join(value.split())).replace('|', r'\|')


def code_cell(value: str) -> str:
    return '`' + value.replace('|', r'\|') + '`'


def hints(value: object) -> dict[str, object]:
    """Resolve postponed annotations when possible; never fail generation on them."""
    try:
        return typing.get_type_hints(value)
    # TYPE_CHECKING-only imports cannot always be resolved at documentation time.
    except Exception:
        return {}


def public_parameters(value: object) -> list[inspect.Parameter]:
    """Return the caller-supplied parameters that the signature block shows."""
    try:
        sig = inspect.signature(value)
    except (ValueError, TypeError):
        return []
    return [p for p in sig.parameters.values() if p.name not in {'self', 'cls'} and not p.name.startswith('_')]


def parameter_table(value: object, docs: dict[str, str]) -> list[str]:
    """Show what each parameter takes, whether it is required, and what it does."""
    params = public_parameters(value)
    if not params:
        return []
    rows = []
    described = any(docs.get(p.name) for p in params)
    for param in params:
        variadic = param.kind in {param.VAR_POSITIONAL, param.VAR_KEYWORD}
        prefix = {param.VAR_POSITIONAL: '*', param.VAR_KEYWORD: '**'}.get(param.kind, '')
        # Keyword-only is visible from `*` in the signature; positional-only is rare enough to label.
        kind = ' (positional-only)' if param.kind == param.POSITIONAL_ONLY else ''
        annotation = code_cell(display(param.annotation)) if param.annotation is not param.empty else '—'
        if variadic:
            default = 'Optional'
        elif param.default is param.empty:
            default = 'Required'
        else:
            default = code_cell(repr(param.default) if isinstance(param.default, str) else display(param.default))
        row = f'| `{prefix}{param.name}`{kind} | {annotation} | {default} |'
        if described:
            row += ' ' + (cell(docs.get(param.name, '')) or '—') + ' |'
        rows.append(row)
    header = ['| Parameter | Type | Default | Description |', '|---|---|---|---|'] if described else ['| Parameter | Type | Default |', '|---|---|---|']
    return [*header, *rows, '']


def check_example(code: str, where: str) -> None:
    """Fail on examples that do not parse or import names Harnest does not export."""
    try:
        tree = compile(code, where, 'exec', flags=ast.PyCF_ONLY_AST | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    except SyntaxError as error:
        raise ValueError(f'Example for {where} does not parse: {error}\n{code}') from error
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split('.')[0] in {'harnest', 'harnest_fused', 'harnest_postgres', 'harnest_redis', 'harnest_threadify'}:
            # Generated agent namespaces (models, tools, ...) exist only inside a project.
            if node.module.startswith(('harnest.models', 'harnest.tools', 'harnest.lib')):
                continue
            loaded = importlib.import_module(node.module)
            for alias in node.names:
                if not hasattr(loaded, alias.name):
                    raise ValueError(f'Example for {where} imports missing name {node.module}.{alias.name}')


BAD_NAMES = set(keyword.kwlist) | set(dir(builtins)) | {'self', 'cls'}


def var_name(class_name: str) -> str:
    """Short instance name from a class name: InMemorySessionStore -> store."""
    words = re.findall(r'[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z0-9]+', class_name) or [class_name]
    name = words[-1].lower()
    if name in BAD_NAMES or not name.isidentifier():
        name = '_'.join(word.lower() for word in words)
    return name + '_value' if name in BAD_NAMES else name


def wrap(code: str, width: int = 88) -> str:
    """Split a long single call onto one argument per line; examples stay readable."""
    lines = []
    for line in code.splitlines():
        match = re.match(r'^(\s*)(.*?\()(.*)(\)[^()]*)$', line)
        if len(line) <= width or not match or not match.group(3):
            lines.append(line)
            continue
        indent, opening, inner, closing = match.groups()
        parts = [part.strip() for part in re.split(r',\s*(?![^\[\]{}()]*[\]})])', inner) if part.strip()]
        lines += [indent + opening, *[f'{indent}    {part},' for part in parts], indent + closing]
    return '\n'.join(lines)


def call_args(value: object) -> str:
    """Required arguments only; `...` marks each value the reader supplies."""
    parts = []
    for param in public_parameters(value):
        if param.kind in {param.VAR_POSITIONAL, param.VAR_KEYWORD} or param.default is not param.empty:
            continue
        parts.append('...' if param.kind == param.POSITIONAL_ONLY else param.name + '=...')
    return ', '.join(parts)


def return_annotation(value: object) -> object:
    try:
        annotation = inspect.signature(value).return_annotation
    except (ValueError, TypeError):
        return inspect.Signature.empty
    return hints(value).get('return', annotation)


def result_name(value: object) -> str | None:
    """Name the returned value after its class, or skip assignment for None."""
    annotation = return_annotation(value)
    if annotation in (inspect.Signature.empty, None, type(None), 'None'):
        return None
    candidates = [annotation, *typing.get_args(annotation)] if typing.get_origin(annotation) in (typing.Union, types.UnionType) else [annotation]
    for candidate in candidates:
        if inspect.isclass(candidate) and candidate is not type(None) and owned_type(candidate):
            return var_name(candidate.__name__)
    return 'result'


def is_async(value: object) -> bool:
    return inspect.iscoroutinefunction(value) or inspect.iscoroutinefunction(getattr(value, '__call__', None))


def context_manager(value: object) -> str | None:
    """Detect @contextmanager/@asynccontextmanager helpers, which are used with `with`."""
    wrapped = getattr(value, '__wrapped__', None)
    if wrapped is not None and inspect.isasyncgenfunction(wrapped):
        return 'async with'
    if wrapped is not None and inspect.isgeneratorfunction(wrapped):
        return 'with'
    text = display(return_annotation(value)) if return_annotation(value) is not inspect.Signature.empty else ''
    if 'AsyncContextManager' in text:
        return 'async with'
    if 'ContextManager' in text:
        return 'with'
    return None


def is_decorator(value: object) -> bool:
    """Decorators return a callable wrapper or accept the decorated function first."""
    annotation = return_annotation(value)
    text = display(annotation) if annotation is not inspect.Signature.empty else ''
    first = next(iter(public_parameters(value)), None)
    takes_function = first is not None and first.default is None and first.name in {'function', 'func', 'fn'}
    return 'Callable[' in text or takes_function


# Modules whose guides import the module and use attribute access: `@lifecycle.resource`.
MODULE_ACCESS = {'harnest.lifecycle': ('from harnest import lifecycle', 'lifecycle')}


def import_target(module: str, name: str) -> tuple[str, str]:
    """Import line and expression for a non-class export, following guide style."""
    if module in MODULE_ACCESS:
        line, prefix = MODULE_ACCESS[module]
        return line, prefix + '.' + name
    return f'from {module} import {name}', name


def handler_params(value: object, param: inspect.Parameter | None) -> str:
    """Name a decorated handler's arguments from a declared Callable[[A, B], R] type."""
    if param is None or param.annotation is param.empty:
        return ''
    annotation = hints(value).get(param.name, param.annotation)
    if isinstance(annotation, str):
        return ''
    if typing.get_origin(annotation) in (typing.Union, types.UnionType):
        annotation = next((a for a in typing.get_args(annotation) if a is not type(None)), annotation)
    args = typing.get_args(annotation)
    if typing.get_origin(annotation) is None or not args or not isinstance(args[0], list):
        return ''
    names = []
    for argument in args[0]:
        name = var_name(argument.__name__) if inspect.isclass(argument) else 'value'
        names.append(name if name not in names else f'{name}_{len(names)}')
    return ', '.join(names)


def use_lines(value: object, target: str) -> list[str]:
    """One use of a callable: a call, a decorator, or a context manager."""
    args = call_args(value)
    if is_decorator(value):
        params = public_parameters(value)
        first = params[0] if params else None
        function_first = first is not None and (first.name in {'function', 'func', 'fn'} or 'Callable' in display(first.annotation))
        # Bare `@decorator` when the decorated function is the only required argument.
        required = [p for p in params[1:] if p.default is p.empty and p.kind not in {p.VAR_POSITIONAL, p.VAR_KEYWORD}]
        if function_first and not required:
            head = '@' + target
        else:
            head = f'@{target}({call_args(value) if not function_first else ", ".join(p.name + "=..." for p in required)})'
        return [head, f'def my_function({handler_params(value, first) if function_first else ""}):', '    ...']
    expr = f'{target}({args})'
    manager = context_manager(value)
    if manager:
        return [f'{manager} {expr}:', '    ...']
    if inspect.isasyncgenfunction(value):
        return [f'async for item in {expr}:', '    ...']
    if is_async(value):
        expr = 'await ' + expr
    name = result_name(value)
    return [f'{name} = {expr}' if name else expr]


def protocol_like(value: type) -> bool:
    return bool(getattr(value, '_is_protocol', False)) or inspect.isabstract(value)


def class_example(value: type, module: str, name: str, constructible: bool) -> list[str]:
    """Import a class and show the one way a caller normally meets it."""
    lines = [f'from {module} import {name}', '']
    if issubclass(value, BaseException):
        return lines + ['try:', '    ...', f'except {name} as error:', '    ...']
    if issubclass(value, enum.Enum):
        member = next(iter(value.__members__), None)
        return lines + ([f'value = {name}.{member}'] if member else [])
    if protocol_like(value):
        return lines + [f'class My{name}({name}):', '    ...']
    if not constructible:
        return lines + [f'{var_name(name)}: {name}  # returned by Harnest, not constructed directly']
    return lines + [f'{var_name(name)} = {name}({call_args(value)})']


class Receiver(typing.NamedTuple):
    """How member examples reach their object: the import and the expression."""

    root: str | None       # exported name to import; None suppresses generated examples
    instance: str | None   # annotated instance variable for class members
    preamble: tuple[str, ...] = ()  # facade access: setup lines replacing the import
    target: str | None = None       # facade access: expression that reaches the object


# How examples reach facades that are not importable (see NESTED_APIS).
FACADES = {
    'SandboxHandle': Receiver(None, None, ('from harnest import context',), 'context.sandboxes["name"]'),
    'ProjectContext.files': Receiver(None, None, ('from harnest.authoring import ProjectContext', '', 'context: ProjectContext'), 'context.files'),
    'ProjectContext.yaml': Receiver(None, None, ('from harnest.authoring import ProjectContext', '', 'context: ProjectContext'), 'context.yaml'),
}


def member_example(member: object, qualified: str, module: str, receiver: Receiver, *, static: bool, prop: bool) -> str:
    """Import the owning export, then use this one member."""
    head, _, attribute = qualified.rpartition('.')
    if receiver.target is not None:
        target = receiver.target
        # A lone import needs a blank line; an annotation line already ends the setup.
        lines = [*receiver.preamble] + ([''] if len(receiver.preamble) == 1 else [])
        if prop:
            return '\n'.join(lines + [f'value = {target}.{attribute}'])
        return '\n'.join(lines + use_lines(member, f'{target}.{attribute}'))
    if receiver.root is None:
        return ''
    if receiver.instance:
        lines = [f'from {module} import {receiver.root}', '']
    else:
        line, prefix = import_target(module, receiver.root)
        lines = [line, '']
        head = prefix + head[len(receiver.root):]
    if receiver.instance and not static:
        target = receiver.instance + head[len(receiver.root):]
        lines += [f'{receiver.instance}: {receiver.root}']
    else:
        target = head
    if prop:
        return '\n'.join(lines + [f'value = {target}.{attribute}'])
    special = {
        '__call__': None,
        '__enter__': [f'with {target}:', '    ...'], '__exit__': [f'with {target}:', '    ...'],
        '__aenter__': [f'async with {target}:', '    ...'], '__aexit__': [f'async with {target}:', '    ...'],
        '__iter__': [f'for item in {target}:', '    ...'], '__aiter__': [f'async for item in {target}:', '    ...'],
    }
    if attribute in special and special[attribute] is not None:
        return '\n'.join(lines + special[attribute])
    call_target = target if attribute == '__call__' else f'{target}.{attribute}'
    return '\n'.join(lines + use_lines(member, call_target))


# Curated details for the page being generated, and the names actually rendered.
PAGE_DETAILS: dict[str, dict] = {}
RENDERED: dict[str, object] = {}


def details_for(qualified: str, value: object, field_docs: dict[str, str] | None = None) -> tuple[dict[str, str], str]:
    """Merge parameter descriptions (curated wins) and pick a curated example."""
    _, sections = parse_doc(value)
    curated = PAGE_DETAILS.get(qualified) or {}
    params = {**(field_docs or {}), **doc_items(sections.get('Args', '')), **(curated.get('params') or {})}
    example = curated.get('example') or (doc_example(sections['Example']) if 'Example' in sections else '')
    RENDERED[qualified] = value
    return params, example.rstrip()


def expandable(value: object | None, qualified: str, example: str, params: dict[str, str]) -> list[str]:
    """Collapsed section holding the parameter table and the example."""
    table = parameter_table(value, params) if value is not None else []
    if not table and not example:
        return []
    if example:
        example = wrap(example)
        check_example(example, qualified)
    title = 'Parameters and example' if table and example else 'Parameters' if table else 'Example'
    body = list(table)
    if example:
        body += ['```python', example, '```', '']
    return [f'<Accordion title="{title}">', '', *body, '</Accordion>', '']


def class_field_docs(value: type, qualified: str) -> dict[str, str]:
    """Field descriptions double as constructor parameter descriptions."""
    _, sections = parse_doc(value)
    docs = doc_items(sections.get('Attributes', ''))
    for name, model_field in getattr(value, 'model_fields', {}).items():
        if getattr(model_field, 'description', None):
            docs.setdefault(name, model_field.description)
    docs.update((PAGE_DETAILS.get(qualified) or {}).get('fields') or {})
    return docs


def load_details(module: str) -> None:
    """Load curated details for one module page."""
    import yaml

    PAGE_DETAILS.clear()
    RENDERED.clear()
    path = DETAILS / (slug(module) + '.yaml')
    if path.exists():
        PAGE_DETAILS.update(yaml.safe_load(path.read_text()) or {})


def validate_details(module: str) -> None:
    """Reject curated entries that no longer match a rendered symbol, parameter, or field."""
    for qualified, entry in PAGE_DETAILS.items():
        entry = entry or {}
        unknown = set(entry) - {'params', 'example', 'fields'}
        if unknown:
            raise ValueError(f'{module}: {qualified} has unknown detail keys {sorted(unknown)}')
        if qualified not in RENDERED:
            raise ValueError(f'{module}: details name {qualified!r} is not a rendered public symbol')
        value = RENDERED[qualified]
        names = {p.name for p in public_parameters(value)}
        for name in entry.get('params') or {}:
            if name not in names:
                raise ValueError(f'{module}: {qualified} documents unknown parameter {name!r}')
        for name in entry.get('fields') or {}:
            if not inspect.isclass(value) or name not in field_names(value):
                raise ValueError(f'{module}: {qualified} documents unknown field {name!r}')


def field_rows(value: type) -> list[tuple[str, str, str]]:
    """List annotated public fields with dataclass defaults where available."""
    annotations = {}
    for base in reversed(value.__mro__):
        # Only Harnest fields belong to this reference; framework internals do not.
        if owned_type(base):
            annotations.update(getattr(base, '__annotations__', {}))
    defaults = {f.name: f for f in dataclasses.fields(value)} if dataclasses.is_dataclass(value) else {}
    model_fields = getattr(value, 'model_fields', {})
    rows = []
    for name, annotation in annotations.items():
        # Private persistence and runtime bindings are deliberately not public fields.
        if name.startswith('_'):
            continue
        default = '—'
        field = defaults.get(name)
        if field is not None:
            # Factories describe per-instance initialization without evaluating provider code.
            if field.default is not dataclasses.MISSING:
                default = repr(field.default) if isinstance(field.default, str) else display(field.default)
            elif field.default_factory is not dataclasses.MISSING:
                default = getattr(field.default_factory, '__name__', 'factory') + '()'
        # Pydantic removes field defaults from class attributes; read its declared field metadata.
        elif name in model_fields:
            model_field = model_fields[name]
            if model_field.default_factory is not None:
                default = getattr(model_field.default_factory, '__name__', 'factory') + '()'
            elif not model_field.is_required():
                default = repr(model_field.default) if isinstance(model_field.default, str) else display(model_field.default)
        else:
            declared = inspect.getattr_static(value, name, dataclasses.MISSING)
            # Descriptors are accessors rather than default field values.
            if declared is not dataclasses.MISSING and not inspect.isdatadescriptor(declared):
                default = repr(declared) if isinstance(declared, str) else display(declared)
        rows.append((name, display(annotation), default))
    return rows


def field_names(value: type) -> set[str]:
    return {name for name, _, _ in field_rows(value)}


def fields(value: type) -> list[str]:
    """Render the original field table: name, type, and declared default."""
    rows = field_rows(value)
    if not rows:
        return []
    lines = ['| `' + name + '` | ' + code_cell(annotation) + ' | ' + code_cell(default) + ' |' for name, annotation, default in rows]
    return ['Fields (`—` means no declared default):', '', '| Field | Type | Default |', '|---|---|---|', *lines, '']


def members(value: object) -> dict[str, object]:
    """Collect inherited Harnest members without running property accessors."""
    cls = value if inspect.isclass(value) else type(value)
    result = {}
    for base in reversed(cls.__mro__):
        # Built-in and dependency methods have their own reference documentation.
        if owned_type(base):
            result.update({k: v for k, v in vars(base).items() if not k.startswith('_') or (inspect.isclass(value) and k in {'__call__', '__enter__', '__exit__', '__aenter__', '__aexit__', '__iter__', '__aiter__'})})
    return result


def member_blocks(value: object, name: str, module: str, receiver: Receiver, depth: int = 0) -> list[str]:
    """Render methods and decorator namespaces without executing managed code."""
    output = []
    for member_name, member in members(value).items():
        qualified = name + '.' + member_name
        # Class-level calls need no instance; remember that before unwrapping.
        static = isinstance(member, (staticmethod, classmethod))
        # Unwrap descriptors for inspection while preserving public call spelling.
        if static:
            member = member.__func__
        if isinstance(member, property):
            doc = description(member.fget)
            output += ['### ' + qualified, '', doc or 'Read-only property.', '']
            _, example = details_for(qualified, member.fget)
            example = example or member_example(member.fget, qualified, module, receiver, static=False, prop=True)
            output += expandable(None, qualified, example, {})
            continue
        if inspect.isfunction(member):
            output += ['### ' + qualified, '', '```python', signature(member, qualified) or qualified, '```', '', description(member), '']
            params, example = details_for(qualified, member)
            example = example or member_example(member, qualified, module, receiver, static=static, prop=False)
            output += expandable(member, qualified, example, params)
            continue
        # Decorator groups contain callable objects instead of ordinary methods.
        if depth < 2 and owned_type(type(member)) and not inspect.isclass(member) and not isinstance(member, enum.Enum):
            output += ['### ' + qualified, '', description(member), '']
            params, example = details_for(qualified, member)
            if callable(member):
                output += ['```python', signature(member, qualified) or qualified, '```', '']
                example = example or member_example(member, qualified + '.__call__', module, receiver, static=False, prop=False)
                output += expandable(member, qualified, example, params)
            output += member_blocks(member, qualified, module, receiver, depth + 1)
    return output


def symbol_blocks(module: str, name: str, value: object) -> list[str]:
    """Emit a public symbol with its signature, fields, methods, and a collapsed example."""
    output = ['## ' + ('cron decorator' if name == 'cron' else name), '']
    if inspect.ismodule(value):
        return output + [f'See [`{value.__name__}`](/harnest/reference/api/{slug(value.__name__)}) for its exports.', '']
    if inspect.isclass(value) or inspect.isroutine(value) or owned_type(type(value)):
        output += [description(value), '']
    private_fields = False
    if callable(value) and typing.get_origin(value) is None:
        sig = signature(value, name)
        # Runtime-returned dataclasses with private constructor fields are not authoring factories.
        private_fields = inspect.isclass(value) and dataclasses.is_dataclass(value) and any(f.name.startswith('_') for f in dataclasses.fields(value)) and module + '.' + name not in CONSTRUCTIBLE
        if private_fields:
            output += ['Obtain this object from the owning Harnest API; its constructor includes runtime bindings.', '']
        elif sig:
            output += ['```python', sig, '```', '']
    if inspect.isclass(value):
        output += fields(value)
        # Enum members are values, not callable methods or dataclass fields.
        if issubclass(value, enum.Enum):
            output += ['| Member | Value |', '|---|---|']
            output += [f'| `{k}` | `{v.value!r}` |' for k, v in value.__members__.items()]
            output += ['']
        # Exceptions, enums, and runtime-owned objects take no authored constructor options.
        constructible = not (private_fields or issubclass(value, (enum.Enum, BaseException)) or protocol_like(value))
        params, example = details_for(name, value, class_field_docs(value, name))
        example = example or '\n'.join(class_example(value, module, name, constructible))
        output += expandable(value if constructible else None, name, example, params)
        output += member_blocks(value, name, module, Receiver(name, var_name(name)))
    elif inspect.isroutine(value) or (callable(value) and owned_type(type(value))):
        params, example = details_for(name, value)
        line, target = import_target(module, name)
        example = example or '\n'.join([line, '', *use_lines(value, target)])
        output += expandable(value, name, example, params)
        if owned_type(type(value)):
            output += member_blocks(value, name, module, Receiver(name, None))
    elif owned_type(type(value)):
        _, example = details_for(name, value)
        line, target = import_target(module, name)
        output += expandable(None, name, example or (line + ('\n\nvalue = ' + target if target != name and not members(value) else '')), {})
        output += member_blocks(value, name, module, Receiver(name, None))
    else:
        _, example = details_for(name, value)
        output += ['```python', name + ' = ' + (repr(value) if isinstance(value, str) else display(value)), '```', '']
        line, target = import_target(module, name)
        output += expandable(None, name, example or (line + ('\n\nvalue = ' + target if target != name else '')), {})
    return output


def load_exports(source: Path) -> dict[str, list[str]]:
    """Use the release snapshot and explicitly scoped compiler entry points."""
    sys.path.insert(0, str(source / 'src'))
    for path in sorted((source / 'packages').glob('*/src')):
        sys.path.insert(0, str(path))
    exports = json.loads((source / 'tests/fixtures/public-api.json').read_text())
    exports.pop('harnest')
    exports.update(EXTRA_EXPORTS)
    # Official extensions normally load into an agent's generated namespace. Load
    # only these trusted bundled definitions; never start their external services.
    for name in ('docker', 'hatchet', 'rag'):
        module = 'harnest.extensions.' + name
        directory = source / 'official-extensions' / name
        spec = importlib.util.spec_from_file_location(
            module, directory / 'extension.py', submodule_search_locations=[str(directory)],
        )
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[module] = loaded
        spec.loader.exec_module(loaded)
        exports[module] = list(loaded.__all__)
    exports['harnest_threadify'] = list(importlib.import_module('harnest_threadify').__all__)
    for module, names in exports.items():
        loaded = importlib.import_module(module)
        # Fail instead of silently publishing an incomplete or outdated module inventory.
        if module not in EXTRA_EXPORTS and set(loaded.__all__) != set(names):
            raise ValueError(f'Public export snapshot differs from source: {module}')
        for name in names:
            value = getattr(loaded, name)
            original = getattr(value, '__module__', '') + '.' + getattr(value, '__qualname__', name)
            PUBLIC_NAMES.setdefault(original, module + '.' + name)
    return exports


def module_page(module: str, names: list[str]) -> str:
    """Combine handwritten contracts with generated API details in one page."""
    loaded = importlib.import_module(module)
    load_details(module)
    lines = ['---', f'title: "{module}"', f'sidebarTitle: "{module}"', 'description: "Public Python signatures, fields, and methods."', 'icon: "code"', '---', '', '{/* Generated by scripts/generate-harnest-reference.py. Edit API notes, api-details, or source docstrings, then regenerate. */}', '', '[All Python modules](/harnest/reference/api/overview) · [Import and compatibility guidance](/harnest/build/python-imports)', '']
    notes = NOTES / (slug(module) + '.md')
    if notes.exists():
        lines += [notes.read_text().strip(), '']
    lines += ['## Exports', '', '| Name | Kind |', '|---|---|']
    for name in names:
        value = getattr(loaded, name)
        kind = 'Module' if inspect.ismodule(value) else 'Class' if inspect.isclass(value) else 'Function' if inspect.isroutine(value) else 'Namespace' if owned_type(type(value)) else 'Value or type alias'
        lines.append(f'| [`{name}`](#{anchor(name)}) | {kind} |')
    lines += ['']
    for name in names:
        lines += symbol_blocks(module, name, getattr(loaded, name))
    for name, (owner, class_name) in NESTED_APIS.get(module, {}).items():
        value = getattr(importlib.import_module(owner), class_name)
        # A named sandbox lookup returns a handle; documenting that type avoids
        # suggesting that execute is a method on the registry itself.
        access = 'context.sandboxes["name"]' if name == 'SandboxHandle' else name
        lines += ['## ' + name, '', 'Access this facade through `' + access + '`; its implementation type is not a public import.', '', description(value), '']
        lines += member_blocks(value, name, module, FACADES.get(name, Receiver(None, None)))
    validate_details(module)
    return '\n'.join(lines).rstrip() + '\n'


def overview(exports: dict[str, list[str]]) -> str:
    """Make every supported public module discoverable from a compact index."""
    lines = ['---', 'title: "Python API reference"', 'sidebarTitle: "Overview"', 'description: "Find Harnest classes, functions, decorators, fields, and methods by public module."', 'icon: "code"', '---', '', 'Use this reference for signatures, defaults, fields, and methods. Start with the [guides](/harnest/overview) for when to use a feature, setup, and operational caveats.', '', 'Import contracts from their public domain modules. Harnest is built and maintained by [Fused](https://usefused.com).', '', '<CardGroup cols={2}>', '  <Card title="Tasks" icon="list-check" href="/harnest/reference/api/task">The task decorator, deferred calls, TaskHandle methods, and storage contracts.</Card>', '  <Card title="Cron" icon="clock" href="/harnest/reference/api/cron">Fixed Cron declarations, dynamic scheduling functions, and CronJob methods.</Card>', '</CardGroup>', '', '## Public modules', '', 'The module pages are generated from the public export snapshot and Python source. They include Harnest-defined inherited methods; methods inherited from third-party libraries belong to those libraries. Async signatures must be awaited. An ellipsis in a default represents an internal sentinel or factory, not a value to pass.', '', '| Module | Exports |', '|---|---|']
    for module, names in sorted(exports.items()):
        lines.append(f'| [`{module}`](/harnest/reference/api/{slug(module)}) | {len(names)} |')
    lines += ['', '`harnest.bundle` and `harnest.orchestrator` list compiler and orchestration entry points separately from the snapshot-tested authoring modules. `harnest_postgres`, `harnest_redis`, `harnest_fused`, and `harnest_threadify` document companion package exports. The `harnest.extensions.*` pages describe official extensions after installation into an agent project.', '', 'See [Python imports and compatibility](/harnest/build/python-imports#public-api-stability) for API stability and editor setup.', '']
    return '\n'.join(lines)


def main() -> None:
    """Refresh only generated pages, or fail a read-only freshness check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    exports = load_exports(args.source.resolve())
    pages = {slug(module) + '.mdx': module_page(module, names) for module, names in sorted(exports.items())}
    pages['overview.mdx'] = overview(exports)
    stale = []
    for name, content in pages.items():
        path = API / name
        if not path.exists() or path.read_text() != content:
            stale.append(name)
            # Check mode must never modify the documentation checkout.
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
    print(f'{len(pages)} API pages; {len(stale)} ' + ('stale' if args.check else 'updated'))
    if args.check and stale:
        raise SystemExit(', '.join(stale))


if __name__ == '__main__':
    main()
