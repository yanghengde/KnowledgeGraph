import pytest

from src.graphstudio_sync.graphstudio_api import require_graphstudio_2026_1_ready


class _Response:
    def __init__(self, payload, *, text=None):
        self._payload = payload
        self.text = str(payload) if text is None else text
        self.ok = True
        self.status_code = 200

    def json(self):
        if isinstance(self._payload, ValueError):
            raise self._payload
        return self._payload


class _Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_accepts_graph_studio_2026_1_2_product_version() -> None:
    session = _Session(_Response({"serverVersion": "2026.1.2"}))

    result = require_graphstudio_2026_1_ready(session, "https://graphstudio.example")

    assert result == {"version": "2026.1.2"}
    assert session.calls[0][0].endswith("/util/serverVersion")


def test_accepts_graph_studio_api_6_3_version() -> None:
    result = require_graphstudio_2026_1_ready(
        _Session(_Response({"version": "6.3.0"})),
        "https://graphstudio.example",
    )

    assert result == {"version": "6.3.0"}


def test_rejects_server_that_is_still_starting() -> None:
    response = _Response(
        ValueError(),
        text="Altair Graph Studio Still Starting Application is still starting up.",
    )

    with pytest.raises(RuntimeError, match="尚未完成启动"):
        require_graphstudio_2026_1_ready(
            _Session(response),
            "https://graphstudio.example",
        )


def test_rejects_pre_2026_1_api_baseline() -> None:
    with pytest.raises(RuntimeError, match="不符合当前发布适配基线"):
        require_graphstudio_2026_1_ready(
            _Session(_Response({"version": "6.2.0"})),
            "https://graphstudio.example",
        )
