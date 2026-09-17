"""SQL identifier rendering shared by physical relationship planning."""
import re

SQL_DIALECTS = {"oracle", "sqlserver"}


def normalize_sql_dialect(value: str) -> str:
    """Return one of the supported deterministic SQL dialect identifiers."""
    normalized = (value or "").strip().lower()
    if normalized not in SQL_DIALECTS:
        raise ValueError(f"Unsupported SQL dialect: {value}")
    return normalized


def _sql_identifier(value: str, sql_dialect: str) -> str:
    """Render a physical identifier safely for the selected database dialect."""
    dialect = normalize_sql_dialect(sql_dialect)
    if dialect == "sqlserver":
        return f"[{value.replace(']', ']]')}]"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        return value
    return f'"{value.replace(chr(34), chr(34) * 2)}"'

