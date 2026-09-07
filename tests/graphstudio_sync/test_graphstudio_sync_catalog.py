from src.graphstudio_sync.catalog import _class_tokens


def test_class_tokens_align_abstract_and_concrete_table_names() -> None:
    assert "setupaccess" in _class_tokens("A_SetupAccess")
    assert _class_tokens("A_SetupAccess") & _class_tokens("SetupAccess")
