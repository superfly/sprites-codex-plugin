from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from scripts.check_auth_metadata import ENDPOINTS, probe


class AuthMetadataTests(unittest.TestCase):
    def responses(self, name: str) -> list:
        resource, metadata_url, issuer, _issuer_metadata_url = ENDPOINTS[name]
        return [
            (401, {"www-authenticate": f'Bearer resource_metadata="{metadata_url}"'}, b""),
            (
                200,
                {},
                json.dumps({"resource": resource, "authorization_servers": [issuer]}).encode(),
            ),
            (
                200,
                {},
                json.dumps(
                    {
                        "issuer": issuer,
                        "authorization_endpoint": issuer + "/authorize",
                        "token_endpoint": issuer + "/token",
                        "registration_endpoint": issuer + "/register",
                        "code_challenge_methods_supported": ["S256"],
                        "token_endpoint_auth_methods_supported": ["none"],
                        "grant_types_supported": ["authorization_code"],
                        "response_types_supported": ["code"],
                    }
                ).encode(),
            ),
        ]

    def test_each_connection_uses_its_own_discovery_and_mcp_accept_header(self) -> None:
        for name, (resource, metadata, _issuer, issuer_metadata) in ENDPOINTS.items():
            with (
                self.subTest(name=name),
                patch("scripts.check_auth_metadata.get", side_effect=self.responses(name)) as get,
            ):
                probe(name)
                self.assertEqual(
                    [call.args for call in get.call_args_list],
                    [(resource, "text/event-stream"), (metadata,), (issuer_metadata,)],
                )

    def test_rejects_landing_page_or_missing_challenge(self) -> None:
        for response in [(200, {}, b"<html>"), (401, {}, b"")]:
            with (
                self.subTest(response=response),
                patch("scripts.check_auth_metadata.get", return_value=response) as get,
            ):
                with self.assertRaises(ValueError):
                    probe("fly")
                get.assert_called_once()

    def test_rejects_cross_connection_discovery(self) -> None:
        for index, field, value in (
            (1, "resource", ENDPOINTS["sprites"][0]),
            (1, "authorization_servers", [ENDPOINTS["sprites"][2]]),
            (2, "issuer", ENDPOINTS["sprites"][2]),
        ):
            with self.subTest(field=field):
                responses = self.responses("fly")
                document = json.loads(responses[index][2])
                document[field] = value
                responses[index] = (200, {}, json.dumps(document).encode())
                with patch("scripts.check_auth_metadata.get", side_effect=responses):
                    with self.assertRaises(ValueError):
                        probe("fly")

    def test_rejects_missing_pkce_dcr_or_public_client_support(self) -> None:
        for field in (
            "code_challenge_methods_supported",
            "registration_endpoint",
            "token_endpoint_auth_methods_supported",
        ):
            with self.subTest(field=field):
                responses = self.responses("fly")
                document = json.loads(responses[2][2])
                del document[field]
                responses[2] = (200, {}, json.dumps(document).encode())
                with patch("scripts.check_auth_metadata.get", side_effect=responses):
                    with self.assertRaises(ValueError):
                        probe("fly")
