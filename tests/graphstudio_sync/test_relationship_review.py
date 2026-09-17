from copy import deepcopy
import pytest
from src.graphstudio_sync.modeling import relationship_review as review
from src.graphstudio_sync.modeling.semantic_mapping import candidate_preview
from tests.graphstudio_sync.test_semantic_mapping import draft


def test_review_is_frozen_with_candidate_and_missing_review_blocks(draft):
    result = candidate_preview(draft)
    assert result["payload"]["classes"][0]["_semanticMapping"]["relationshipReviews"]["category"]["actor"] == "reviewer"
    draft["design"]["relationshipReviews"] = {}
    assert any("业务含义" in b for b in candidate_preview(draft)["blockers"])


@pytest.mark.parametrize("patch", [{"description": "新的业务定义"}, {"chineseName": "新的名称"}, {"role": "event"}])
def test_definition_changes_invalidate_confirmation_and_preserve_history(draft, patch):
    before = deepcopy(draft)
    design = {**draft["design"], **patch}
    saved = review.preserve_records(draft, design)
    assert saved["relationshipReviews"] == {}
    assert saved["relationshipReviewHistory"] == before["design"]["relationshipReviewHistory"]
    assert draft == before


def test_unselect_and_reselect_requires_new_review(draft):
    design = deepcopy(draft["design"])
    design["fields"]["category"] = "excluded"
    draft["design"] = review.preserve_records(draft, design)
    draft["design"]["fields"]["category"] = "relationship"
    assert review.current_review(draft, draft["fields"][-1]) is None


def test_regular_save_cannot_forge_review_or_erase_history(draft):
    forged = deepcopy(draft["design"])
    forged["relationshipReviews"]["category"]["actor"] = "forged"
    forged["relationshipReviewHistory"] = []
    saved = review.preserve_records(draft, forged)
    assert saved["relationshipReviews"]["category"]["actor"] == "reviewer"
    assert len(saved["relationshipReviewHistory"]) == 1
    saved["notes"] = "仅修改设计笔记"
    assert review.preserve_records(draft, saved)["relationshipReviews"]


def test_source_changes_and_blank_reviews_rejected(draft):
    draft["snapshotId"] = "changed"
    assert review.current_review(draft, draft["fields"][-1]) is None
    with pytest.raises(ValueError): review.confirm(draft, "category", " ", "reviewer")
    with pytest.raises(ValueError): review.confirm(draft, "name", "说明", "reviewer")


def test_review_store_rejects_stale_revision_before_writing(draft):
    import json
    from src.graphstudio_sync.modeling.semantic_mapping import MappingStore
    class Connection:
        writes = []
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql, params): self.writes.append((str(sql), params))
    connection = Connection()
    store = MappingStore(type("Engine", (), {"begin": lambda self: connection})())
    store.detail = lambda *args, **kwargs: deepcopy(draft)
    with pytest.raises(RuntimeError):
        store.review_relationship("d1", draft["revision"] - 1, "category", "新的含义", "reviewer")
    assert not connection.writes
    result = store.review_relationship("d1", draft["revision"], "category", "新的含义", "reviewer")
    assert result["revision"] == draft["revision"] + 1
    saved = json.loads(connection.writes[0][1]["design"])
    assert len(saved["relationshipReviewHistory"]) == 2
    assert saved["relationshipReviews"]["category"]["meaning"] == "新的含义"
