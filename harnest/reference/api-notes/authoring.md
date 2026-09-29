

## Pack configuration

| Property | Required | Contract |
|---|---|---|
| `name` | Yes | A unique kebab-case identifier beginning with a letter, up to 63 characters. `harnest` is reserved. |
| `schema_version` | Yes | A positive integer identifying the company configuration schema. Track it separately from your package release version. |
| `options` | No | A Pydantic model for caller-supplied inputs. |
| `templates` | No | A directory containing inert UTF-8 [templates](/harnest/build/project-packs/changes#templates). |
| `config_file` | With `config_model` | The project-relative company configuration path. |
| `config_model` | With `config_file` | A Pydantic model that validates the resulting configuration mapping. |

## File operations

| Method | Result |
|---|---|
| `context.files.read_text(path)` | Read an existing staged UTF-8 file. Missing files raise `ProjectError`. |
| `context.files.write_text(path, content, policy=...)` | Propose file creation or a managed replacement. |
| `context.files.from_template(path, template=..., values=..., policy=...)` | Read an inert UTF-8 template and propose its rendered content. |
| `context.files.from_file(path, source=..., policy=...)` | Copy a packaged file unchanged, including binary documents and assets. |
| `context.files.delete(path)` | Remove an unchanged file owned by the pack. An absent file is a no-op. |

## YAML operations

| Method | Result |
|---|---|
| `context.yaml.read(path)` | Return a detached mapping from staged YAML; return `{}` for an absent file. |
| `context.yaml.set(path, key=(...), value=..., policy=...)` | Set a JSON-compatible value while retaining unrelated keys. |
| `context.yaml.rename_key(path, source=(...), destination=(...))` | Move the current value to an unoccupied destination. |

## Initializer contract

```python
@pack.initialize
def initialize(context: ProjectContext) -> ChangePlan:
    ...
```

| Rule | Behavior |
|---|---|
| Registration | One initializer per pack. Registering another raises `ProjectError`. |
| Function | A synchronous callable accepting one `ProjectContext` and returning `ChangePlan`. |
| Timing | Runs during init planning, including `--dry-run`. It does not write to the live project. |
| Version | New projects start at the installed pack's current `schema_version`. |
| Upgrades | Never runs during upgrade. Use [`@pack.migration`](/harnest/build/project-packs/migrations). |
| Optional hook | A pack can omit its initializer. Any declared configuration model must still validate. |

## Hook context

| Member | What it provides |
|---|---|
| `context.name` | The requested project directory's final path component. |
| `context.options` | Validated Pydantic options, or `None` if the pack declares none. |
| `context.files` | Read staged UTF-8 files and propose file/template operations. |
| `context.yaml` | Read staged mappings and propose field changes. |

## Migration contract

```python
@pack.migration(from_version=1, to_version=2)
def migrate(context: ProjectContext) -> ChangePlan:
    ...
```

| Parameter or rule | Contract |
|---|---|
| `from_version` | A positive integer schema version. |
| `to_version` | Exactly `from_version + 1`, no greater than `pack.schema_version`. |
| Function | A synchronous callable accepting `ProjectContext` and returning `ChangePlan`. |
| Registration | One migration per source version. Duplicate registrations are rejected. |
| Timing | Runs during upgrade planning, including previews. |
| New projects | Skip historical migrations; their initializer must create the current schema directly. |

## Plan results

| Plan member | Purpose |
|---|---|
| `root` | The resolved target directory. |
| `changes` | Net file changes: `ChangeKind.CREATE`, `UPDATE`, or `DELETE`, with paths and owners. |
| `blockers` | Problems that prevent the entire plan from applying. |
| `render()` | A readable combined summary. |
| `public()` | A JSON-compatible summary without file contents or option values. |
