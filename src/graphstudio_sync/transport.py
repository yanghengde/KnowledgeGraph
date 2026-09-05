"""HTTPS transport with optional host-scoped SHA-256 certificate pinning."""

import re

import requests
from requests.adapters import HTTPAdapter

from .config import normalize_graphstudio_url


class FingerprintAdapter(HTTPAdapter):
    def __init__(self, fingerprint: str):
        self.fingerprint = fingerprint.replace(":", "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", self.fingerprint):
            raise ValueError("Graph Studio certificate fingerprint must be SHA-256")
        super().__init__()

    def init_poolmanager(self, *args, **kwargs):
        kwargs["assert_fingerprint"] = self.fingerprint
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **kwargs):
        kwargs["assert_fingerprint"] = self.fingerprint
        return super().proxy_manager_for(proxy, **kwargs)

    def cert_verify(self, conn, url, verify, cert):
        # urllib3 verifies the exact certificate instead of its public CA chain.
        # This override is only mounted on the configured Graph Studio origin.
        super().cert_verify(conn, url, False, cert)

    def build_connection_pool_key_attributes(self, request, verify, cert=None):
        host, pool = super().build_connection_pool_key_attributes(request, False, cert)
        pool["assert_fingerprint"] = self.fingerprint
        return host, pool


def configure_graphstudio_tls(session, base_url: str, fingerprint: str | None):
    if fingerprint:
        base = normalize_graphstudio_url(base_url)
        if not base.startswith("https://"):
            raise ValueError("Certificate pinning requires a Graph Studio HTTPS URL")
        session.mount(base + "/", FingerprintAdapter(fingerprint))
    return session
