import pytest

from src.graphstudio_sync.entity_labels import (
    resolve_entity_label,
    suggest_label_template,
    validate_presentation,
)


def _properties(*names):
    return [
        {"targetName": name, "sourceName": name, "dataType": "String", "published": True}
        for name in names
    ]


def test_auto_label_combines_name_and_revision() -> None:
    properties = _properties("name", "revision", "description")

    assert suggest_label_template(properties) == "{name} / Rev {revision}"
    assert resolve_entity_label(
        {"targetName": "Workflow", "labelMode": "auto"},
        properties,
        {"name": "AssemblyFlow", "revision": "03"},
    ) == "AssemblyFlow / Rev 03"


def test_template_falls_back_to_business_key_when_a_value_is_missing() -> None:
    properties = _properties("name", "revision")

    label = resolve_entity_label(
        {
            "targetName": "Workflow", "labelMode": "template",
            "labelTemplate": "{name} / Rev {revision}",
            "labelFallbacks": ["$businessKey", "$primaryKey"],
        },
        properties,
        {"name": "AssemblyFlow", "revision": None},
        business_key={"WorkflowName": "AssemblyFlow"},
        primary_key={"WorkflowId": "123"},
    )

    assert label == "AssemblyFlow"


def test_presentation_rejects_unpublished_or_navigation_fields() -> None:
    properties = [
        {"targetName": "name", "dataType": "String", "published": False},
        {"targetName": "product", "dataType": "Navigation", "published": True},
    ]

    with pytest.raises(ValueError, match="not a published scalar"):
        validate_presentation({"labelMode": "field", "labelField": "product"}, properties)


def test_presentation_normalizes_field_case_and_search_fields() -> None:
    result = validate_presentation({
        "labelMode": "field",
        "labelField": "NAME",
        "labelFallbacks": ["$businessKey", "$primaryKey"],
        "searchFields": ["DESCRIPTION"],
    }, _properties("name", "description"))

    assert result["labelField"] == "name"
    assert result["searchFields"] == ["description"]
