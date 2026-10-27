"""Expose Sharad's framework-independent domain package to the app runtime.

The domain implementation lives in ``backend/app`` so it can also be used by
its standalone tests. Extend this runtime package path instead of copying the
engine into the HTTP application.
"""

from pathlib import Path

_shared_domain = Path(__file__).resolve().parents[4] / "app" / "domain"
if _shared_domain.is_dir() and str(_shared_domain) not in __path__:
    __path__.append(str(_shared_domain))
