from contextlib import nullcontext
from types import SimpleNamespace

import pytest
import requests

from scripts.check import diagnose_graphstudio_https as diagnostic


@pytest.mark.parametrize("error, expected", [
    (None, {"verified": True, "httpStatus": 401}),
    (requests.exceptions.SSLError("UNEXPECTED_EOF_WHILE_READING"),
     {"verified": False, "error": "tls_eof"}),
    (requests.exceptions.SSLError("Fingerprints did not match"),
     {"verified": False, "error": "certificate_mismatch"}),
])
def test_diagnosis_sends_no_credentials_or_redirects_and_preserves_tls_policy(monkeypatch, error, expected):
    calls = []
    class Session:
        trust_env = True
        def get(self, url, **kwargs):
            assert self.trust_env is False
            assert kwargs == {"timeout": 8, "allow_redirects": False, "stream": True}
            assert url == "https://example.test:8443/api/utils/serverVersion"
            if error:
                raise error
            return nullcontext(SimpleNamespace(status_code=401))
        def __enter__(self):
            return self
        def __exit__(self, *args):
            calls.append("closed")
    monkeypatch.setattr(diagnostic.requests, "Session", Session)
    monkeypatch.setattr(diagnostic, "configure_graphstudio_tls", lambda session, base, pin: calls.append((base, pin)))
    monkeypatch.setattr(diagnostic.socket, "getaddrinfo", lambda *a, **k: [(None, None, None, None, ("198.18.1.121", 8443))])
    monkeypatch.setattr(diagnostic.socket, "create_connection", lambda *a, **k: nullcontext())
    result = diagnostic.diagnose("https://example.test:8443", "a" * 64)
    assert result["https"] == expected
    assert result["dns"]["benchmarkRangeDetected"] is True
    assert result["credentialsSent"] is False
    assert result["remoteMutated"] is False
    assert result["publicationReadinessChecked"] is False
    assert calls == [("https://example.test:8443", "a" * 64), "closed"]


def test_diagnosis_rejects_plain_http():
    with pytest.raises(ValueError, match="HTTPS"):
        diagnostic.diagnose("http://example.test", None)
