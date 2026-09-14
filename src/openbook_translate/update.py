from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from openbook_translate.spec import (
    REMOTE_SCHEMA_DIR_URL,
    REMOTE_SCHEMA_URL,
    REMOTE_SPEC_URL,
    SCHEMA_DIR,
    parse_spec_version,
    schema_names,
    spec_version_stamp,
)


def find_spec_root(start: Path | None = None) -> Path | None:
    here = start or SCHEMA_DIR.parent
    for path in [here, *here.parents]:
        if (path / "schema").is_dir() and (path / "spec" / "openbook.md").is_file():
            if (path / "schema").resolve() != SCHEMA_DIR.resolve():
                return path
    return None


def check(*, spec_root: Path | None = None, fetch: bool = False) -> list[str]:
    problems: list[str] = []
    stamp = spec_version_stamp()
    local_names = set(schema_names())

    # Both modes resolve to (remote spec version, the set of schema names the
    # spec ships, a reader that returns one schema's bytes or None). The
    # comparison below is then identical, so drift is detected symmetrically —
    # including schemas added to or removed from the spec, not only edited ones.
    remote_bytes: Callable[[str], bytes | None]
    if spec_root is not None:
        version_text = (spec_root / "spec" / "openbook.md").read_text(encoding="utf-8")
        remote_version = parse_spec_version(version_text)
        remote_dir = spec_root / "schema"
        remote_names = {p.name for p in remote_dir.glob("*.json")}

        def remote_bytes(name: str) -> bytes | None:
            path = remote_dir / name
            return path.read_bytes() if path.is_file() else None

    elif fetch:
        version_text = _get(REMOTE_SPEC_URL)
        remote_version = parse_spec_version(version_text)
        remote_names = _remote_schema_names()

        def remote_bytes(name: str) -> bytes | None:
            try:
                return _get_bytes(REMOTE_SCHEMA_URL.format(name=name))
            except urllib.error.HTTPError:
                return None

    else:
        raise ValueError("pass spec_root or fetch=True")

    for name in sorted(local_names | remote_names):
        if name not in remote_names:
            problems.append(f"{name}: vendored, not in spec")
            continue
        if name not in local_names:
            problems.append(f"{name}: in spec, not vendored")
            continue
        remote = remote_bytes(name)
        if remote is None:
            problems.append(f"{name}: could not read from spec")
            continue
        if (SCHEMA_DIR / name).read_bytes() != remote:
            problems.append(f"{name}: differs from spec")

    if remote_version is None:
        problems.append("could not read spec version")
    elif remote_version != stamp:
        problems.append(f"openbook-spec-version {stamp!r} != spec {remote_version!r}")
    return problems


def _remote_schema_names() -> set[str]:
    entries = json.loads(_get(REMOTE_SCHEMA_DIR_URL))
    if not isinstance(entries, list):
        return set()
    return {
        e["name"]
        for e in entries
        if isinstance(e, dict) and str(e.get("name", "")).endswith(".json")
    }


def _get(url: str) -> str:
    return _get_bytes(url).decode("utf-8")


def _get_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        return resp.read()
