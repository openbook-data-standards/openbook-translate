from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Documents:
    """One successful map: one or more OpenBook documents."""

    documents: tuple[dict, ...]

    def __post_init__(self) -> None:
        if not self.documents:
            raise ValueError("Documents must not be empty; return Quarantine for unmapped")


@dataclass(frozen=True)
class Quarantine:
    """Unmapped inbound (or a document that cannot reverse). Not a skip."""

    raw: bytes
    reason: str


@dataclass(frozen=True)
class Vendor:
    """Outbound vendor form of one OpenBook document."""

    raw: bytes
    parsed: dict | None = None
