from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_plugin import ROOT, build_package, json_bytes, validate_package


class DirectoryPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.release = json.loads((ROOT / "release/directory.json").read_text())
        self.archive = build_package(ROOT, self.output)
        with zipfile.ZipFile(self.archive) as bundle:
            prefix = self.release["plugin_id"] + "/"
            self.files = {
                name.removeprefix(prefix): bundle.read(name) for name in bundle.namelist()
            }

    def edit_json(self, path: str, edit) -> None:
        data = json.loads(self.files[path])
        edit(data)
        self.files[path] = json_bytes(data)

    def edit_interfaces(self, **changes) -> None:
        self.edit_json(
            "plugin.json",
            lambda m: m["extensions"]["com.openai"]["interface"].update(changes),
        )
        self.edit_json(".codex-plugin/plugin.json", lambda m: m["interface"].update(changes))

    def test_package_preserves_runtime_skill_and_local_configuration(self) -> None:
        source = ROOT / "plugins/sprites"
        self.assertEqual(
            self.files["skills/sprites/SKILL.md"], (source / "skills/sprites/SKILL.md").read_bytes()
        )
        local = json.loads((source / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(local["name"], "sprites")
        server = json.loads((source / ".mcp.json").read_text())["mcpServers"]["sprites"]
        self.assertEqual(server["http_headers"]["Fly-Client-Agent"], "codex")
        self.assertEqual(server["http_headers"]["Fly-Client-Interactive"], "false")
        self.assertNotIn(
            "http_headers", json.loads(self.files[".mcp.json"])["mcpServers"]["sprites"]
        )
        self.assertNotIn("headers", json.loads(self.files["mcp.json"])["mcpServers"]["sprites"])

    def test_reproducible_archive(self) -> None:
        first = self.archive.read_bytes()
        self.assertEqual(build_package(ROOT, self.output).read_bytes(), first)

    def test_rejects_wrong_directory_identity(self) -> None:
        self.edit_json("plugin.json", lambda m: m.update(name="sprites"))
        with self.assertRaisesRegex(ValueError, "directory ID"):
            validate_package(self.files, self.release)

    def test_rejects_non_increasing_version(self) -> None:
        candidate = json.loads(self.files["plugin.json"])["version"]
        for published in (candidate, "99.0.0"):
            with self.subTest(published=published):
                with self.assertRaisesRegex(ValueError, "exceed published_version"):
                    build_package(ROOT, self.output, published)

    def test_rejects_mismatched_manifest_versions(self) -> None:
        self.edit_json(".codex-plugin/plugin.json", lambda m: m.update(version="2.0.0"))
        with self.assertRaisesRegex(ValueError, "versions must match"):
            validate_package(self.files, self.release)

    def test_rejects_headers_in_either_configuration(self) -> None:
        for path, key in (("mcp.json", "headers"), (".mcp.json", "http_headers")):
            with self.subTest(path=path):
                original = self.files[path]
                self.edit_json(path, lambda m: m["mcpServers"]["sprites"].update({key: {}}))
                with self.assertRaisesRegex(ValueError, "headers unsupported"):
                    validate_package(self.files, self.release)
                self.files[path] = original

    def test_rejects_previous_low_contrast_color(self) -> None:
        self.edit_interfaces(brandColor="#8AE234")
        with self.assertRaisesRegex(ValueError, "2:1 contrast"):
            validate_package(self.files, self.release)

    def test_rejects_previous_long_subtitle(self) -> None:
        self.edit_interfaces(shortDescription="Manage remote development sprites from Codex.")
        with self.assertRaisesRegex(ValueError, "shortDescription"):
            validate_package(self.files, self.release)

    def test_rejects_missing_logo(self) -> None:
        self.edit_interfaces(logo="./assets/missing.png")
        with self.assertRaisesRegex(ValueError, "Missing icon"):
            validate_package(self.files, self.release)

    def test_rejects_asset_path_escape(self) -> None:
        self.edit_interfaces(logo="../outside.png")
        with self.assertRaisesRegex(ValueError, "inside package"):
            validate_package(self.files, self.release)

    def test_rejects_non_square_logo(self) -> None:
        name = "assets/fly-logo.png"
        data = bytearray(self.files[name])
        data[20:24] = (256).to_bytes(4, "big")
        self.files[name] = bytes(data)
        with self.assertRaisesRegex(ValueError, "square"):
            validate_package(self.files, self.release)

    def test_rejects_changed_endpoint(self) -> None:
        self.edit_json(
            "mcp.json", lambda m: m["mcpServers"]["sprites"].update(url="https://example.com/mcp")
        )
        with self.assertRaisesRegex(ValueError, "existing MCP endpoint"):
            validate_package(self.files, self.release)
