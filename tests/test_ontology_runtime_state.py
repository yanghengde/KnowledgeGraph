from src.ontology import runtime_state


def test_empty_baseline_state_round_trip(monkeypatch, tmp_path):
    state_file = tmp_path / "ontology_graph_state.json"
    monkeypatch.setattr(runtime_state, "GRAPH_STATE_FILE", state_file)

    assert runtime_state.is_empty_baseline_mode() is False

    saved = runtime_state.mark_graph_cleared(nodes=11, relationships=17)
    assert saved["baselineMode"] == "empty"
    assert saved["clearedCounts"] == {"nodes": 11, "relationships": 17}
    assert runtime_state.is_empty_baseline_mode() is True

    runtime_state.enable_curated_baseline()
    assert runtime_state.is_empty_baseline_mode() is False
