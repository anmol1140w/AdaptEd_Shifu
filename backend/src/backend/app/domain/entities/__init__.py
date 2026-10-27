"""Shared domain entities used by the API runtime."""

from pathlib import Path

_shared_entities = Path(__file__).resolve().parents[5] / "app" / "domain" / "entities"
if _shared_entities.is_dir() and str(_shared_entities) not in __path__:
    __path__.append(str(_shared_entities))
