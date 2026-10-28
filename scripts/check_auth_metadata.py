#!/usr/bin/env python3
"""Probe public MCP OAuth metadata without credentials or client registration."""

from __future__ import annotations

import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

# Pin discovery to each connection's own resource and authorization server.
ENDPOINTS = {
    "fly": (
        "https://mcp.fly.io",
        "https://mcp.fly.io/.well-known/oauth-protected-resource",
        "https://fly.io/mcp/oauth",
        "https://fly.io/.well-known/oauth-authorization-server/mcp/oauth",
    ),
    "sprites": (
        "https://sprites.dev/mcp",
        "https://sprites.dev/.well-known/oauth-protected-resource/mcp",
        "https://sprites.dev",
        "https://sprites.dev/.well-known/oauth-authorization-server",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def get(url: str, accept: str = "application/json") -> tuple[int, dict, bytes]:
    request = Request(url, headers={"Accept": accept})
    try:
        response = urlopen(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        return response.status, dict(response.headers.items()), response.read(1024 * 1024)


def get_json(url: str) -> dict:
    status, _headers, body = get(url)
    require(status == 200, f"Discovery document returned HTTP {status}: {url}")
    data = json.loads(body)
    require(isinstance(data, dict), f"Discovery document must be an object: {url}")
    return data


def probe(name: str) -> None:
    resource, metadata_url, issuer, issuer_metadata_url = ENDPOINTS[name]
    # Fly serves an HTML landing page for ordinary GETs. Ask for MCP's SSE transport.
    status, headers, _body = get(resource, "text/event-stream")
    require(status == 401, f"Unauthenticated MCP request returned HTTP {status}, expected 401")
    challenge = next((v for k, v in headers.items() if k.lower() == "www-authenticate"), "")
    require(bool(re.match(r"Bearer\s", challenge, re.I)), "Missing Bearer WWW-Authenticate")
    match = re.search(r'\bresource_metadata="([^"]+)"', challenge)
    require(match is not None and match[1] == metadata_url, "Unexpected resource metadata URL")

    metadata = get_json(metadata_url)
    require(metadata.get("resource") == resource, "Resource identity mismatch")
    require(issuer in metadata.get("authorization_servers", []), "Expected issuer not advertised")
    authorization = get_json(issuer_metadata_url)
    require(authorization.get("issuer") == issuer, "Authorization issuer mismatch")
    for key in ("authorization_endpoint", "token_endpoint", "registration_endpoint"):
        url = urlsplit(authorization.get(key, ""))
        require(
            url.scheme == "https" and bool(url.hostname) and not url.username and not url.password,
            f"Missing or invalid HTTPS {key}",
        )
    for key, value in (
        ("code_challenge_methods_supported", "S256"),
        ("token_endpoint_auth_methods_supported", "none"),
        ("grant_types_supported", "authorization_code"),
        ("grant_types_supported", "refresh_token"),
        ("response_types_supported", "code"),
    ):
        require(value in authorization.get(key, []), f"{key} must advertise {value}")


def main() -> int:
    failures = 0
    for name in ENDPOINTS:
        try:
            probe(name)
        except (ValueError, URLError, OSError) as error:
            print(f"{name}: {error}", file=sys.stderr)
            failures += 1
        else:
            print(
                f"{name}: 401 challenge, resource/issuer, PKCE S256, DCR, "
                "public clients, refresh tokens OK"
            )
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
