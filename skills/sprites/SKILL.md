---
name: sprites
description: Use Sprites to create, inspect, operate, and clean up isolated cloud development environments from Codex.
---

# Sprites

Use this skill when the user asks Codex to work with Sprites, sprite environments, remote development environments, cloud sandboxes, or the Sprites MCP server.

Sprites are remote, isolated development environments with their own filesystem, URL, services, checkpoints, and network policy. This skill runs in Codex, outside the sprite. Treat the Sprites MCP server as the primary control plane for creating, inspecting, and operating those environments.

Do not assume Codex's local shell is inside a sprite. Local files, local git state, local services, and local network behavior are separate from a sprite unless the user is explicitly asking about the local plugin/repo. To inspect or change a sprite, use Sprites MCP tools.

## Tooling

Prefer the bundled Sprites MCP server when it is available.

The top-level Sprites MCP server exposes management tools such as:

- `list_sprites`: list existing sprites in the authenticated organization.
- `create_sprite`: create a new sprite.
- `destroy_sprite`: permanently delete a sprite.

Sprite-scoped tools are proxied into a specific sprite and usually require a `sprite` argument. Common tools include:

- `exec`: run a command inside the sprite.
- `service_list`, `service_get`, `service_create`, `service_start`, `service_stop`, `service_restart`, `service_delete`, `service_signal`: manage long-running services.
- `logs`: inspect environment or service logs.
- `checkpoint_create`, `checkpoint_list`, `checkpoint_get`, `checkpoint_restore`, `checkpoint_delete`: manage filesystem checkpoints.
- `policy_network_get`, `policy_network_update`: inspect or update network policy.
- `capabilities`: inspect available sprite-scoped tools and environment guidance.

If the MCP server is not authenticated, guide the user through the Sprites OAuth flow or API-token setup. Codex MCP OAuth can normally be started with `codex mcp login sprites`.

## Workflow

1. Start by listing sprites unless the user gave a specific sprite name or explicitly asked to create one.
2. Reuse an existing sprite when it clearly matches the task. Create a new sprite when the user asks for a fresh environment or no suitable sprite exists.
3. Use descriptive, task-scoped sprite names. Prefer names that include the repo or task, such as `repo-feature-test`.
4. After creating or selecting a sprite, inspect it through MCP. Start with `capabilities`, `service_list`, or a lightweight `exec` command such as `pwd` or `ls`.
5. For risky filesystem changes, package installs, migrations, or broad refactors, create a checkpoint first and mention the checkpoint id.
6. Use services for long-running processes such as dev servers, databases, and workers. Services persist across reboots, restart on crash, and can expose one HTTP port through the sprite URL.
7. Use sprite-scoped `exec` for one-off remote commands. Active sessions can keep sprites alive; clean up or stop sessions and services when they are no longer needed.
8. When reporting results, include the sprite name, organization if known, important URLs, running services, and any checkpoint ids.

## Codex vs Sprite Context

Keep these contexts distinct:

- Codex local workspace: the repository and shell where this conversation is running.
- Sprites MCP server: the API Codex uses to create and operate sprites.
- Sprite filesystem: the remote environment reached only through sprite-scoped tools.

When a task involves code that should run in a sprite, first verify whether the repository already exists there. If it does not, clone it, copy it, or follow the user's requested setup path by running `exec` in that sprite.

If sprite-specific guidance files exist, read them remotely with `exec` only when they are relevant. Examples include `/.sprite/llm.txt`, `llm-dev.txt`, repository `AGENTS.md`, or project docs inside the sprite. Do not try to read `/.sprite/...` from Codex's local filesystem.

## Safety

Treat any HTTP service in a sprite as potentially internet-accessible. Sprite URLs can be switched from authenticated access to public access.

Never create HTTP endpoints that expose:

- Environment variables, secrets, tokens, credentials, or API keys.
- Arbitrary file contents without explicit user approval and access controls.
- Debug, admin, status, or process endpoints that dump internals.
- Unfiltered logs, stack traces, system paths, or user data.

When building web services in a sprite:

- Return the minimum data needed for the task.
- Validate and sanitize inputs.
- Use app-level authentication for sensitive routes.
- Avoid printing secrets in command output, logs, HTTP responses, or tool results.

Destroying a sprite is irreversible. It deletes the writable filesystem overlay, services, checkpoints, and URL. Only call `destroy_sprite` when the user explicitly asks to delete/destroy/remove a sprite, or when they have approved cleanup. Prefer creating a checkpoint before destructive in-sprite changes.

Network policy is enforced through DNS-based rules. If network access fails, use `policy_network_get` first. Update network policy only when the user has asked to allow or block domains for the task, or when the required access is clearly part of the requested work and you can explain it.

## Remote Operations

Use MCP service tools before falling back to running `sprite-env` commands through `exec`. The MCP tools give Codex structured inputs and outputs, which are easier to inspect and safer to automate.

Use `exec` for commands that must run in the sprite, such as:

- Inspecting the remote filesystem or repository.
- Installing dependencies.
- Running builds, tests, linters, migrations, or package managers.
- Reading in-sprite guidance files.
- Running short diagnostic commands.

Prefer services for long-running processes. If no service owns an HTTP port, the sprite URL proxy routes to port `8080` by default. When exposing a dev server, create or update a service with the correct HTTP port and report the resulting URL.

## Common Patterns

Create and validate a development environment:

1. `list_sprites`
2. `create_sprite` if needed.
3. Use `capabilities` and `exec` to inspect the remote repo/runtime.
4. Create a checkpoint before installing dependencies or making broad changes.
5. Run tests or build commands.
6. Use `service_create` for a dev server and expose the expected HTTP port.
7. Report the URL, service status, and test results.

Investigate a failing sprite:

1. `list_sprites` and identify the target.
2. Use `service_list`, `logs`, and targeted `exec` commands.
3. Check network policy if dependency downloads or API calls fail.
4. Prefer small, reversible fixes and checkpoint before risky repair work.

Clean up:

1. Stop or delete services the user no longer needs.
2. Close or stop stray exec sessions when appropriate.
3. Destroy sprites only after explicit user intent is clear.
