"""Declarative vendor -> OpenBook mapping tables, so an adapter is data, not code.

A table is JSON (a path or an already-loaded dict)::

    {
      "adapter": "acme",
      "sport":       [{"vendor": "SOCC", "id": "sport:soccer", "name": "Soccer"}],
      "segment":     [{"vendor": "1H",   "id": "segment:soccer:1st-half"}],
      "market_type": [{"vendor": "ML",   "id": "market:moneyline"}],
      "side":        [{"vendor": "1",    "id": "home"}]
    }

Every ``id`` must be known to :mod:`openbook_translate.vocab` for its kind and
vendor keys must be unique per kind; both are checked at load. ``x`` on an
entry is free extra data handed back on a hit. A miss returns :class:`Unmapped`
carrying the catch-all id and the ``x_`` field an adapter stamps the vendor
value into (``x_acmeSportId``), so nothing is lost and gaps can be counted.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openbook_translate import vocab

KINDS = ("sport", "segment", "market_type", "side")

_CATCH_ALL = {
    "sport": vocab.SPORT_UNKNOWN,
    "segment": vocab.SEGMENT_UNKNOWN,
    "market_type": vocab.MARKET_UNKNOWN,
    "side": "other",
}

_KNOWN = {
    "sport": vocab.is_known_sport,
    "segment": vocab.is_known_segment,
    "market_type": vocab.is_known_market,
    "side": vocab.is_known_side,
}

_X_SUFFIX = {
    "sport": "SportId",
    "segment": "SegmentId",
    "market_type": "MarketTypeId",
    "side": "SideId",
}


class TableError(ValueError):
    """The table is malformed. ``problems`` lists every issue found."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class Mapped:
    kind: str
    vendor: str
    id: str
    name: str | None = None
    x: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Unmapped:
    kind: str
    vendor: str
    id: str
    """The catch-all id for this kind (``sport:unknown`` and friends)."""
    x_field: str
    """Extension property to stamp the vendor value into, e.g. ``x_acmeSportId``."""

    def stamp(self, document: dict) -> dict:
        """Return ``document`` with the vendor value on ``x_field`` (shallow copy)."""
        out = dict(document)
        out[self.x_field] = self.vendor
        return out


def catch_all(kind: str) -> str:
    return _CATCH_ALL[kind]


def x_field_name(adapter: str, kind: str) -> str:
    """``("acme-feeds", "sport")`` -> ``x_acmeFeedsSportId``."""
    parts = [p for p in re.split(r"[^0-9A-Za-z]+", adapter) if p]
    head = parts[0][:1].lower() + parts[0][1:] if parts else "adapter"
    camel = head + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    return f"x_{camel}{_X_SUFFIX[kind]}"


@dataclass(frozen=True)
class MappingTable:
    adapter: str
    entries: dict[str, dict[str, Mapped]]

    @classmethod
    def load(cls, source: str | Path | dict, *, adapter: str | None = None) -> MappingTable:
        """Read and validate a table. ``adapter`` overrides the file's own."""
        if isinstance(source, (str, Path)):
            data = json.loads(Path(source).read_text(encoding="utf-8"))
        else:
            data = source
        problems: list[str] = []
        if not isinstance(data, dict):
            raise TableError(["table must be a JSON object"])
        name = adapter or data.get("adapter")
        if not isinstance(name, str) or not name:
            problems.append("adapter name missing: set \"adapter\" in the table or pass adapter=")
            name = "adapter"
        entries: dict[str, dict[str, Mapped]] = {k: {} for k in KINDS}
        for key, rows in data.items():
            if key == "adapter":
                continue
            if key not in KINDS:
                problems.append(f"unknown kind {key!r} (expected one of {', '.join(KINDS)})")
                continue
            if not isinstance(rows, list):
                problems.append(f"{key}: must be a list of entries")
                continue
            for i, row in enumerate(rows):
                where = f"{key}[{i}]"
                if not isinstance(row, dict):
                    problems.append(f"{where}: entry must be an object")
                    continue
                vendor = row.get("vendor")
                ident = row.get("id")
                if vendor is None or vendor == "":
                    problems.append(f"{where}: missing \"vendor\"")
                    continue
                vendor = str(vendor)
                if not isinstance(ident, str) or not ident:
                    problems.append(f"{where}: missing \"id\"")
                    continue
                if not _KNOWN[key](ident):
                    problems.append(f"{where}: {ident!r} is not a known {key} id")
                if vendor in entries[key]:
                    problems.append(f"{where}: duplicate vendor key {vendor!r}")
                    continue
                x = row.get("x") or {}
                if not isinstance(x, dict):
                    problems.append(f"{where}: \"x\" must be an object")
                    x = {}
                display = row.get("name")
                entries[key][vendor] = Mapped(
                    kind=key,
                    vendor=vendor,
                    id=ident,
                    name=display if isinstance(display, str) else None,
                    x=dict(x),
                )
        if problems:
            raise TableError(problems)
        return cls(adapter=name, entries=entries)

    def lookup(self, kind: str, vendor_value: object) -> Mapped | Unmapped:
        """The mapping for one vendor value (matched as a string), or an :class:`Unmapped`."""
        if kind not in KINDS:
            raise KeyError(kind)
        vendor = str(vendor_value)
        hit = self.entries[kind].get(vendor)
        if hit is not None:
            return hit
        return Unmapped(
            kind=kind,
            vendor=vendor,
            id=_CATCH_ALL[kind],
            x_field=x_field_name(self.adapter, kind),
        )

    def kinds(self) -> list[str]:
        return [k for k in KINDS if self.entries[k]]

    def __len__(self) -> int:
        return sum(len(v) for v in self.entries.values())


__all__ = ["KINDS", "Mapped", "MappingTable", "TableError", "Unmapped", "catch_all", "x_field_name"]
