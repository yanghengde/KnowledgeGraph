import pytest

from src.graphstudio_sync.graphstudio_api import require_graphstudio_2026_1_ready


class _Response:
    def __init__(self, payload, *, text=None, status_code=200):
        self._payload = payload
        self.text = str(payload) if text is None else text
        self.status_code = status_code
        self.ok = 200 <= status_code < 400

    def json(self):
        if isinstance(self._payload, ValueError):
            raise self._payload
        return self._payload


class _Session:
    def __init__(self, response, routes=None):
        self.response = response
        self.routes = routes or {}
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        for suffix, response in self.routes.items():
            if url.endswith(suffix):
                return response
        return self.response


def test_accepts_graph_studio_2026_1_2_product_version() -> None:
    session = _Session(_Response({"serverVersion": "2026.1.2"}))

    result = require_graphstudio_2026_1_ready(session, "https://graphstudio.example")

    assert result == {"version": "2026.1.2"}
    assert session.calls[0][0].endswith("/api/utils/serverVersion")


def test_accepts_graph_studio_api_6_3_version() -> None:
    result = require_graphstudio_2026_1_ready(
        _Session(_Response({"version": "6.3.0"})),
        "https://graphstudio.example",
    )

    assert result == {"version": "6.3.0"}


def test_accepts_6_3_capabilities_when_version_route_is_misrouted() -> None:
    version_response = _Response(
        ValueError(),
        text=(
            '<!doctype html><html data-template-version="1.0">'
            "Altair Graph Studio Still Starting Application is still starting up.</html>"
        ),
    )
    session = _Session(
        version_response,
        routes={
            "/api/graphmarts": _Response([]),
            "/api/models": _Response([]),
            "/api/datasets": _Response([]),
            "/api/graphmarts/urn%3Agraphmart%3Atarget": _Response(
                {"uri": "urn:graphmart:target"}
            ),
            (
                "/api/runconfigs/"
                "urn%3Agraphmart%3Atarget_RunConfiguration-Design"
            ): _Response({"runConfigurationAssumeDisabled": True}),
            "/api/fileconnections/urn%3Afile%3Ashared": _Response({
                "uri": "urn:file:shared",
                "fileConnectionSupportsGlobalLoad": True,
            }),
            "/api/fileconnections/urn%3Afile%3Ashared/files": _Response([]),
        },
    )

    result = require_graphstudio_2026_1_ready(
        session,
        "https://graphstudio.example",
        graphmart_uri="urn:graphmart:target",
        file_connection="urn:file:shared",
        file_path="Opcenter2607/CamstarSync",
    )

    assert result == {
        "version": "6.3-compatible",
        "source": "capabilityProbe",
    }
    file_call = next(call for call in session.calls if call[0].endswith("/files"))
    assert file_call[1]["params"] == {"path": "Opcenter2607/CamstarSync"}


def test_rejects_starting_page_when_flds_capability_is_unavailable() -> None:
    version_response = _Response(
        ValueError(),
        text="Altair Graph Studio Still Starting Application is still starting up.",
    )
    session = _Session(
        version_response,
        routes={
            "/api/graphmarts": _Response([]),
            "/api/models": _Response([]),
            "/api/datasets": _Response([]),
            "/api/fileconnections/urn%3Afile%3Ashared": _Response({
                "uri": "urn:file:shared",
                "fileConnectionSupportsGlobalLoad": True,
            }),
            "/api/fileconnections/urn%3Afile%3Ashared/files": _Response(
                {"error": "not ready"}, status_code=503
            ),
        },
    )

    with pytest.raises(RuntimeError, match="filePath=HTTP 503"):
        require_graphstudio_2026_1_ready(
            session,
            "https://graphstudio.example",
            file_connection="urn:file:shared",
            file_path="Opcenter2607/CamstarSync",
        )


def test_rejects_pre_2026_1_api_baseline() -> None:
    with pytest.raises(RuntimeError, match="不符合当前发布适配基线"):
        require_graphstudio_2026_1_ready(
            _Session(_Response({"version": "6.2.0"})),
            "https://graphstudio.example",
        )


def test_rejects_file_store_not_enabled_for_graph_lakehouse() -> None:
    session = _Session(
        _Response({"serverVersion": "2026.1.2"}),
        routes={
            "/api/graphmarts": _Response([]),
            "/api/models": _Response([]),
            "/api/datasets": _Response([]),
            "/api/fileconnections/urn%3Afile%3Alocal": _Response({
                "uri": "urn:file:local",
                "fileConnectionSupportsGlobalLoad": False,
            }),
            "/api/fileconnections/urn%3Afile%3Alocal/files": _Response([]),
        },
    )

    with pytest.raises(
        RuntimeError,
        match=r"REST API 2026\.1\.2.*fileConnectionSupportsGlobalLoad=false",
    ):
        require_graphstudio_2026_1_ready(
            session,
            "https://graphstudio.example",
            file_connection="urn:file:local",
            file_path="Opcenter2607/CamstarSync",
        )


def test_rejects_graph_secured_file_staging_before_dataset_upload() -> None:
    session = _Session(
        _Response({"serverVersion": "2026.1.2"}),
        routes={
            "/api/graphmarts": _Response([]),
            "/api/models": _Response([]),
            "/api/datasets": _Response([]),
            "/api/fileconnections/urn%3Afile%3Astaging": _Response({
                "uri": "urn:file:staging",
                "fileConnectionSupportsGlobalLoad": True,
                "fileConnectionGraphSecured": True,
            }),
            "/api/fileconnections/urn%3Afile%3Astaging/files": _Response(
                ValueError(), status_code=500
            ),
        },
    )

    with pytest.raises(
        RuntimeError,
        match=r"fileConnectionGraphSecured=true.*does not accept the required graph context",
    ):
        require_graphstudio_2026_1_ready(
            session,
            "https://graphstudio.example",
            file_connection="urn:file:staging",
            file_path="CamstarSync",
        )

    assert not any(call[0].endswith("/files") for call in session.calls)
