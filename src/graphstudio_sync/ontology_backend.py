"""Explicit backend selection. PostgreSQL never silently falls back to Neo4j."""
from functools import wraps
import os


def backend(settings=None):
    value = getattr(settings, "ontology_backend", "neo4j") if settings is not None else os.getenv("ONTOLOGY_BACKEND", "neo4j")
    if value not in {"postgres", "neo4j"}:
        raise ValueError("ONTOLOGY_BACKEND must be postgres or neo4j")
    return value


def postgres_backend(function):
    """Keep legacy entry points while routing the selected storage implementation."""
    @wraps(function)
    def dispatch(settings, *args, **kwargs):
        if backend(settings) == "postgres":
            from . import publish_ontology_postgres
            return getattr(publish_ontology_postgres, function.__name__)(settings, *args, **kwargs)
        return function(settings, *args, **kwargs)
    return dispatch
