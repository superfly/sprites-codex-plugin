# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This repository ships two independent plugins. Directory uploads stay separate;
never upload Fly as an update to the Sprites entry.

## [Fly 1.0.0] - 2026-10-28

Initial Fly plugin for Codex. Connects to `https://mcp.fly.io` with its own
OAuth grant, skills, and directory package identity (`fly`). Source version
`1.0.0`; `release/fly.json` still has `plugin_id` and `published_version` unset
until the portal assigns and confirms them.

### Added

- Fly MCP connection for authorized apps, Machines, volumes, and app secrets
- Read-only inspection of IP assignments and TLS certificates
- Managed Postgres support: inspect clusters, plans, backups, databases,
  extensions, users, and query activity; create or fork clusters, create backups
  and databases, and enable extensions (deletion and user/password changes are
  not supported)
- Sprites workflows through the same Fly connection, including Sprite Inspector
  guidance
- Guidance for resource scopes, identity checks, mutation recovery, and keeping
  Fly and Sprites tokens isolated (do not reuse a grant across
  `https://mcp.fly.io` and `https://sprites.dev/mcp`)
- Separate reproducible directory packaging via
  `python3 scripts/package_plugin.py --plugin fly` (output `dist/fly-1.0.0.zip`)
- CI builds both directory archives and runs credential-free public OAuth
  metadata probes for both MCP endpoints

### Notes

- App creation, deployment workflows, and organization administration are not
  included
- Access follows the user's Fly MCP consent; product grants (for example Managed
  Postgres) are independent of app or Sprites access

## [Sprites 1.0.2] - Unreleased

**Held.** `release/README.md` records the last confirmed published directory
version as **1.0.0**. Source is **1.0.2**, an icon and listing metadata patch
over the unpublished 1.0.1 packaging work. OpenAI directory submission of this
patch is deferred until a future functional change; do not submit it alone.

### Changed

- Listing and composer icons updated to the purple Fly balloon artwork
  (committed 1024×1024 PNG)
- Website URL updated to `https://fly.io/sprites`
- Directory packaging made reproducible; upload copy uses the verified
  directory identity and strips local Codex attribution headers from the archive
  (authentication stays in the portal connection settings)
- Listing metadata tightened for directory rules (subtitle length, brand color
  `#16A34A`, PNG icons, support URL)

### Added (unpublished since 1.0.0)

- Guidance for selecting individual Sprites in supported desktop composers and
  opening the Sprite Inspector for services, checkpoints, and recent logs
- Verify selected Sprite identities (`sprite` + `sprite_id`) before remote
  operations; do not substitute a similarly named environment

## [Sprites 1.0.0] - Published

Confirmed published OpenAI directory version (`published_version` in
`release/directory.json`). No git tags exist; this section reflects the
published baseline the repository records against.

### Added

- Sprites plugin for Codex connecting to `https://sprites.dev/mcp`
- Skills for creating, listing, inspecting, and operating remote Sprites
  environments (files, commands, services, checkpoints, network policy)
- Local Codex client attribution headers on the MCP connection
- Repository CI for validation and tests
