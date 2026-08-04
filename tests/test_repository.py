from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class CodexPluginRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.marketplace = load_json(ROOT / ".agents/plugins/marketplace.json")
        self.listing = self.marketplace["plugins"][0]
        self.plugin_root = ROOT / self.listing["source"]["path"]
        self.manifest = load_json(self.plugin_root / ".codex-plugin/plugin.json")

    def test_marketplace_points_to_plugin(self) -> None:
        self.assertEqual(self.marketplace["name"], self.manifest["name"])
        self.assertEqual(self.listing["name"], self.manifest["name"])
        self.assertEqual(self.listing["source"]["source"], "local")
        self.assertTrue(self.plugin_root.is_dir())

    def test_install_policy_requires_authentication(self) -> None:
        policy = self.listing["policy"]
        self.assertEqual(policy["installation"], "AVAILABLE")
        self.assertEqual(policy["authentication"], "ON_INSTALL")

    def test_manifest_references_existing_content(self) -> None:
        self.assertTrue((self.plugin_root / self.manifest["skills"]).is_dir())
        self.assertTrue((self.plugin_root / self.manifest["mcpServers"]).is_file())
        interface = self.manifest["interface"]
        self.assertTrue((self.plugin_root / interface["composerIcon"]).is_file())
        self.assertTrue((self.plugin_root / interface["logo"]).is_file())

    def test_mcp_server_uses_https(self) -> None:
        config = load_json(self.plugin_root / self.manifest["mcpServers"])
        server = config["mcpServers"]["sprites"]
        parsed = urlparse(server["url"])
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "sprites.dev")
        self.assertEqual(parsed.path, "/mcp")
        self.assertGreaterEqual(server["tool_timeout_sec"], 60)


if __name__ == "__main__":
    unittest.main()
