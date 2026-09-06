"""Deterministic relationship names derived from physical field names."""
import re

def relation_name(property_name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", property_name).upper()
    if snake.startswith("HAS_"):
        return snake
    return f"HAS_{snake}"
