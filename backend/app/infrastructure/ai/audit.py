"""In-memory audit adapter for local AI integration tests."""

from __future__ import annotations

from collections.abc import Mapping

from ...application.ports.ai import AIAuditEvent, AIAuditPort


class InMemoryAIAudit(AIAuditPort):
    """Store generation and fallback metadata for local inspection."""

    def __init__(self, *, prefix: str = "ai-audit") -> None:
        if not prefix.strip():
            raise ValueError("audit ID prefix must not be empty")
        self._prefix = prefix
        self._next_number = 1
        self._events: dict[str, AIAuditEvent] = {}

    def record(self, event: AIAuditEvent) -> str:
        event_id = f"{self._prefix}-{self._next_number}"
        self._next_number += 1
        self._events[event_id] = event
        return event_id

    @property
    def events(self) -> Mapping[str, AIAuditEvent]:
        """Return a defensive view of recorded audit events."""

        return dict(self._events)
