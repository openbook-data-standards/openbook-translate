"""OpenBook controlled vocabularies, parsed from the vendored spec tables.

``sports.md``, ``segments.md`` and ``market_types.md`` ship as package data and
are parsed at import. The backticked first column of every table row is the id.
Catch-alls are exactly ``sport:unknown``, ``segment:unknown:unknown`` and
``market:unknown`` (Q34); consumers MUST still accept unrecognised values, so
these helpers never raise on an unknown id: they return the catch-all.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from openbook_translate.spec import schema, vocabulary_text

SPORT_UNKNOWN = "sport:unknown"
SEGMENT_UNKNOWN = "segment:unknown:unknown"
MARKET_UNKNOWN = "market:unknown"

_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|(.*)\|\s*$")
_PARAM = re.compile(r"<[a-z]>")


@dataclass(frozen=True)
class MarketType:
    id: str
    name: str
    shape: str
    category: str
    sides: str
    description: str


@dataclass(frozen=True)
class SegmentFamily:
    """A numbered id family such as ``segment:baseball:inning-<n>``."""

    pattern: str
    regex: re.Pattern[str]
    name: str

    def matches(self, segment_id: str) -> bool:
        return self.regex.fullmatch(segment_id) is not None


def _rows(text: str) -> list[list[str]]:
    """Every table row whose first cell is a backticked id -> stripped cells."""
    out = []
    for line in text.splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        rest = [c.strip() for c in m.group(2).split("|")]
        out.append([m.group(1).strip(), *rest])
    return out


def _parse_sports() -> tuple[frozenset[str], dict[str, str], frozenset[str]]:
    sports: dict[str, str] = {}
    disciplines: set[str] = set()
    for cells in _rows(vocabulary_text("sports.md")):
        ident = cells[0]
        if ident.startswith("sport:"):
            sports[ident] = cells[1] if len(cells) > 1 else ident
        elif ":" in ident:
            disciplines.add(ident)
    return frozenset(sports), sports, frozenset(disciplines)


def _family_regex(pattern: str) -> re.Pattern[str]:
    parts = _PARAM.split(pattern)
    return re.compile("[1-9][0-9]*".join(re.escape(p) for p in parts))


def _parse_segments() -> tuple[frozenset[str], dict[str, str], tuple[SegmentFamily, ...]]:
    exact: dict[str, str] = {}
    families: list[SegmentFamily] = []
    for cells in _rows(vocabulary_text("segments.md")):
        ident = cells[0]
        if not ident.startswith("segment:"):
            continue
        name = cells[1] if len(cells) > 1 else ident
        if _PARAM.search(ident):
            families.append(SegmentFamily(ident, _family_regex(ident), name))
        else:
            exact[ident] = name
    return frozenset(exact), exact, tuple(families)


def _parse_market_types() -> dict[str, MarketType]:
    out: dict[str, MarketType] = {}
    for cells in _rows(vocabulary_text("market_types.md")):
        ident = cells[0]
        if not ident.startswith("market:"):
            continue
        cells = cells + [""] * (6 - len(cells))
        out[ident] = MarketType(
            id=ident,
            name=cells[1],
            shape=cells[2],
            category=cells[3],
            sides=cells[4],
            description=cells[5],
        )
    return out


def _parse_deprecated() -> dict[str, list]:
    data = json.loads(vocabulary_text("deprecated.json"))
    return data if isinstance(data, dict) else {}


SPORTS, SPORT_NAMES, DISCIPLINES = _parse_sports()
SEGMENTS, SEGMENT_NAMES, SEGMENT_FAMILIES = _parse_segments()
MARKET_TYPES = _parse_market_types()
DEPRECATED = _parse_deprecated()
SIDES: frozenset[str] = frozenset(schema("common")["$defs"]["side"]["enum"])


def _with_prefix(value: str, prefix: str) -> str:
    return value if value.startswith(prefix) else prefix + value


def sport_slug(sport_id: str) -> str:
    """``sport:soccer`` -> ``soccer`` (the bare slug an envelope carries)."""
    return sport_id.removeprefix("sport:")


def is_known_sport(sport_id: str) -> bool:
    return sport_id in SPORTS


def is_known_segment(segment_id: str) -> bool:
    if segment_id in SEGMENTS:
        return True
    return any(f.matches(segment_id) for f in SEGMENT_FAMILIES)


def is_known_market(market_id: str) -> bool:
    return market_id in MARKET_TYPES


def is_known_side(side: str) -> bool:
    return side in SIDES


def sport_or_unknown(slug: str) -> str:
    """``soccer`` or ``sport:soccer`` -> ``sport:soccer``; anything else -> ``sport:unknown``."""
    if not isinstance(slug, str) or not slug:
        return SPORT_UNKNOWN
    ident = _with_prefix(slug, "sport:")
    return ident if ident in SPORTS else SPORT_UNKNOWN


def segment_or_unknown(sport_slug: str, slice: str) -> str:
    """``("soccer", "1st-half")`` -> ``segment:soccer:1st-half``, else ``segment:unknown:unknown``.

    ``sport_slug`` may carry the ``sport:`` prefix; ``slice`` may be a member of a
    numbered family (``inning-12``)."""
    if not isinstance(sport_slug, str) or not isinstance(slice, str) or not sport_slug or not slice:
        return SEGMENT_UNKNOWN
    ident = f"segment:{sport_slug.removeprefix('sport:')}:{slice}"
    return ident if is_known_segment(ident) else SEGMENT_UNKNOWN


def market_or_unknown(slug: str) -> str:
    """``moneyline`` or ``market:moneyline`` -> ``market:moneyline``; else ``market:unknown``."""
    if not isinstance(slug, str) or not slug:
        return MARKET_UNKNOWN
    ident = _with_prefix(slug, "market:")
    return ident if ident in MARKET_TYPES else MARKET_UNKNOWN


def is_deprecated(value: str) -> bool:
    """True if the spec's ``deprecated.json`` lists ``value`` under any heading."""
    return any(value in entries for entries in DEPRECATED.values() if isinstance(entries, list))


__all__ = [
    "DEPRECATED",
    "DISCIPLINES",
    "MARKET_TYPES",
    "MARKET_UNKNOWN",
    "MarketType",
    "SEGMENTS",
    "SEGMENT_FAMILIES",
    "SEGMENT_NAMES",
    "SEGMENT_UNKNOWN",
    "SIDES",
    "SPORTS",
    "SPORT_NAMES",
    "SPORT_UNKNOWN",
    "SegmentFamily",
    "is_deprecated",
    "is_known_market",
    "is_known_segment",
    "is_known_side",
    "is_known_sport",
    "market_or_unknown",
    "segment_or_unknown",
    "sport_or_unknown",
    "sport_slug",
]
