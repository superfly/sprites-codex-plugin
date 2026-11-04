# Fly.io plugins for Codex

This repository is one marketplace containing two independently installable plugins.

| Plugin | Scope | MCP endpoint | Source |
| --- | --- | --- | --- |
| **Fly.io** | Fly.io apps, Machines, volumes, app secrets, Managed Postgres, IP and certificate inspection, and Sprites | `https://mcp.fly.io` | [plugins/fly](plugins/fly/README.md) |
| **Sprites** | The original Sprites integration | `https://sprites.dev/mcp` | [plugins/sprites](plugins/sprites/README.md) |

Choose **Fly.io** for new installations. The original Sprites package remains
available for existing users. Fly.io is developed here; its presence in this
marketplace does not mean it has been published to the OpenAI directory.

## Install from Git

Add the repository marketplace once:

```sh
codex plugin marketplace add superfly/sprites-codex-plugin
```

Install **Fly.io**:

```sh
codex plugin add fly@flyio
```

Or install **Sprites** with `codex plugin add sprites@flyio`. Adding the
marketplace makes both available; it does not install or enable both. Restart
Codex and complete the selected plugin's OAuth flow.

For a local checkout, run this from the repository root instead:

```sh
codex plugin marketplace add .
codex plugin add fly@flyio
```

The catalog is [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json).
Each entry points to its own directory, manifest, skills, and connection.
The marketplace's internal name is `flyio`, and its visible label is **Fly.io**.
Plugin configuration keys are `fly@flyio` for Fly.io and `sprites@flyio` for
Sprites. Both Git and local installations use these identifiers. The repository
URL and name remain unchanged.

## Existing Git installations

Refresh an existing `flyio` Git marketplace:

```sh
codex plugin marketplace upgrade flyio
```

Then restart Codex and install Fly.io from the **Fly.io** marketplace. A checkout
registered with `add .` needs to be updated with Git instead; `marketplace
upgrade` refreshes Git-backed snapshots. A pinned Git ref must contain the Fly.io
package. Sparse checkouts must include `.agents/plugins`, `plugins/fly`, and
`plugins/sprites` to make both entries available.

### Migrating from the old `sprites` catalog

Older installations can stay on their existing revision. To opt into the renamed
catalog, remove the old registration and add this repository again:

```sh
codex plugin marketplace remove sprites
codex plugin marketplace add superfly/sprites-codex-plugin
codex plugin add fly@flyio
```

For a local checkout, use `codex plugin marketplace add .` from the repository
root instead of adding the Git source. To keep using Sprites, install
`sprites@flyio` instead of `fly@flyio`. Complete authorization for the new
installation. The old `fly@sprites` and `sprites@sprites` identifiers are not
aliases for the renamed catalog.

Installing Fly.io is opt-in. Each plugin keeps its own package identity and
endpoint. Fly.io needs its own authorization. After checking
that Fly.io can access the resources you need, disable or uninstall Sprites to
avoid overlapping Sprite tools and instructions. Do not assume their grants
are interchangeable. Switching plugins does not delete remote resources.

Git marketplace distribution is separate from the OpenAI directory: each
plugin has its own version, upload archive, and directory entry. Git users get
source changes when they refresh the relevant repository revision; directory
users get separately published releases. See the
[official marketplace documentation](https://developers.openai.com/plugins/build/plugins#marketplace-metadata).

## Build and validate

```sh
python3 -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
python3 scripts/check_repository.py
python3 -m unittest discover --start-directory tests --verbose
python3 scripts/package_plugin.py --plugin fly
python3 scripts/package_plugin.py --plugin sprites
```

The archives are written separately to `dist/`. Omitting `--plugin` continues
to build Sprites for compatibility with existing release commands. See
[release packaging](release/README.md) for identity and publication details.

CI also runs `python3 scripts/check_auth_metadata.py` against both live MCP
endpoints without credentials. This checks OAuth discovery and advertised
capabilities; human sign-in and revocation-isolation checks remain required
before directory submission.
