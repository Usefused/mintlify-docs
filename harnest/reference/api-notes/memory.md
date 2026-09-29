

## Retention and limits

| Setting | Behavior |
| --- | --- |
| `expires_at` | Optional future UTC epoch timestamp. Expired records disappear from reads; purge them for physical cleanup. |
| Session lifetime | Deleting a session or expiring a checkpoint does not delete memories. |
| Record metadata | Creation/update times, revision, and source session/invocation/agent; updates replace content and metadata, not append history. |
| Size limits | Key: 256 UTF-8 bytes. Content: 64 KiB. Metadata and provenance: 16 KiB combined. |
| Page size | 1–100 records. |

## Storage maintenance

| Provider method | Scope and result |
| --- | --- |
| `delete_all(scope)` | Physically remove live and expired records in one namespace; return the removed count |
| `delete_user(application_id, user_id)` | Remove that application's user across every namespace; return the removed count |
| `purge_expired(scope, limit=100, after=None)` | Inspect a bounded page and return `MemoryCleanupPage(deleted, next_cursor)` |
