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


def asset_path(value: str) -> str:
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts, "Asset must stay inside package")
    require(path.parts[0] == "assets", "Icons must be in assets/")
    return path.as_posix()


def validate_package(files: dict[str, bytes], release: dict) -> None:
    """Check the effective manifests and known portal rules in the actual archive content."""
    manifest = json.loads(files["plugin.json"])
    legacy = json.loads(files[".codex-plugin/plugin.json"])
    for item in (manifest, legacy):
        require(item["name"] == release["plugin_id"], "Plugin name must match directory ID")
        require(
            stable_version(item["version"]) > stable_version(release["published_version"]),
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
    require(set(portable) == set(compatibility) == {"sprites"}, "Unexpected MCP server inventory")
    for servers in (portable, compatibility):
        server = servers["sprites"]
        require("headers" not in server and "http_headers" not in server, "MCP headers unsupported")
        require(server["url"] == "https://sprites.dev/mcp", "Keep the existing MCP endpoint")
    require(
        set(portable["sprites"]) == {"type", "url"}
        and portable["sprites"]["type"] == "streamable-http",
        "Unsupported portable MCP settings",
    )
    require(".app.json" not in files, "Upload cannot include .app.json")
    require("skills/sprites/SKILL.md" in files, "Missing Sprites skill")
    require(legacy["skills"] == "./skills/", "Unexpected legacy skill path")
    require(legacy["mcpServers"] == "./.mcp.json", "Unexpected legacy MCP path")


def build_package(root: Path, output: Path, published_version: str | None = None) -> Path:
    source = root / "plugins/sprites"
    release = json.loads((root / "release/directory.json").read_text())
    if published_version:
        release["published_version"] = published_version
    require(
        bool(re.fullmatch(r"app-[0-9a-f]{32}", release["plugin_id"])),
        "Expected the verified directory plugin ID",
    )
    legacy = json.loads((source / ".codex-plugin/plugin.json").read_text())
    legacy["name"] = release["plugin_id"]
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
    config = json.loads((source / ".mcp.json").read_text())
    require(set(config["mcpServers"]) == {"sprites"}, "Unexpected source MCP server inventory")
    server = config["mcpServers"]["sprites"]
    require(
        set(server) <= {"url", "http_headers", "headers", "tool_timeout_sec"},
        "Unsupported source MCP setting; review before packaging",
    )
    server.pop("http_headers", None)
    server.pop("headers", None)
    portable = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        "mcpServers": {"sprites": {"type": "streamable-http", "url": server["url"]}},
    }
    files = {
        "plugin.json": json_bytes(manifest),
        ".codex-plugin/plugin.json": json_bytes(legacy),
        "mcp.json": json_bytes(portable),
        ".mcp.json": json_bytes(config),
        "LICENSE": (root / "LICENSE").read_bytes(),
    }
    paths = {asset_path(legacy["interface"][field]) for field in ("logo", "composerIcon")}
    paths.update(p.relative_to(source).as_posix() for p in (source / "skills").rglob("*.md"))
    for relative in sorted(paths):
        path = source / relative
        require(path.resolve().is_relative_to(source.resolve()), "File escapes plugin directory")
        require(not path.is_symlink(), "Package cannot contain symlinks")
        files[relative] = path.read_bytes()
    validate_package(files, release)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"sprites-{manifest['version']}.zip"
    # Fixed metadata and sorted paths make repeated builds byte-for-byte reproducible.
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(f"{release['plugin_id']}/{name}", (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)
    with zipfile.ZipFile(archive) as bundle:
        require(bundle.testzip() is None, "ZIP integrity check failed")
        prefix = release["plugin_id"] + "/"
        actual = {name.removeprefix(prefix): bundle.read(name) for name in bundle.namelist()}
        require(actual == files, "ZIP content differs from prepared package")
        validate_package(actual, release)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--published-version", help="Override the last confirmed published version")
    args = parser.parse_args()
    try:
        archive = build_package(ROOT, args.output_dir, args.published_version)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Packaging failed: {exc}\n")
    print(f"Built and locally validated {archive}")
    print("Portal acceptance, review, and publication are not verified by these checks.")


if __name__ == "__main__":
    main()
