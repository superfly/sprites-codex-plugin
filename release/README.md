# Directory release packaging

The last confirmed published directory version is **1.0.0**. The **1.0.1**
package is prepared and pending publication; preparing or uploading it does not
mean it has been approved or published. A previous upload labeled 0.2.0 entered
review before the published version was checked.

Build the directory ZIP from the repository root with Python 3.12 or newer:

```sh
python3 scripts/package_plugin.py
```

The output is `dist/sprites-1.0.1.zip` for the current version. ZIP files and
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

The logo is Fly.io's official color brandmark from
[Fly.io's brand assets](https://docs.fly.io/about/brand). The committed 512 x 512
PNG was rendered from the official SVG with transparent square padding. It is
used for both listing and composer icons. The green brand color `#16A34A` has
approximately 3.30:1 contrast against white, exceeding the directory's 2:1 minimum.
