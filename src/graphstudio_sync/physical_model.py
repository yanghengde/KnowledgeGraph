"""Complete physical catalog views; never apply ontology field exclusions."""


def physical_fields(rows):
    """Collapse repeated inherited declarations of the same physical column.

    The snapshot retains the original rows. FK evidence wins in the view,
    matching the CSV validator's precedence, while identity flags are retained.
    """
    selected = {}
    for row in rows:
        name = row["FieldName"]
        old = selected.get(name)
        def priority(value):
            return (str(value.get("IsForeignKey", "")).lower() == "true" and bool(value.get("FKTableName")),
                    str(value.get("IsForeignKey", "")).lower() == "true",
                    str(value.get("IsList", "")).lower() == "true")
        preferred = row if old is None or priority(row) > priority(old) else old
        selected[name] = {**preferred}
        if str(row.get("IsPrimaryKey", "")).lower() == "true" or old and str(old.get("IsPrimaryKey", "")).lower() == "true":
            selected[name]["IsPrimaryKey"] = "True"
    return list(selected.values())
