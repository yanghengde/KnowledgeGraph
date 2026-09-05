#!/usr/bin/env python3
"""Read-only HTTPS diagnostics; no database access or account credentials."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import socket
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
import requests

from src.graphstudio_sync.config import normalize_graphstudio_url
from src.graphstudio_sync.transport import configure_graphstudio_tls


def diagnose(base_url: str, fingerprint: str | None, timeout: float = 8) -> dict:
    base = normalize_graphstudio_url(base_url)
    parts = urlsplit(base)
    if parts.scheme != "https":
        raise ValueError("HTTPS diagnosis requires an HTTPS URL")
    port = parts.port or 443
    result = {
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "endpoint": base,
        "certificatePolicy": "sha256_pin" if fingerprint else "system_ca",
        "remoteMutated": False,
        "credentialsSent": False,
    }
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(
            parts.hostname, port, type=socket.SOCK_STREAM)})
        result["dns"] = {
            "addresses": addresses,
            "benchmarkRangeDetected": any(
                ipaddress.ip_address(addr) in ipaddress.ip_network("198.18.0.0/15")
                for addr in addresses
            ),
        }
    except OSError:
        result["dns"] = {"error": "dns_resolution_failed"}
    try:
        with socket.create_connection((parts.hostname, port), timeout=timeout):
            result["tcp"] = {"connected": True}
    except OSError:
        result["tcp"] = {"connected": False}

    with requests.Session() as session:
        # Ignore both environment proxies and .netrc credentials. OS-level VPN
        # routing still applies. Never follow a redirect or include response bodies.
        session.trust_env = False
        configure_graphstudio_tls(session, base, fingerprint)
        try:
            with session.get(base + "/api/utils/serverVersion", timeout=timeout,
                             allow_redirects=False, stream=True) as response:
                result["https"] = {"verified": True, "httpStatus": response.status_code}
        except requests.exceptions.SSLError as exc:
            message = str(exc).lower()
            kind = ("tls_eof" if "eof" in message else
                    "certificate_mismatch" if "fingerprint" in message or "certificate_verify_failed" in message
                    else "tls_error")
            result["https"] = {"verified": False, "error": kind}
        except requests.exceptions.Timeout:
            result["https"] = {"verified": False, "error": "timeout"}
        except requests.exceptions.RequestException:
            result["https"] = {"verified": False, "error": "connection_error"}
    # Verified HTTP (including 401) proves transport only, not publication readiness.
    result["publicationReadinessChecked"] = False
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    result = diagnose(os.environ["GRAPHSTUDIO_BASE_URL"],
                      os.getenv("GRAPHSTUDIO_TLS_FINGERPRINT") or None)
    report = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if result["https"]["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
