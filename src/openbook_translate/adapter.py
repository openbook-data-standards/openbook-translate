from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Inbound:
    source: str
    raw: bytes
    parsed: dict | None = None


@dataclass(frozen=True)
class Quarantine:
    inbound: Inbound | None
    reason: str
    document: dict | None = None


@dataclass(frozen=True)
class TranslateOk:
    documents: list[dict]


@dataclass(frozen=True)
class ReverseOk:
    raw: bytes
    parsed: dict | None = None


class Adapter(ABC):
    """One vendor dialect. Sync; one record per call."""

    source_id: str

    @abstractmethod
    def translate(self, inbound: Inbound) -> TranslateOk | Quarantine:
        ...

    @abstractmethod
    def reverse(self, document: dict) -> ReverseOk | Quarantine:
        ...
