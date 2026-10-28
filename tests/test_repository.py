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
        server = load_json(root / "mcp.json")["mcpServers"]
        self.assertEqual(server, {"fly": {"type": "streamable-http", "url": "https://mcp.fly.io"}})


if __name__ == "__main__":
    unittest.main()
