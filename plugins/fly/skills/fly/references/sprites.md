# Sprites through Fly

Use Sprite tools from the Fly connection. Its Sprites binding can restrict names
by prefix or label and limit creation. `list_sprites` returns only the visible
subset, not necessarily all Sprites in an organization or only those this client
created. Before `create_sprite`, call `get_fly_context` and inspect `name_prefix`
and `max_sprites_total`. Prefer an existing environment that clearly matches
the task; a name restriction or quota is not a reason to delete other Sprites.

## Identity and visual inspection

Use `get_sprite_info` for metadata without waking a Sprite. A composer reference
has the form `sprites://org/<org_id>/<encoded-name>?id=<sprite_id>`. Decode its
name, pass it as `sprite` together with `sprite_id`, and verify the returned
organization. Pass the ID to subsequent tools when their schemas support it.
If the reference is stale, deleted, recreated, or inaccessible, report that
instead of substituting a matching name. A selection identifies a target; it
does not authorize deletion or checkpoint restoration.

Use `open_sprite_inspector` when the user wants a visual overview. Opening it
lists metadata; explicit runtime reads can wake a Sprite. The Inspector is
read-only. `search_sprite_mentions` is host-driven composer search, with up to
20 authorized prefix matches; use `list_sprites` for normal discovery. If the
host lacks UI or mention support, continue with direct inspection tools.

## Files and commands

Use `file_list`, `file_read`, `file_write`, `file_copy`, `file_rename`, and
`file_delete` for filesystem operations. Inspect the current tool schemas for
content encoding and arguments; the HTTP description of raw bytes is not an
MCP argument schema. File writes support up to 16 MiB. Resolve paths in the
Sprite, not in the local workspace, and check targets before overwriting or
deleting work.

Use `exec` for non-interactive commands, tests, and builds. `exec_list` inspects
active sessions and `exec_kill` stops the selected session. The local Codex
shell is not inside the Sprite. Read remote repository instructions when
working in that repository, and use service tools for long-running processes.

## Services, checkpoints, and network

| Task | Tools | Behavior that affects the choice |
| --- | --- | --- |
| Inspect services and logs | `service_list`, `service_get`, `service_logs` | Runtime reads may wake the Sprite; summarize relevant logs without exposing secrets. |
| Manage services | `service_create`, `service_start`, `service_stop` | Creating can update an existing definition. Streaming progress alone does not prove the service is healthy. |
| Protect and inspect state | `checkpoint_create`, `checkpoint_list`, `checkpoint_get` | Create a checkpoint before risky filesystem changes, package installs, migrations, or broad refactors; verify completion. |
| Restore state | `checkpoint_restore` | Can discard current work. Require authorization for the selected restoration and verify completion. |
| Diagnose network access | `policy_network_get` | Inspect policy before changing it. |
| Change network access | `policy_network_update` | Change only the access needed for the user's request; preserve unrelated rules. |

After a timed-out mutation, inspect its result before repeating it. Report
streaming operations as in progress until completion is observed.

## Removal and exposure

`destroy_sprite` is irreversible and removes the environment state, services,
checkpoints, and URL. Use it only for explicit deletion or approved cleanup of
that Sprite. Neither creation limits nor a troubleshooting request authorize it.

Sprite HTTP URLs can become public. Do not create endpoints exposing secrets,
environment variables, arbitrary filesystem contents, or unfiltered logs.
Respect the intended access controls when publishing a service URL.
