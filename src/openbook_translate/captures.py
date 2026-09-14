"""Read golden captures: one vendor record per ``*.json`` file, one per ``*.jsonl`` line."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Capture:
    path: Path
    line: int | None
    raw: bytes

    @property
    def label(self) -> str:
        return f"{self.path}:{self.line}" if self.line is not None else str(self.path)


def iter_captures(directory: str | Path) -> Iterator[Capture]:
    """Yield every record under ``directory`` (recursive), sorted by path.

    Blank lines in ``.jsonl`` files are skipped. Bytes are passed through
    untouched; parsing is the adapter's job."""
    root = Path(directory)
    if root.is_file():
        paths = [root]
    else:
        paths = sorted(p for p in root.rglob("*") if p.suffix in (".json", ".jsonl") and p.is_file())
    for path in paths:
        if path.suffix == ".jsonl":
            for i, line in enumerate(path.read_bytes().splitlines(), 1):
                if line.strip():
                    yield Capture(path=path, line=i, raw=line)
        else:
            yield Capture(path=path, line=None, raw=path.read_bytes())


__all__ = ["Capture", "iter_captures"]
