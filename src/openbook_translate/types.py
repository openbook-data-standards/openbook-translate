from __future__ import annotations

import base64
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any

# Quarantine reason vocabulary. ``reason`` is one of these; the free text goes
# in ``detail`` so a service can count quarantines by reason across adapters.
UNMAPPED_SPORT = "unmapped-sport"
UNMAPPED_LEAGUE = "unmapped-league"
UNMAPPED_MARKET_TYPE = "unmapped-market-type"
UNMAPPED_SEGMENT = "unmapped-segment"
UNMAPPED_PARTICIPANT = "unmapped-participant"
SCHEMA_INVALID = "schema-invalid"
PARSE_ERROR = "parse-error"
OTHER = "other"

REASONS: frozenset[str] = frozenset(
    {
        UNMAPPED_SPORT,
        UNMAPPED_LEAGUE,
        UNMAPPED_MARKET_TYPE,
        UNMAPPED_SEGMENT,
        UNMAPPED_PARTICIPANT,
        SCHEMA_INVALID,
        PARSE_ERROR,
        OTHER,
    }
)


@dataclass(frozen=True)
class Documents:
    """One successful map: one or more OpenBook documents."""

    documents: tuple[dict, ...]

    def __post_init__(self) -> None:
        if not self.documents:
            raise ValueError("Documents must not be empty; return Quarantine for unmapped")


@dataclass(frozen=True)
class Quarantine:
    """Unmapped inbound (or a document that cannot reverse). Not a skip.

    ``raw`` and ``reason`` are positional as before. The rest is optional
    context a service can persist: which feed (``source_id``), which adapter,
    free-text or structured ``detail``, and when it arrived.
    """

    raw: bytes
    reason: str
    source_id: str | None = None
    adapter: str | None = None
    detail: str | dict[str, Any] | None = None
    received_at: str | datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe form; ``raw`` is base64."""
        received = self.received_at
        if isinstance(received, datetime):
            received = received.isoformat()
        return {
            "raw": base64.b64encode(self.raw).decode("ascii"),
            "reason": self.reason,
            "source_id": self.source_id,
            "adapter": self.adapter,
            "detail": self.detail,
            "received_at": received,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Quarantine:
        """Inverse of :meth:`to_dict`. Unknown keys are ignored."""
        known = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in known and k != "raw"}
        raw = data.get("raw", b"")
        if isinstance(raw, str):
            raw = base64.b64decode(raw)
        return cls(raw=raw, **kwargs)


@dataclass(frozen=True)
class Vendor:
    """Outbound vendor form of one OpenBook document."""

    raw: bytes
    parsed: dict | None = None


__all__ = [
    "Documents",
    "OTHER",
    "PARSE_ERROR",
    "Quarantine",
    "REASONS",
    "SCHEMA_INVALID",
    "UNMAPPED_LEAGUE",
    "UNMAPPED_MARKET_TYPE",
    "UNMAPPED_PARTICIPANT",
    "UNMAPPED_SEGMENT",
    "UNMAPPED_SPORT",
    "Vendor",
]
