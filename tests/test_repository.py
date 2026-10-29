from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class CodexPluginRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.marketplace = load_json(ROOT / ".agents/plugins/marketplace.json")
        self.listings = self.marketplace["plugins"]

    def test_marketplace_preserves_existing_identity_and_exposes_both_plugins(self) -> None:
        self.assertEqual(self.marketplace["name"], "sprites")
        self.assertEqual(self.marketplace["interface"]["displayName"], "Fly.io")
        names = [entry["name"] for entry in self.listings]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {"sprites", "fly"})
        for listing in self.listings:
            with self.subTest(plugin=listing["name"]):
                self.assertEqual(listing["source"]["source"], "local")
                self.assertEqual(listing["source"]["path"], f"./plugins/{listing['name']}")
                root = ROOT / listing["source"]["path"]
                manifest = load_json(root / ".codex-plugin/plugin.json")
                self.assertEqual(listing["name"], manifest["name"])
                self.assertEqual(listing["policy"]["installation"], "AVAILABLE")
                self.assertEqual(listing["policy"]["authentication"], "ON_INSTALL")
                self.assertTrue((root / manifest["skills"]).is_dir())
                self.assertTrue((root / manifest["mcpServers"]).is_file())
                for key in ("composerIcon", "logo"):
                    self.assertTrue((root / manifest["interface"][key]).is_file())

    def test_sprites_catalog_and_homepage_follow_sprites_dev(self) -> None:
        manifest = load_json(ROOT / "plugins/sprites/.codex-plugin/plugin.json")
        self.assertEqual(manifest["homepage"], "https://sprites.dev")
        self.assertEqual(manifest["interface"]["websiteURL"], "https://sprites.dev")
        skill = (ROOT / "plugins/sprites/skills/sprites/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Sprites MCP (24)", skill)
        self.assertIn("Fly MCP / host extensions", skill)
        for name in (
            "file_list",
            "file_read",
            "file_write",
            "file_copy",
            "file_rename",
            "file_delete",
        ):
            self.assertIn(f"`{name}`", skill)

    def test_mcp_manifests_use_the_fields_codex_accepts(self) -> None:
        schema = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
        for name, endpoint in (
            ("sprites", "https://sprites.dev/mcp"),
            ("fly", "https://mcp.fly.io"),
        ):
            with self.subTest(plugin=name):
                root = ROOT / "plugins" / name
                portable_file = load_json(root / "mcp.json")
                runtime = load_json(root / ".mcp.json")["mcpServers"][name]
                portable = portable_file["mcpServers"][name]
                self.assertEqual(set(portable_file), {"$schema", "mcpServers"})
                self.assertEqual(portable_file["$schema"], schema)
                # Portable mcp.json is the Agent Plugins file Codex parses with
                # deny_unknown_fields. Only type, url, and headers are valid.
                self.assertEqual(set(portable), {"type", "url", "headers"})
                self.assertEqual(portable["type"], "streamable-http")
                self.assertEqual(portable["url"], endpoint)
                # Legacy .mcp.json keeps Codex fields. `type` is removed before
                # validation; `headers` would be rejected as unknown.
                self.assertEqual(set(runtime), {"type", "url", "http_headers", "tool_timeout_sec"})
                self.assertEqual(runtime["type"], "streamable-http")
                self.assertEqual(runtime["url"], endpoint)
                self.assertEqual(runtime["http_headers"], portable["headers"])
                self.assertGreaterEqual(runtime["tool_timeout_sec"], 60)
                self.assertEqual(
                    runtime["http_headers"],
                    {"Fly-Client-Agent": "codex", "Fly-Client-Interactive": "false"},
                )

    def test_connections_remain_separate(self) -> None:
        for name, endpoint in (
            ("sprites", "https://sprites.dev/mcp"),
            ("fly", "https://mcp.fly.io"),
        ):
            with self.subTest(plugin=name):
                servers = load_json(ROOT / f"plugins/{name}/.mcp.json")["mcpServers"]
                self.assertEqual(set(servers), {name})
                self.assertEqual(servers[name]["url"], endpoint)
                self.assertGreaterEqual(servers[name]["tool_timeout_sec"], 60)

    def test_fly_portable_and_compatibility_installs_are_equivalent(self) -> None:
        root = ROOT / "plugins/fly"
        portable = load_json(root / "plugin.json")
        compatibility = load_json(root / ".codex-plugin/plugin.json")
        for key, value in compatibility.items():
            if key == "interface":
                self.assertEqual(portable["extensions"]["com.openai"][key], value)
            elif key not in ("skills", "mcpServers"):
                self.assertEqual(portable[key], value)
        portable = load_json(root / "mcp.json")["mcpServers"]["fly"]
        runtime = load_json(root / ".mcp.json")["mcpServers"]["fly"]
        self.assertEqual(
            compatibility["keywords"],
            ["fly", "fly.io", "machines", "volumes", "postgres", "sprites", "mcp", "codex"],
        )
        self.assertEqual(set(portable), {"type", "url", "headers"})
        self.assertEqual(portable["type"], "streamable-http")
        self.assertEqual(portable["url"], runtime["url"])
        self.assertEqual(portable["headers"], runtime["http_headers"])
        self.assertNotIn("http_headers", portable)
        self.assertNotIn("tool_timeout_sec", portable)


if __name__ == "__main__":
    unittest.main()
