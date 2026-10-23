> ## Documentation Index
> Fetch the complete documentation index at: https://usefused.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Update or roll back an app

> Deploy a code change or switch traffic to a previous version.

## Deploy a change

Edit your TypeScript, then increase `version` in the existing YAML file:

```yaml theme={null}
name: customer-app
version: "1.0.1"
```

```bash theme={null}
fused-cli app plan -f .fused/unified_app/customer-app.yaml
fused-cli app apply -f .fused/unified_app/customer-app.yaml
```

Each published version is fixed. Reusing a version number with changed code returns `app_version_immutable`. Use a new number for each change.

Direct REST callers keep the same app family URL and token. SDK and MCP apps that select an exact version need a [matching update](/docs/app/unified-apps/use-from-apps).

## Roll back

Choose a previously deployed version by app name:

```bash theme={null}
fused-cli app promote customer-app --version 1.0.0
```

New requests go to that version. Your REST URL and token stay the same. Promotion does not rebuild the app or edit your local files.

You can also read the app name from your config:

```bash theme={null}
fused-cli app promote -f .fused/unified_app/customer-app.yaml --version 1.0.0
```

Always pass the destination in `--version`. The config's `version` field does not choose the promotion target.

<Accordion title="Permissions and version behavior">
  * Promotion requires `app.unified_app.read` and `app.unified_app.manage`.
  * The target must still have a runnable bundle. Deleted versions cannot be promoted.
  * An explicit app name takes precedence over the config. Without a name or `-f`, discovery must find exactly one Unified App config.
  * Historical results remain readable through the app family URL and their read handles. Rerun and replay require the original version to be receiving traffic.
  * Unified App REST URLs use the family ID, not an individual version ID. The hosted MCP family URL follows traffic changes; sessions on the old version must reconnect.
  * If another deployment changes traffic concurrently, inspect the current target before retrying.
</Accordion>


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.