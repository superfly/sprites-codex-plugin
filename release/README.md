# Directory release packaging

## Separate Fly and Sprites releases

This repository's Git marketplace exposes both plugins independently. Directory
uploads also remain separate; never upload Fly as an update to the Sprites entry.

```sh
python3 scripts/package_plugin.py --plugin fly
python3 scripts/package_plugin.py --plugin sprites
```

Fly starts at **1.0.0**, producing `dist/fly-1.0.0.zip`. Its settings live in
[fly.json](fly.json), with `plugin_id` and `published_version` set to `null`
until assigned or confirmed in the portal. Its initial package identity and
archive folder are `fly`. Record Fly's own verified directory ID after creation;
never reuse Sprites' ID. Set `published_version` only after confirming publication.
Once set, subsequent package versions must exceed it.

Fly's portable source manifests and Codex compatibility files must agree. The
packager checks their identity, version, listing, and endpoint, includes the
skill's Markdown references and icon, and preserves any review/publication
metadata added to the portable source. It adds release notes from `fly.json`.
Review cases, demo, and other publication details have not yet been prepared;
the ZIP is a development package, not a claim of submission readiness.

The build rejects shared directory IDs and validates each plugin against its
own MCP endpoint. Both archives are deterministic. Building one does not change
the other or rewrite Git installation identities. No portal actions are performed.
Both local `.mcp.json` files include Codex client attribution headers; the
packager removes those headers from both directory archives.

## Connection validation before submission

CI builds both archives and runs `python3 scripts/check_auth_metadata.py` in a
separate job. The probe uses only unauthenticated GETs: it checks each MCP
endpoint's 401/Bearer challenge, resource and issuer identity, PKCE S256, a DCR
registration endpoint, public-client support, and the refresh-token grant type.
It sends an SSE Accept header
so Fly's public HTML landing page is not mistaken for an authenticated MCP
response. It never registers a client, logs in, or revokes a grant. Failures in
this job can reflect a live endpoint outage as well as an auth metadata change.

Before directory submission, a human must complete browser OAuth for **both**
plugins in the target host and run a read-only resource listing through each.
Using separate test grants, revoke Fly's grant and confirm Fly loses access
while Sprites still works; reauthorize Fly, then revoke Sprites' grant and
confirm Sprites loses access while Fly still works. Check that the host cannot
refresh the revoked grant. Record the host version and results without tokens,
authorization codes, or private output. This end-to-end and revocation-isolation
check remains pending; the credential-free probe does not establish it.

## Existing Sprites release

The recorded last confirmed published directory version is **1.0.0**. The source
version is **1.0.2**, an icon and listing metadata patch over 1.0.1. OpenAI directory submission
and publication are deferred until a future functional change; this patch should
not be submitted for review on its own. Preparing a package does not mean it has
been approved or published. A previous upload labeled 0.2.0 entered review before
the published version was checked.

Build the directory ZIP from the repository root with Python 3.12 or newer:

```sh
python3 scripts/package_plugin.py
```

The output is `dist/sprites-1.0.2.zip` for the current version. ZIP files and
staging copies stay in ignored `dist/`; commit the source and release settings.
No additional Python packages or network access are needed to build the ZIP.

The local manifest is the source for the version and listing. Before each
release, confirm the latest published version in the directory and update
`published_version` in [directory.json](directory.json). Increase the source
manifest version above it, and update `release_notes` for the intended release.
An explicit `--published-version 1.0.1` can override the recorded baseline for a
single build. This check cannot discover remote publication changes itself.

The packager preserves the local plugin name `sprites` and local attribution
headers. In the upload copy only, it uses the verified directory identity
`app-6a8485b5beac8191954e37241acffe6d` in both manifests and the archive folder,
generates portable `plugin.json` and `mcp.json`, and removes `headers` and
`http_headers` from both MCP configurations. The directory rejected those
headers during existing-connection setup. Authentication belongs in the portal's
connection settings; no credentials belong in the package.

Local checks cover version progression, matching manifests, the directory ID,
MCP endpoint and headers, subtitle length, default prompts, required HTTPS links,
brand color contrast against white, icon paths and PNG dimensions, skill presence,
and the final ZIP contents. The build uses fixed ZIP metadata so identical source
produces identical bytes. These checks cover known upload constraints, not every
portal rule. They do not verify live URLs, remote tool behavior, connection state,
review materials, scans, attestations, or publication status.

After uploading to the existing entry, inspect its saved listing, connection,
review materials, and publication settings. Review and publication are separate
steps. Replacing an in-review submission requires cancelling review first; do
not infer approval to cancel from a request to prepare a ZIP.

The logo is the supplied Fly balloon artwork on a purple background. The
committed 1024 x 1024 PNG is used unchanged for both listing and composer icons.
The green brand color `#16A34A` has
approximately 3.30:1 contrast against white, exceeding the directory's 2:1 minimum.
