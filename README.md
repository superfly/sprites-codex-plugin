# Sprites

Use Sprites from Codex to create, inspect, and operate remote development environments.

Sprites are isolated cloud environments with their own filesystem, URL, services, checkpoints, and network policy. This plugin connects Codex to the Sprites MCP server so Codex can manage those remote environments without treating your local shell as the sprite runtime.

## What You Can Do

With this plugin enabled, you can ask Codex to:

- List your active sprites.
- Create a fresh remote environment for a task.
- Inspect a sprite's files, services, logs, checkpoints, and network policy.
- Run commands, tests, builds, and diagnostics inside a selected sprite.
- Start long-running services such as dev servers, background workers, and databases.
- Create checkpoints before risky changes.
- Clean up services or destroy sprites when you explicitly ask for that.

## Requirements

- Codex with plugin support.
- Access to Sprites for your organization.
- Permission to authenticate Codex with the Sprites MCP server.

## Installation

Install the `Sprites` plugin from the Codex plugin marketplace.

For local installation from this repository:

```sh
codex plugin marketplace add .
```

Then restart Codex, open the plugin directory, choose the `Sprites` marketplace, and install `Sprites`.

## Authentication

The plugin uses the Sprites MCP server at:

```text
https://sprites.dev/mcp
```

When Codex needs access, it may prompt you to authenticate. You can also start the login flow from the CLI:

```sh
codex mcp login sprites
```

## Example Prompts

- "Use Sprites to list my active development environments."
- "Use Sprites to create a new remote environment for this repo and run the tests."
- "Use Sprites to inspect services and logs for a selected sprite."
- "Create a checkpoint in my `api-debug` sprite, then run the failing test."
- "Start the web service in my sprite and give me the URL."

## How Codex Uses Sprites

Codex runs outside the sprite. The plugin teaches Codex to use Sprites MCP tools as the control plane for remote work.

That means:

- Your local Codex workspace is separate from a sprite's filesystem.
- Commands that should run in a sprite are run through sprite-scoped MCP tools.
- Long-running processes should usually be managed as sprite services.
- Checkpoints are available for reversible remote filesystem changes.
- Network access is controlled by the sprite's network policy.

Codex will normally list sprites first, reuse an existing sprite when it clearly matches your task, and create a new sprite when you ask for one or when no suitable sprite exists.

## Safety Notes

Treat any HTTP service in a sprite as potentially internet-accessible. Do not expose secrets, environment variables, tokens, arbitrary file contents, debug endpoints, or unfiltered logs through a sprite URL.

Destroying a sprite is irreversible. It deletes the writable filesystem overlay, services, checkpoints, and URL. Codex should only destroy a sprite when you explicitly ask it to delete, destroy, or remove that sprite.

## Troubleshooting

If Codex cannot see Sprites tools, confirm that the plugin is installed and restart Codex.

If authentication fails, rerun:

```sh
codex mcp login sprites
```

If a command inside a sprite cannot reach the network, ask Codex to inspect the sprite network policy before changing it.

If a web service is not reachable, ask Codex to inspect the sprite's services, logs, and configured HTTP port.
