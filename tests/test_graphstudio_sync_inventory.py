from src.graphstudio_sync.inventory import _physical_candidates, normalize_identifier


def test_normalize_identifier_is_case_and_separator_insensitive() -> None:
    assert normalize_identifier("Mfg_Order-ID") == "mfgorderid"


def test_navigation_candidates_strip_common_prefix_and_id_suffix() -> None:
    candidates = _physical_candidates("ES_ProductDefId", navigation=True)
    assert "product" in candidates
    assert "productdefid" in candidates


def test_data_property_candidates_do_not_strip_id_suffix() -> None:
    candidates = _physical_candidates("IconId", navigation=False)
    assert candidates == {"iconid"}
