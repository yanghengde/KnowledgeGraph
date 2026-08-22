"""Deterministic presentation labels for published ontology instances."""

from __future__ import annotations

import re
from typing import Any


LABEL_MODES = {"auto", "field", "template"}
SPECIAL_FIELDS = {"$businessKey", "$primaryKey"}
_NON_SCALAR_TYPES = {"navigation", "array", "subentity", "subentitylist"}
_TOKEN = re.compile(r"\{([^{}]+)\}")


def published_scalar_names(properties: list[dict[str, Any]]) -> list[str]:
    """Return stable target names that are safe to use in a display label."""
    return [
        str(item.get("targetName") or item.get("sourceName") or "").strip()
        for item in properties
        if item.get("published", True)
        and str(item.get("dataType") or "string").casefold() not in _NON_SCALAR_TYPES
        and str(item.get("targetName") or item.get("sourceName") or "").strip()
    ]


def suggest_label_template(properties: list[dict[str, Any]]) -> str | None:
    """Suggest a small, explainable label template from published properties."""
    names = published_scalar_names(properties)
    by_fold = {name.casefold(): name for name in names}
    display_name = by_fold.get("displayname")
    if display_name:
        return f"{{{display_name}}}"
    name = by_fold.get("name")
    revision = by_fold.get("revision")
    if name and revision:
        return f"{{{name}}} / Rev {{{revision}}}"
    if name:
        return f"{{{name}}}"
    for suffix in ("name", "code", "number", "no"):
        candidate = next(
            (item for item in names if item.casefold().endswith(suffix)), None,
        )
        if candidate:
            return f"{{{candidate}}}"
    description = by_fold.get("description")
    return f"{{{description}}}" if description else None


def template_tokens(template: str | None) -> list[str]:
    return list(dict.fromkeys(match.strip() for match in _TOKEN.findall(template or "") if match.strip()))


def validate_presentation(
    config: dict[str, Any], properties: list[dict[str, Any]],
) -> dict[str, Any]:
    """Normalize and validate the deliberately small presentation DSL."""
    mode = str(config.get("labelMode") or "auto")
    if mode not in LABEL_MODES:
        raise ValueError("labelMode must be auto, field or template")
    available = published_scalar_names(properties)
    canonical = {item.casefold(): item for item in available}

    def normalize_field(value: Any, *, allow_special: bool = False) -> str:
        field = str(value or "").strip()
        if allow_special and field in SPECIAL_FIELDS:
            return field
        resolved = canonical.get(field.casefold())
        if not resolved:
            raise ValueError(f"Display field is not a published scalar property: {field}")
        return resolved

    field = str(config.get("labelField") or "").strip()
    template = str(config.get("labelTemplate") or "").strip()
    if len(template) > 500:
        raise ValueError("labelTemplate exceeds 500 characters")
    if mode == "field":
        field = normalize_field(field)
    elif mode == "template":
        tokens = template_tokens(template)
        if not template or not tokens:
            raise ValueError("Template mode requires at least one {property} placeholder")
        for token in tokens:
            normalize_field(token, allow_special=True)

    fallbacks = [
        normalize_field(item, allow_special=True)
        for item in dict.fromkeys(config.get("labelFallbacks") or [])
    ]
    search_fields = [
        normalize_field(item)
        for item in dict.fromkeys(config.get("searchFields") or [])
    ]
    return {
        "labelMode": mode,
        "labelField": field or None,
        "labelTemplate": template or None,
        "labelFallbacks": fallbacks,
        "searchFields": search_fields,
        "emitRdfsLabel": bool(config.get("emitRdfsLabel", True)),
    }


def _value_map(properties: list[dict[str, Any]], values: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in properties:
        source = str(item.get("sourceName") or "").strip()
        target = str(item.get("targetName") or source).strip()
        value = values.get(source, values.get(target))
        if target:
            result[target.casefold()] = value
        if source:
            result[source.casefold()] = value
    return result


def _text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, list):
        members = [str(item).strip() for item in value if item not in (None, "")]
        return ", ".join(members) or None
    if isinstance(value, dict):
        members = [str(item).strip() for item in value.values() if item not in (None, "")]
        return " / ".join(members) or None
    return str(value).strip() or None


def resolve_entity_label(
    ontology_class: dict[str, Any],
    properties: list[dict[str, Any]],
    values: dict[str, Any],
    *,
    business_key: dict[str, Any] | None = None,
    primary_key: dict[str, Any] | None = None,
) -> str:
    """Resolve one human-facing label while keeping the instance URI ID-based."""
    mapped = _value_map(properties, values)

    def field_value(field: str) -> str | None:
        if field == "$businessKey":
            return _text(business_key)
        if field == "$primaryKey":
            return _text(primary_key)
        return _text(mapped.get(field.casefold()))

    def render(template: str | None) -> str | None:
        tokens = template_tokens(template)
        if not template or not tokens:
            return None
        replacements = {token: field_value(token) for token in tokens}
        if any(value is None for value in replacements.values()):
            return None
        rendered = _TOKEN.sub(lambda match: replacements[match.group(1).strip()] or "", template)
        return rendered.strip() or None

    mode = str(ontology_class.get("labelMode") or "auto")
    label = None
    if mode == "field":
        label = field_value(str(ontology_class.get("labelField") or ""))
    elif mode == "template":
        label = render(str(ontology_class.get("labelTemplate") or ""))
    else:
        label = render(suggest_label_template(properties))
    if label:
        return label

    fallbacks = ontology_class.get("labelFallbacks") or [
        "name", "description", "$businessKey", "$primaryKey",
    ]
    for field in fallbacks:
        label = field_value(str(field))
        if label:
            return label
    target = str(ontology_class.get("targetName") or "Entity")
    identifier = _text(primary_key) or "unidentified"
    return f"{target} {identifier}"
