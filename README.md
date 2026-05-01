# Sprites Codex Plugin

This repository contains the Codex plugin for Sprites. It bundles:

- A Codex plugin manifest at `.codex-plugin/plugin.json`.
- A Sprites MCP server configuration in `.mcp.json`.
- A first-pass Sprites skill in `skills/sprites/SKILL.md`.
- A local marketplace file for testing in `.agents/plugins/marketplace.json`.

The plugin is intentionally small. The Sprites API owns the `/mcp` endpoint, OAuth, token restrictions, tool schemas, and runtime behavior. This repo owns Codex packaging and agent workflow guidance for Codex operating Sprites remotely through MCP.

## Framing

Codex runs outside a sprite. This plugin should consistently describe Sprites as remote environments managed through the Sprites MCP server, not as the local shell where Codex is running.

When the skill needs to inspect or change a sprite, it should tell Codex to use sprite-scoped MCP tools such as `exec`, `service_list`, `logs`, checkpoints, and network policy tools. Local plugin development in this repository is separate from remote sprite operation.

## Local Development

From this repo, add the local marketplace to Codex:

```sh
codex plugin marketplace add .
```

Restart Codex, open the plugin directory, choose the `Sprites Codex Plugin` marketplace, and install `Sprites`.

If the MCP server needs OAuth login from the CLI:

```sh
codex mcp login sprites
```

## Plugin Layout

```text
.
├── .agents/plugins/marketplace.json
├── .codex-plugin/plugin.json
├── .mcp.json
├── assets/
└── skills/sprites/SKILL.md
```

## Iterating On The Skill

Most iteration should happen in `skills/sprites/SKILL.md`.

Good changes to make there:

- Tighten rules for when to create versus reuse a sprite.
- Add preferred naming conventions.
- Add task-specific workflows for remote web apps, test runs, and long-running services.
- Refine safety rules around public URLs, secrets, checkpoints, and destructive actions.
- Add known troubleshooting paths as Sprites MCP tools evolve.

After changing the plugin, restart Codex so the local marketplace install picks up the updated files.

## MCP Server

The bundled MCP config points at:

```text
https://sprites.dev/mcp
```

The server advertises OAuth metadata and supports `sprites:read` and `sprites:write` scopes. The Sprites API currently exposes management tools such as `list_sprites`, `create_sprite`, and `destroy_sprite`, plus sprite-scoped tools generated from the `sprite-env` schema. Those tools let Codex operate a remote sprite without treating Codex's local shell as the sprite runtime.

For local Sprites API testing, use a tunnel as documented in `sprites-api/docs/local_development.md`, then temporarily change `.mcp.json` to the tunnel URL.

## Release Notes

Initial version: `0.1.0`.
