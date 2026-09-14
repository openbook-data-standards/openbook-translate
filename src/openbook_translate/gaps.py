"""Count what an adapter could not map, so the mapping tables can grow.

``GapCounter`` is in-memory. Give it a ``GapSink`` and every record is also
forwarded there, so a service can persist counts in whatever store it has
without this package knowing about it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from openbook_translate.tables import Unmapped


@runtime_checkable
class GapSink(Protocol):
    """Anything that accepts one gap at a time (a DB table, a metrics client, a queue)."""

    def record(self, kind: str, vendor_value: str, sample: Any | None = None) -> None: ...


@dataclass(frozen=True)
class Gap:
    kind: str
    vendor: str
    count: int
    sample: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "vendor": self.vendor, "count": self.count, "sample": self.sample}


class GapCounter:
    """Tally of (kind, vendor value) misses with one retained sample each."""

    def __init__(self, sink: GapSink | None = None) -> None:
        self._counts: Counter[tuple[str, str]] = Counter()
        self._samples: dict[tuple[str, str], Any] = {}
        self.sink = sink

    def record(self, kind: str, vendor_value: object, sample: Any | None = None) -> None:
        vendor = str(vendor_value)
        key = (kind, vendor)
        self._counts[key] += 1
        if sample is not None and key not in self._samples:
            self._samples[key] = sample
        if self.sink is not None:
            self.sink.record(kind, vendor, sample)

    def record_unmapped(self, unmapped: Unmapped, sample: Any | None = None) -> None:
        """Convenience for the result of ``MappingTable.lookup``."""
        self.record(unmapped.kind, unmapped.vendor, sample)

    def report(self, top: int = 50) -> list[Gap]:
        """Gaps sorted by count (desc), then kind and vendor value."""
        ordered = sorted(self._counts.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))
        return [
            Gap(kind=k, vendor=v, count=n, sample=self._samples.get((k, v)))
            for (k, v), n in ordered[:top]
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "distinct": len(self._counts),
            "gaps": [g.to_dict() for g in self.report(top=len(self._counts))],
        }

    def format(self, top: int = 50) -> str:
        """Plain-text report, one line per gap."""
        rows = self.report(top)
        if not rows:
            return "no gaps"
        width = max(len(g.kind) for g in rows)
        lines = [f"{self.total} gap(s), {len(self._counts)} distinct"]
        for g in rows:
            line = f"{g.count:>6}  {g.kind:<{width}}  {g.vendor}"
            if g.sample is not None:
                line += f"  sample={g.sample!r}"
            lines.append(line)
        return "\n".join(lines)

    def clear(self) -> None:
        self._counts.clear()
        self._samples.clear()

    @property
    def total(self) -> int:
        return sum(self._counts.values())

    def __len__(self) -> int:
        return len(self._counts)

    def __bool__(self) -> bool:
        return True


def counter_of(translator: object) -> GapCounter | None:
    """The ``GapCounter`` a translator exposes as ``gaps``, if any.

    Adapters that want their gaps reported (by the contract suite and the
    ``gaps`` CLI) set ``self.gaps = GapCounter()``."""
    gaps = getattr(translator, "gaps", None)
    return gaps if isinstance(gaps, GapCounter) else None


__all__ = ["Gap", "GapCounter", "GapSink", "counter_of"]
