from __future__ import annotations

from abc import ABC, abstractmethod

from openbook_translate.types import Documents, Quarantine, Vendor


class Translator(ABC):
    """One record, two sync methods. Adapter name is the identifier.propertyID."""

    name: str

    @abstractmethod
    def translate(
        self,
        raw: bytes,
        *,
        source_id: str,
        parsed: dict | None = None,
    ) -> Documents | Quarantine:
        """Vendor → OpenBook documents, or quarantine (raw + reason)."""

    @abstractmethod
    def reverse(self, document: dict) -> Vendor | Quarantine:
        """OpenBook document → vendor bytes + optional dict."""
