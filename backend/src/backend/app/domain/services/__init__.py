"""Shared deterministic domain services used by the API runtime."""

from pathlib import Path

_shared_services = Path(__file__).resolve().parents[5] / "app" / "domain" / "services"
if _shared_services.is_dir() and str(_shared_services) not in __path__:
    __path__.append(str(_shared_services))
