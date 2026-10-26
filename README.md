# Fly.io plugins for Codex

This repository is one marketplace containing two independently installable plugins.

| Plugin | Scope | MCP endpoint | Source |
| --- | --- | --- | --- |
| **Fly** | Fly apps, Machines, volumes, app secrets, IP and certificate inspection, and Sprites | `https://mcp.fly.io` | [plugins/fly](plugins/fly/README.md) |
| **Sprites** | The original Sprites integration | `https://sprites.dev/mcp` | [plugins/sprites](plugins/sprites/README.md) |

Choose **Fly** for new installations. The original Sprites package remains
available for existing users. Fly is developed here; its presence in this
marketplace does not mean it has been published to the OpenAI directory.

## Install from Git

Add the repository marketplace once:

```sh
codex plugin marketplace add superfly/sprites-codex-plugin
```

Restart Codex, open the plugin directory, select the **Fly.io** marketplace,
and install **Fly** or **Sprites**. Adding the marketplace makes both available;
it does not install or enable both. Complete the selected plugin's OAuth flow.

For a local checkout, run this from the repository root instead:

```sh
codex plugin marketplace add .
```

The catalog is [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json).
Each entry points to its own directory, manifest, skills, and connection.
The marketplace's internal name remains `sprites` for compatibility, while its
visible label is **Fly.io**. Plugin configuration keys remain `sprites@sprites`
for the original plugin and `fly@sprites` for Fly. The repository URL and name
do not need to change.

## Existing Git installations

Refresh the Git marketplace to discover Fly:

```sh
codex plugin marketplace upgrade sprites
```

Then restart Codex and install Fly from the **Fly.io** marketplace. A checkout
registered with `add .` needs to be updated with Git instead; `marketplace
upgrade` refreshes Git-backed snapshots. A pinned Git ref must contain the Fly
package. Sparse checkouts must include `.agents/plugins`, `plugins/fly`, and
`plugins/sprites` to make both entries available.

Installing Fly is opt-in: existing Sprites settings, package identity, and
endpoint remain unchanged. Fly needs its own authorization. After checking
that Fly can access the resources you need, disable or uninstall Sprites to
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
