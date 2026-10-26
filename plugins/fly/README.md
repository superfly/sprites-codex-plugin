# Fly

Use Fly MCP from Codex to operate authorized Fly.io resources and Sprites.
The plugin connects to `https://mcp.fly.io` using browser OAuth, with no pasted
API tokens or custom authorization headers.

## Install

Follow the [repository installation instructions](../../README.md) and choose
**Fly** in the **Fly.io** marketplace. Both portable `plugin.json` / `mcp.json`
and Codex compatibility manifests are included for source installations.

During authorization, select the organizations, apps, and Sprites permissions
you need. The connection's scopes and resource restrictions determine what
calls are permitted. Installing the plugin does not grant access to all of Fly.

## What it supports

- Inspect authorized organizations, resource bindings, and launch blockers.
- Inspect existing apps; operate Machines, leases, memory, and metadata.
- Manage volumes and snapshots, and set or remove app secrets.
- Inspect IP assignments and TLS certificates.
- Create and operate Sprites: files, commands, services, checkpoints, and
  network policies, plus composer mentions and the read-only Sprite Inspector
  in supported hosts.

App creation, deployment workflows, product provisioning, and organization
administration are outside the current MCP tool set. Network addresses and
certificates are read-only. Machine and volume creation can incur charges;
deleting resources and restoring Sprite checkpoints can discard data.

The [Fly skill](skills/fly/SKILL.md) routes to focused Fly-resource and Sprite
guidance. Tools and their argument schemas come from the server; the package
does not maintain a tool allowlist. New tools remain subject to server consent,
host support, and any directory review checks.

## Try it

- "Use Fly to show my authorized apps and Sprites."
- "Inspect the Machines and volumes for my app; do not change anything."
- "Show the names of my app secrets without their values."
- "Create a Sprite for this task and run the tests."
- "Open the Sprite Inspector for the environment I selected."

Codex's local shell is separate from both Machines and Sprites. The plugin uses
the corresponding remote tools and verifies selected resource identities.
Secret reads return metadata, not values. Mutation timeouts require checking
whether the operation completed before retrying.

## Troubleshooting

If Fly tools are missing, refresh or reinstall the plugin and restart Codex.
Use the host's plugin authorization flow if access expires or permissions are
missing; do not register another MCP server to work around the connection.
An empty list can reflect grant restrictions rather than an empty organization.
If the Inspector is unavailable in the host, direct inspection tools still work.

When moving from Sprites, authorize Fly separately and disable the original
plugin after verifying access. Keep operations on the selected connection;
their grants can differ even for identically named resources.

See the [official Fly MCP guide](https://mcp.fly.io/guide.md) for the current
server capabilities and the [release notes](../../release/README.md) for packaging.
