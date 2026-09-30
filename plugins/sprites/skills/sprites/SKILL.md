---
name: sprites
description: Use Sprites to create, list, inspect, operate, and clean up isolated cloud development environments from Codex.
---

# Sprites

Use this skill when the user asks Codex to work with Sprites, sprite environments, remote development environments, cloud sandboxes, or the Sprites MCP server.

Sprites are remote, isolated development environments with their own filesystem, URL, services, checkpoints, and network policy. This skill runs in Codex, outside the sprite. Use the Sprites MCP tools provided by the installed plugin as the control plane.

## Golden Path

For normal Sprites tasks, call the Sprites MCP tools directly. Do not use shell commands, nested `codex exec`, `codex mcp add`, `codex mcp list`, `codex mcp login`, curl, or local config inspection as part of the normal flow.

If Sprites MCP tools are not available in the current tool list, say that the Sprites plugin MCP tools are not loaded in this session and ask the user to restart Codex or reinstall/refresh the plugin. Do not try to work around missing plugin tools by registering another MCP server from the shell.

OAuth is handled by Codex when the Sprites MCP tools are invoked. If Codex prompts for authorization, wait for the user to complete it, then retry the original MCP tool call once. Do not start a second login path from the shell.

Keep user-facing progress concise. Report the result, not MCP registration details, local config checks, or CLI noise.

## Tool Map

Use the smallest direct tool for the request:

- List sprites: `list_sprites`.
- Inspect a mentioned Sprite's identity: `get_sprite_info` with `sprite` and `sprite_id`.
- Open a visual inspection panel: `open_sprite_inspector`, optionally with `sprite`.
- Create a sprite: `create_sprite`, then `list_sprites` only if the user asked to see the updated list.
- Delete a sprite: `destroy_sprite`, only after explicit delete/destroy/remove intent.
- Run a one-off command in a sprite: `exec`. Inspect or stop exec sessions with `exec_list` and `exec_kill`.
- Inspect services: `service_list` and `service_get`.
- Manage services: `service_create`, `service_start`, `service_stop`.
- Inspect service logs: `service_logs`.
- Manage checkpoints: `checkpoint_create`, `checkpoint_list`, `checkpoint_get`, `checkpoint_restore`.
- Inspect or change network policy: `policy_network_get`, `policy_network_update`.

Sprite-scoped tools usually require a `sprite` argument. If the user did not name a sprite and the task needs one, call `list_sprites` and choose the obvious match; ask a short clarification only when there is no clear choice.

## Composer Mentions and Inspector

On supported desktop clients, users can select individual Sprites from the composer. A Sprite reference uses `sprites://org/<org_id>/<encoded-name>?id=<sprite_id>` and identifies an environment in a particular organization. The Inspector can also attach a selected Sprite's name, ID, and organization to the conversation.

Use that explicit selection as the target. Verify it with `get_sprite_info`, passing the decoded name as `sprite` and the reference's ID as `sprite_id`, and check that the returned organization matches the reference. Pass `sprite_id` alongside `sprite` to subsequent sprite-scoped tools that advertise it. If access fails or the identity has changed, report that the reference is stale or unavailable; do not substitute a similarly named environment. When multiple selections leave the target ambiguous, ask which one the user means. A selection supplies context, not permission to delete or restore an environment.

When the user asks for a visual overview, open `open_sprite_inspector`. It lists environments and provides explicit reads for services, checkpoints, and the last 100 service-log lines. Runtime reads may wake the selected Sprite. The Inspector has no mutation controls; use the existing tools for requested changes. Its current selection is contextual and may be removed from the composer.

These extensions require support from both the host and the hosted MCP server. If only the extension tools or UI are unavailable, continue using the existing list and inspection tools and summarize their results in chat. Do not attempt to register a second server. Composer search is host-driven; `search_sprite_mentions` is an app-only tool.

## Common Flows

List sprites:

1. Call `list_sprites`.
2. If the list is empty, say no sprites were found for the authenticated organization.
3. If sprites exist, summarize name, status, URL, and any useful identifiers. Do not dump raw JSON unless asked.

Create a sprite:

1. Call `create_sprite` with a descriptive task-scoped name.
2. Report the created sprite name, id, status, and URL.
3. If the user asked to list after creation, call `list_sprites` and summarize the updated list.

Inspect or operate a sprite:

1. Identify the target sprite.
2. Use `service_list`, `service_logs`, or targeted `exec` based on the task.
3. Prefer MCP service tools for service inspection and lifecycle work.
4. Use services for long-running processes and `exec` for short commands.

## Codex vs Sprite Context

Keep these contexts distinct:

- Codex local workspace: the repository and shell where this conversation is running.
- Sprites MCP server: the API Codex uses to operate sprites.
- Sprite filesystem: the remote environment reached only through sprite-scoped tools.

Do not assume Codex's local shell is inside a sprite. To inspect or change a sprite, use Sprites MCP tools.

If sprite-specific guidance files exist, read them remotely with `exec` only when relevant. Common examples include repository guidance files or project docs inside the sprite.

## Safety

Treat any HTTP service in a sprite as potentially internet-accessible. Sprite URLs can be switched from authenticated access to public access.

Never create HTTP endpoints that expose:

- Environment variables, secrets, tokens, credentials, or API keys.
- Arbitrary file contents without explicit user approval and access controls.
- Debug, admin, status, or process endpoints that dump internals.
- Unfiltered logs, stack traces, system paths, or user data.

Destroying a sprite is irreversible. It deletes the environment state, services, checkpoints, and URL. Only call `destroy_sprite` when the user explicitly asks to delete, destroy, or remove a sprite, or when they approve cleanup.

For risky filesystem changes, package installs, migrations, or broad refactors inside a sprite, create a checkpoint first and mention the checkpoint id.

If network access fails, use `policy_network_get` first. Update network policy only when the user has asked to allow or block domains, or when the required access is clearly part of the requested work and you can explain it.
