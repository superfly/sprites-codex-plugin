---
name: fly
description: Operate Fly.io apps, Machines, volumes, app secrets, Managed Postgres, and Sprites through Fly MCP. Use for inspecting or managing Fly resources and working in Sprite environments.
---

# Fly

Use the Fly plugin's MCP tools at `https://mcp.fly.io`. This connection covers
both Fly resources and Sprites. Codex's local workspace, a Fly Machine, and a
Sprite filesystem are separate environments.

## Connection and scope

Use the installed plugin's direct tools. Discover the current tool schema before
constructing arguments; the references describe tool selection, not fixed schemas.
Do not register a second MCP server or start a separate CLI login during ordinary
plugin use. If tools are absent, explain that the Fly connection is not loaded
and ask the user to refresh the plugin or restart the host. Let the host handle
OAuth; after the user completes authorization, retry the original call once.

Use `get_fly_context` when establishing the target or diagnosing denied access.
It reports authorized resource bindings, scopes, and restrictions; a catalog
entry does not grant permission to operate a resource. `list_organizations` and
`get_organization` describe organizations but do not authorize their resources.
`get_launch_requirements` explains blockers and returns browser handoffs; it
does not accept terms or change billing settings.

Resolve the organization and app, Machine, volume, Postgres cluster/database, or
Sprite before acting.
Use IDs returned by discovery or explicit selections. Ask only when the target
is ambiguous. Do not fall back to another connection, organization, or similarly
named resource after an authorization failure. If both Fly and Sprites plugins
are enabled, keep this workflow on the Fly connection; their grants can differ.

### Authentication isolation

Never reuse a Sprites token issued for `https://sprites.dev/mcp` against
`https://mcp.fly.io`, or a Fly MCP token against the Sprites endpoint. Authorize
each connection separately through the host's OAuth flow. Never ask for or paste
API tokens into chat, or copy tokens between connections to bypass a failure.
Check the selected connection's status: a connected app and a local MCP server
with the same display name can have separate authorization.

## Choose a workflow

- For Fly apps, Machines, volumes, secrets, IPs, certificates, or Managed Postgres, read
  [Fly resources](references/fly-resources.md).
- For Sprite files, commands, services, checkpoints, network policies, composer
  mentions, or Inspector, read [Sprites](references/sprites.md).

Use the smallest tool that serves the request. Summarize results instead of
dumping configuration, private output, or raw JSON. Honor the user's authorized
scope; read-only inspection does not authorize creating billable resources,
interrupting services, or deleting data. Existing explicit authorization need
not be requested again.

After a write times out or loses its response, inspect the target before
retrying: the operation may have completed. Distinguish accepted asynchronous
work from completion. Permission errors require correcting the grant through
the host's consent flow, not repeated calls or credentials copied into chat.

## Capability boundary

The server supports direct operations on existing Fly apps and their resources,
Managed Postgres inspection and provisioning, and Sprite lifecycle and runtime
operations. Postgres tools can create and fork clusters, create backups and
databases, and enable extensions; they cannot delete Postgres resources, change
users or passwords, or return passwords. IPs and TLS certificates are read-only.
App creation, deployment workflows, other product provisioning, and organization
administration are not included. Creating a Machine from supplied
configuration is not a complete build-and-deploy workflow. Explain unsupported
steps instead of inventing tools or silently switching to another integration.

The live tool schemas and authorization are authoritative. The references were
checked against the [Fly MCP guide](https://mcp.fly.io/guide.md) on 2026-10-28.
