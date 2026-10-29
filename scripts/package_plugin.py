#!/usr/bin/env python3
"""Build and preflight the directory upload without changing local plugin configuration."""

from __future__ import annotations

import argparse
import copy
import json
import re
import struct
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PLUGINS = {
    "sprites": ("release/directory.json", "https://sprites.dev/mcp"),
    "fly": ("release/fly.json", "https://mcp.fly.io"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def stable_version(value: str) -> tuple[int, ...]:
    require(
        bool(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value)),
        f"Expected a stable major.minor.patch version, got {value!r}",
    )
    return tuple(map(int, value.split(".")))


def contrast_against_white(color: str) -> float:
    require(bool(re.fullmatch(r"#[0-9a-fA-F]{6}", color)), "brandColor must be #RRGGBB")
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    luminance = sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    return 1.05 / (luminance + 0.05)


def json_bytes(data: dict) -> bytes:
    return (json.dumps(data, indent=2) + "\n").encode()


def string_map(value: object, message: str) -> dict[str, str]:
    require(isinstance(value, dict), message)
    require(
        all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()),
        message,
    )
    return value


def runtime_header_map(server: dict) -> dict[str, str]:
    """Return attribution headers from a Codex `.mcp.json` server entry."""
    message = "MCP headers must be an object of strings"
    headers = string_map(server.get("http_headers", {}), message)
    if "headers" not in server:
        return headers
    portable_headers = string_map(server["headers"], message)
    require(not headers or portable_headers == headers, "MCP header fields disagree")
    return portable_headers


def asset_path(value: str) -> str:
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts, "Asset must stay inside package")
    require(path.parts[0] == "assets", "Icons must be in assets/")
    return path.as_posix()


def validate_package(files: dict[str, bytes], release: dict, plugin: str = "sprites") -> None:
    """Check the effective manifests and known portal rules in the actual archive content."""
    manifest = json.loads(files["plugin.json"])
    legacy = json.loads(files[".codex-plugin/plugin.json"])
    identity = release["plugin_id"] or plugin
    for item in (manifest, legacy):
        require(item["name"] == identity, "Plugin name must match directory ID or new package name")
        version = stable_version(item["version"])
        if release["published_version"] is not None:
            require(
                version > stable_version(release["published_version"]),
                "Package version must exceed published_version",
            )
        require(not item.get("apps"), "Upload cannot declare app bindings")
        require(
            not item.get("extensions", {}).get("com.openai", {}).get("apps"),
            "Upload cannot declare app bindings",
        )
    require(manifest["version"] == legacy["version"], "Manifest versions must match")
    interface = manifest["extensions"]["com.openai"]["interface"]
    require(interface == legacy["interface"], "Manifest interfaces must match")
    for field, limit in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000)):
        require(0 < len(interface[field]) <= limit, f"{field} must be 1-{limit} characters")
    require(contrast_against_white(interface["brandColor"]) >= 2, "brandColor needs 2:1 contrast")
    prompts = interface["defaultPrompt"]
    prompts = [prompts] if isinstance(prompts, str) else prompts
    require(1 <= len(prompts) <= 3, "Expected 1-3 default prompts")
    require(
        all(p.strip() and len(p) <= 128 and "\n" not in p for p in prompts),
        "Prompts must be nonblank single lines of at most 128 characters",
    )
    require(len({" ".join(p.split()) for p in prompts}) == len(prompts), "Duplicate prompts")
    for field in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        url = urlparse(interface[field])
        require(
            url.scheme == "https" and bool(url.hostname) and not url.username and not url.password,
            f"{field} must be an HTTPS URL without credentials",
        )
    for field in ("logo", "composerIcon"):
        path = asset_path(interface[field])
        require(path in files, f"Missing icon: {path}")
        data = files[path]
        require(
            len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR",
            "Icons must be PNG files",
        )
        width, height = struct.unpack(">II", data[16:24])
        minimum = 256 if field == "logo" else 48
        require(minimum <= width == height <= 4096, "Icons must be square and correctly sized")
        require(len(data) <= 5 * 1024 * 1024, "Icon exceeds 5 MiB")
    portable = json.loads(files["mcp.json"])["mcpServers"]
    compatibility = json.loads(files[".mcp.json"])["mcpServers"]
    require(set(portable) == set(compatibility) == {plugin}, "Unexpected MCP server inventory")
    for servers in (portable, compatibility):
        server = servers[plugin]
        require("headers" not in server and "http_headers" not in server, "MCP headers unsupported")
        require(
            server["url"] == PLUGINS[plugin][1], "Keep the existing MCP endpoint for this plugin"
        )
    require(
        set(portable[plugin]) == {"type", "url"} and portable[plugin]["type"] == "streamable-http",
        "Unsupported portable MCP settings",
    )
    require(".app.json" not in files, "Upload cannot include .app.json")
    require(f"skills/{plugin}/SKILL.md" in files, f"Missing {plugin} skill")
    require(legacy["skills"] == "./skills/", "Unexpected legacy skill path")
    require(legacy["mcpServers"] == "./.mcp.json", "Unexpected legacy MCP path")


