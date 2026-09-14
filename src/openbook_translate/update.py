from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from openbook_translate.spec import (
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
    if spec_root is not None:
        version_text = (spec_root / "spec" / "openbook.md").read_text(encoding="utf-8")
        remote_version = parse_spec_version(version_text)
        remote_dir = spec_root / "schema"
        remote_names = {p.name for p in remote_dir.glob("*.json")}
        local_names = set(schema_names())
        for name in sorted(local_names | remote_names):
            local = SCHEMA_DIR / name
            remote = remote_dir / name
            if not local.is_file():
                problems.append(f"{name}: in spec, not vendored")
                continue
            if not remote.is_file():
                problems.append(f"{name}: vendored, not in spec")
                continue
            if local.read_bytes() != remote.read_bytes():
                problems.append(f"{name}: differs from spec")
    elif fetch:
        version_text = _get(REMOTE_SPEC_URL)
        remote_version = parse_spec_version(version_text)
        for name in schema_names():
            try:
                body = _get_bytes(REMOTE_SCHEMA_URL.format(name=name))
            except urllib.error.HTTPError as e:
                problems.append(f"{name}: fetch {e.code}")
                continue
            if (SCHEMA_DIR / name).read_bytes() != body:
                problems.append(f"{name}: differs from spec")
    else:
        raise ValueError("pass spec_root or fetch=True")

    if remote_version is None:
        problems.append("could not read spec version")
    elif remote_version != stamp:
        problems.append(f"openbook-spec-version {stamp!r} != spec {remote_version!r}")
    return problems


def _get(url: str) -> str:
    return _get_bytes(url).decode("utf-8")


def _get_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        return resp.read()
