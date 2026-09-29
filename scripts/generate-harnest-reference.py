"""Refresh public Python API pages from a trusted Harnest source checkout.

Run with Harnest's development Python environment (including bundled packages):
  /path/to/Harnest/.venv/bin/python scripts/generate-harnest-reference.py /path/to/Harnest
Use --check to detect stale pages without writing them. Handwritten usage notes
live in harnest/reference/api-notes/<module>.md and survive regeneration.
"""
from __future__ import annotations

import argparse
import dataclasses
import enum
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import re
import sys
import types
import typing

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / 'harnest/reference/api'
NOTES = ROOT / 'harnest/reference/api-notes'
EXTRA_EXPORTS = {
    'harnest.bundle': ['BundleError', 'BundleConventionError', 'BundleImportError',
        'BundleExportError', 'BundleDuplicateError', 'BundleSkillError', 'BundleEvalError',
        'EvalSuite', 'compile_agent', 'compile_app', 'compile_application',
        'compile_artifact', 'bundle_agent', 'discover_evals'],
    'harnest.orchestrator': ['AgentSource', 'Orchestrator', 'define_orchestrator'],
}
PUBLIC_NAMES: dict[str, str] = {}
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


def description(value: object) -> str:
    """Avoid inherited built-in help masquerading as Harnest documentation."""
    return prose(inspect.cleandoc(getattr(value, '__doc__', '') or ''))


def fields(value: type) -> list[str]:
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
        rows.append('| `' + name + '` | `' + display(annotation).replace('|', r'\|') + '` | `' + default.replace('|', r'\|') + '` |')
    if not rows:
        return []
    return ['Fields (`—` means no declared default):', '', '| Field | Type | Default |', '|---|---|---|', *rows, '']


def members(value: object) -> dict[str, object]:
    """Collect inherited Harnest members without running property accessors."""
    cls = value if inspect.isclass(value) else type(value)
    result = {}
    for base in reversed(cls.__mro__):
        # Built-in and dependency methods have their own reference documentation.
        if owned_type(base):
            result.update({k: v for k, v in vars(base).items() if not k.startswith('_') or (inspect.isclass(value) and k in {'__call__', '__enter__', '__exit__', '__aenter__', '__aexit__', '__iter__', '__aiter__'})})
    return result


def member_blocks(value: object, name: str, depth: int = 0) -> list[str]:
    """Render methods and decorator namespaces without executing managed code."""
    output = []
    for member_name, member in members(value).items():
        qualified = name + '.' + member_name
        # Unwrap descriptors for inspection while preserving public call spelling.
        if isinstance(member, (staticmethod, classmethod)):
            member = member.__func__
        if isinstance(member, property):
            doc = description(member.fget)
            output += ['### ' + qualified, '', doc or 'Read-only property.', '']
            continue
        if inspect.isfunction(member):
            output += ['### ' + qualified, '', '```python', signature(member, qualified) or qualified, '```', '', description(member), '']
            continue
        # Decorator groups contain callable objects instead of ordinary methods.
        if depth < 2 and owned_type(type(member)) and not inspect.isclass(member) and not isinstance(member, enum.Enum):
            output += ['### ' + qualified, '', description(member), '']
            if callable(member):
                output += ['```python', signature(member, qualified) or qualified, '```', '']
            output += member_blocks(member, qualified, depth + 1)
    return output


def symbol_blocks(module: str, name: str, value: object) -> list[str]:
    """Emit a public symbol with signatures, fields, and supported methods."""
    output = ['## ' + ('cron decorator' if name == 'cron' else name), '']
    if inspect.ismodule(value):
        return output + [f'See [`{value.__name__}`](/harnest/reference/api/{slug(value.__name__)}) for its exports.', '']
    if inspect.isclass(value) or inspect.isroutine(value) or owned_type(type(value)):
        output += [description(value), '']
    if callable(value) and typing.get_origin(value) is None:
        sig = signature(value, name)
        # Runtime-returned dataclasses with private constructor fields are not authoring factories.
        private_fields = inspect.isclass(value) and dataclasses.is_dataclass(value) and any(f.name.startswith('_') for f in dataclasses.fields(value))
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
        output += member_blocks(value, name)
    elif owned_type(type(value)):
        output += member_blocks(value, name)
    elif not inspect.isroutine(value):
        output += ['```python', name + ' = ' + (repr(value) if isinstance(value, str) else display(value)), '```', '']
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
    lines = ['---', f'title: "{module}"', f'sidebarTitle: "{module}"', 'description: "Public Python signatures, fields, and methods."', 'icon: "code"', '---', '', '{/* Generated by scripts/generate-harnest-reference.py. Edit API notes or source docstrings, then regenerate. */}', '', '[All Python modules](/harnest/reference/api/overview) · [Import and compatibility guidance](/harnest/build/python-imports)', '']
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
        lines += member_blocks(value, name)
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