def build_package(
    root: Path, output: Path, published_version: str | None = None, *, plugin: str = "sprites"
) -> Path:
    require(plugin in PLUGINS, "Unknown plugin")
    source = root / "plugins" / plugin
    release = json.loads((root / PLUGINS[plugin][0]).read_text())
    if published_version:
        release["published_version"] = published_version
    if release["plugin_id"] is None:
        require(plugin == "fly", "Expected the verified directory plugin ID")
        require(release["published_version"] is None, "Published releases require a directory ID")
    else:
        require(
            bool(re.fullmatch(r"app-[0-9a-f]{32}", release["plugin_id"])),
            "Expected the verified directory plugin ID",
        )
        other = "sprites" if plugin == "fly" else "fly"
        other_release = json.loads((root / PLUGINS[other][0]).read_text())
        require(
            release["plugin_id"] != other_release["plugin_id"],
            "Plugins must have separate directory identities",
        )
    legacy = json.loads((source / ".codex-plugin/plugin.json").read_text())
    require(legacy["name"] == plugin, "Source plugin name must match selected plugin")
    manifest = {
        k: copy.deepcopy(v)
        for k, v in legacy.items()
        if k not in ("skills", "mcpServers", "interface")
    }
    manifest["$schema"] = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    manifest["extensions"] = {
        "com.openai": {
            "interface": copy.deepcopy(legacy["interface"]),
            "publication": {"release_notes": release["release_notes"]},
        }
    }
    if (source / "plugin.json").exists():
        portable_source = json.loads((source / "plugin.json").read_text())
        expected = copy.deepcopy(manifest)
        expected["extensions"]["com.openai"].pop("publication")
        # Source is authoritative for review/publication metadata as it is added.
        comparison = copy.deepcopy(portable_source)
        for field in ("review", "publication"):
            comparison.get("extensions", {}).get("com.openai", {}).pop(field, None)
        require(comparison == expected, "Portable source and compatibility manifest differ")
        manifest = portable_source
        manifest["extensions"]["com.openai"].setdefault("publication", {}).update(
            release_notes=release["release_notes"]
        )
    identity = release["plugin_id"] or plugin
    manifest["name"] = legacy["name"] = identity
    config = json.loads((source / ".mcp.json").read_text())
    require(set(config["mcpServers"]) == {plugin}, "Unexpected source MCP server inventory")
    server = config["mcpServers"][plugin]
    # Legacy Codex `.mcp.json` accepts `type` and then removes it. `tool_timeout_sec`
    # and `http_headers` are real Codex fields. Portable `mcp.json` cannot carry them:
    # the Agent Plugins schema and Codex's parser only allow `type`, `url`, and `headers`.
    require(
        set(server) <= {"url", "http_headers", "headers", "tool_timeout_sec", "type"},
        "Unsupported source MCP setting; review before packaging",
    )
    if "type" in server:
        require(server["type"] == "streamable-http", "Unsupported source MCP transport")
    runtime_headers = runtime_header_map(server)
    packaged_runtime = copy.deepcopy(config)
    packaged_server = packaged_runtime["mcpServers"][plugin]
    # Directory archives keep the previously accepted compatibility shape.
    for field in ("type", "http_headers", "headers"):
        packaged_server.pop(field, None)
    portable = {
        "$schema": PORTABLE_MCP_SCHEMA,
        "mcpServers": {plugin: {"type": "streamable-http", "url": server["url"]}},
    }
    if (source / "mcp.json").exists():
        source_portable = json.loads((source / "mcp.json").read_text())
        require(
            set(source_portable) <= {"$schema", "mcpServers"}
            and source_portable.get("$schema") == PORTABLE_MCP_SCHEMA,
            "Unsupported portable MCP settings",
        )
        require(
            set(source_portable["mcpServers"]) == {plugin},
            "Unexpected source MCP server inventory",
        )
        declared = source_portable["mcpServers"][plugin]
        # `http_headers` and `tool_timeout_sec` are invalid on this file. Codex
        # rejects the server, and the published schema sets additionalProperties false.
        require(set(declared) <= {"type", "url", "headers"}, "Unsupported portable MCP settings")
        require(declared.get("type") == "streamable-http", "Unsupported portable MCP settings")
        require(
            declared.get("url") == server["url"],
            "Portable source and compatibility MCP configurations differ",
        )
        declared_headers = string_map(
            declared.get("headers", {}), "MCP headers must be an object of strings"
        )
        require(
            declared_headers == runtime_headers,
            "Portable source and compatibility MCP configurations differ",
        )
    files = {
        "plugin.json": json_bytes(manifest),
        ".codex-plugin/plugin.json": json_bytes(legacy),
        "mcp.json": json_bytes(portable),
        ".mcp.json": json_bytes(packaged_runtime),
        "LICENSE": (root / "LICENSE").read_bytes(),
    }
    paths = {asset_path(legacy["interface"][field]) for field in ("logo", "composerIcon")}
    paths.update(p.relative_to(source).as_posix() for p in (source / "skills").rglob("*.md"))
    for relative in sorted(paths):
        path = source / relative
        require(path.resolve().is_relative_to(source.resolve()), "File escapes plugin directory")
        require(not path.is_symlink(), "Package cannot contain symlinks")
        files[relative] = path.read_bytes()
    validate_package(files, release, plugin)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{plugin}-{manifest['version']}.zip"
    # Fixed metadata and sorted paths make repeated builds byte-for-byte reproducible.
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(f"{identity}/{name}", (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)
    with zipfile.ZipFile(archive) as bundle:
        require(bundle.testzip() is None, "ZIP integrity check failed")
        prefix = identity + "/"
        actual = {name.removeprefix(prefix): bundle.read(name) for name in bundle.namelist()}
        require(actual == files, "ZIP content differs from prepared package")
        validate_package(actual, release, plugin)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--plugin", choices=PLUGINS, default="sprites")
    parser.add_argument("--published-version", help="Override the last confirmed published version")
    args = parser.parse_args()
    try:
        archive = build_package(ROOT, args.output_dir, args.published_version, plugin=args.plugin)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Packaging failed: {exc}\n")
    print(f"Built and locally validated {archive}")
    print("Portal acceptance, review, and publication are not verified by these checks.")


if __name__ == "__main__":
    main()
