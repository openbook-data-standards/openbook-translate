"""Build OpenBook change envelopes and RFC 7386 Merge Patches.

An envelope is one object, one action, and ``changes``: the whole document for
``snapshot``/``create``, a Merge Patch for everything else (absent = unchanged,
``null`` = removed). Validate with :func:`openbook_translate.spec.validate_envelope`.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from openbook_translate.spec import SPEC_VERSION

HEARTBEAT_SPORT = "unknown"


def now_rfc3339() -> str:
    """Current UTC time as the spec writes it (``2026-09-19T14:37:25Z``)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sport_slug(sport: str) -> str:
    """``sport:soccer`` -> ``soccer``. The envelope carries the bare slug."""
    return sport.removeprefix("sport:")


def change_envelope(
    *,
    publisher: str,
    sequence: int,
    object: str,
    action: str,
    sport: str,
    id: str | None = None,
    changes: dict[str, Any],
    openbook_version: str = SPEC_VERSION,
    date_published: str | datetime | None = None,
    conflated: bool | None = None,
    x: dict[str, Any] | None = None,
    msg_type: str | None = None,
    reason: str | None = None,
    references: list[int] | None = None,
) -> dict[str, Any]:
    """One envelope. ``sport`` may be the id (``sport:soccer``) or the slug.

    ``x`` holds extension fields; keys get the ``x_`` prefix if they lack it.
    Key order follows the spec examples so diffs against them read cleanly."""
    if not isinstance(changes, dict):
        raise TypeError("changes must be a dict (the object for snapshot/create, a Merge Patch otherwise)")
    if isinstance(date_published, datetime):
        if date_published.tzinfo is None:
            date_published = date_published.replace(tzinfo=timezone.utc)
        date_published = date_published.isoformat().replace("+00:00", "Z")
    env: dict[str, Any] = {
        "openbookVersion": openbook_version,
        "sequence": sequence,
        "datePublished": date_published or now_rfc3339(),
        "publisher": publisher,
        "object": object,
        "action": action,
        "sport": sport_slug(sport),
    }
    if id is not None:
        env["id"] = id
    if msg_type is not None:
        env["msgType"] = msg_type
    if reason is not None:
        env["reason"] = reason
    if references is not None:
        env["references"] = list(references)
    if conflated is not None:
        env["conflated"] = conflated
    for key, value in (x or {}).items():
        env[key if key.startswith("x_") else f"x_{key}"] = value
    env["changes"] = changes
    return env


def heartbeat(
    publisher: str,
    sequence: int,
    *,
    openbook_version: str = SPEC_VERSION,
    date_published: str | datetime | None = None,
) -> dict[str, Any]:
    """``publisher/heartbeat`` control message (sport ``unknown``, empty changes)."""
    return change_envelope(
        publisher=publisher,
        sequence=sequence,
        object="publisher",
        action="heartbeat",
        sport=HEARTBEAT_SPORT,
        changes={},
        openbook_version=openbook_version,
        date_published=date_published,
    )


def snapshot_complete(
    publisher: str,
    sequence: int,
    object: str,
    sport: str,
    *,
    id: str | None = None,
    openbook_version: str = SPEC_VERSION,
    date_published: str | datetime | None = None,
) -> dict[str, Any]:
    """``<object>/snapshotComplete`` control message (empty changes)."""
    return change_envelope(
        publisher=publisher,
        sequence=sequence,
        object=object,
        action="snapshotComplete",
        sport=sport,
        id=id,
        changes={},
        openbook_version=openbook_version,
        date_published=date_published,
    )


def merge_patch(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Minimal RFC 7386 Merge Patch turning ``old`` into ``new``.

    Removed keys become ``null`` tombstones, nested objects recurse, lists are
    replaced whole. An empty result means no change."""
    patch: dict[str, Any] = {}
    for key in old:
        if key not in new:
            patch[key] = None
    for key, value in new.items():
        if key not in old:
            patch[key] = copy.deepcopy(value)
            continue
        before = old[key]
        if isinstance(before, dict) and isinstance(value, dict):
            inner = merge_patch(before, value)
            if inner:
                patch[key] = inner
        elif before != value or type(before) is not type(value):
            patch[key] = copy.deepcopy(value)
    return patch


def apply_merge_patch(target: Any, patch: Any) -> Any:
    """RFC 7386 apply. Returns a new value; ``target`` is not mutated."""
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)
    out: dict[str, Any] = dict(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            out.pop(key, None)
        else:
            out[key] = apply_merge_patch(out.get(key), value)
    return out


__all__ = [
    "apply_merge_patch",
    "change_envelope",
    "heartbeat",
    "merge_patch",
    "now_rfc3339",
    "snapshot_complete",
    "sport_slug",
]
