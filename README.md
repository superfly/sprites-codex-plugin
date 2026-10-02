# Sprites

Use Sprites from Codex to create, inspect, and operate remote development environments.

Sprites are isolated cloud environments with their own filesystem, URL, services, checkpoints, and network policy. This plugin connects Codex to the Sprites MCP server so Codex can manage those remote environments without treating your local shell as the sprite runtime.

## What You Can Do

With this plugin enabled, you can ask Codex to:

- List your active sprites.
- Create a fresh remote environment for a task.
- Inspect a sprite's files, services, logs, checkpoints, and network policy.
- Select a specific Sprite in the desktop composer and inspect it beside the conversation.
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

When Codex needs access, it will prompt you to authenticate through the plugin flow.

## Usage Attribution

The plugin attributes its hosted MCP requests to Codex using the coarse,
privacy-safe [`client-signals`](https://github.com/superfly/client-signals)
headers. It sends two fixed values on every request to `https://sprites.dev/mcp`:

```text
Fly-Client-Agent: codex
Fly-Client-Interactive: false
```

`Fly-Client-Agent` is the attribution marker. `Fly-Client-Interactive` is the
instrumentation sentinel that `client-signals` requires before it will read the
marker at all; a static plugin configuration cannot observe whether a given
Codex session is attached to a terminal, so it sends a constant rather than a
measurement. Requests classify as agent traffic on the strength of the marker,
not this value.

Both values are fixed in the plugin's MCP configuration. Nothing user-,
machine-, or repo-specific is sent, and the attribution is advisory analytics
only — it is never used for access control, gating, or rate-limiting.

## Example Prompts

- "Use Sprites to list my active development environments."
- "Use Sprites to create a new remote environment for this repo and run the tests."
- "Use Sprites to inspect services and logs for a selected sprite."
- "Create a checkpoint in my `api-debug` sprite, then run the failing test."
- "Start the web service in my sprite and give me the URL."
- "Open the Sprite Inspector for `api-debug`."

## Composer Mentions and Sprite Inspector

With the matching MCP server update deployed, supported desktop clients can search
for individual Sprites in the composer. Search uses a name prefix and shows up to
20 environments accessible to the authenticated organization and token. Selecting
a result adds a reference containing the Sprite's organization, name, and ID.
Codex verifies that identity before using the environment.

The **Sprite Inspector** opens beside the conversation. Ask Codex to open it, or
use its conversation-panel entrypoint where the host supports one. You can browse
and filter environments, load more results, attach a selected Sprite to chat,
inspect services and checkpoints, and read the last 100 lines of a service's logs.
Opening the panel lists metadata; loading runtime details or logs may wake a
sleeping Sprite. The panel is read-only and refreshes on request.

The hosted MCP server supplies the UI and extension metadata. No extra local
server or credentials are needed. Existing text-based tools remain available on
clients without extension support. After the server update is deployed, refresh
the plugin connection or restart Codex to discover the new tools.

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

Destroying a sprite is irreversible. It deletes the environment state, services, checkpoints, and URL. Codex should only destroy a sprite when you explicitly ask it to delete, destroy, or remove that sprite.

## Troubleshooting

If Codex cannot see Sprites tools, confirm that the plugin is installed and restart Codex.

Codex should not ask you to manually run `codex mcp add sprites --url https://sprites.dev/mcp` during normal Sprites use. If it does, restart Codex or reinstall/refresh the plugin so the plugin-provided MCP server is loaded.

If authentication fails during plugin install or first use, retry the plugin authorization flow from Codex. Avoid starting a separate CLI login unless you are deliberately debugging a manually registered MCP server.

If a command inside a sprite cannot reach the network, ask Codex to inspect the sprite network policy before changing it.

If a web service is not reachable, ask Codex to inspect the sprite's services, logs, and configured HTTP port.

## Packaging a Directory Update

Run `python3 scripts/package_plugin.py` to build and validate the upload ZIP.
See [directory release packaging](release/README.md) for the published-version
baseline, upload-specific settings, and remaining portal checks.
