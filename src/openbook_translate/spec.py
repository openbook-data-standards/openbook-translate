"""Vendored OpenBook schemas and validation.

Everything this module reads ships inside the wheel as package data
(``schema/*.json``, ``openbook-spec-version``, ``openbook-spec-commit``,
``vocabularies/*``) and is located through :mod:`importlib.resources`, so a
non-editable install works the same as a checkout.
"""

from __future__ import annotations

import copy
import json
import re
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

_PACKAGE = files("openbook_translate")

# Filesystem locations of the vendored data. Kept as ``Path`` for callers that
# already use them (``update`` reads bytes to diff against the spec checkout).
PACKAGE_ROOT = Path(str(_PACKAGE))
SCHEMA_DIR = PACKAGE_ROOT / "schema"
VOCAB_DIR = PACKAGE_ROOT / "vocabularies"
STAMP_PATH = PACKAGE_ROOT / "openbook-spec-version"
COMMIT_PATH = PACKAGE_ROOT / "openbook-spec-commit"

SPEC_VERSION_RE = re.compile(r"Version `([^`]+)`")
SPEC_REPO = "openbook-data-standards/openbook"
REMOTE_SPEC_URL = f"https://raw.githubusercontent.com/{SPEC_REPO}/main/spec/openbook.md"
REMOTE_SCHEMA_URL = f"https://raw.githubusercontent.com/{SPEC_REPO}/main/schema/{{name}}"
REMOTE_VOCAB_URL = f"https://raw.githubusercontent.com/{SPEC_REPO}/main/vocabularies/{{name}}"
REMOTE_SCHEMA_DIR_URL = f"https://api.github.com/repos/{SPEC_REPO}/contents/schema?ref=main"

# Vocabulary files vendored from the spec's ``vocabularies/`` directory.
VOCABULARY_NAMES = ("sports.md", "segments.md", "market_types.md", "deprecated.json")

# Envelope ``object`` -> document schema stem its ``changes`` are validated
# against. Mirrors ``tools/validate.py`` in the spec repository.
OBJECT_SCHEMA: dict[str, str] = {
    "fixture": "fixture",
    "odds": "odds_change",
    "market": "market",
    "score": "score",
    "grade": "grade",
    "league": "league",
    "season": "season",
    "stage": "stage",
    "participant": "participant",
    "player": "player",
    "publisher": "publisher",
    "lineup": "lineup",
    "stall": "stall",
    "toss": "toss",
    "series": "series",
}

# Carried by the envelope, never required inside ``changes``.
ENVELOPE_FIELDS = ("openbookVersion", "sequence", "dateModified")

# Actions whose ``changes`` is the whole object (everything else is a Merge Patch).
FULL_ACTIONS = frozenset({"snapshot", "create"})


def _read_text(name: str) -> str:
    return _PACKAGE.joinpath(name).read_text(encoding="utf-8")


def spec_version_stamp() -> str:
    """The OpenBook version the vendored schemas were copied from."""
    return _read_text("openbook-spec-version").strip()


def spec_commit_stamp() -> str:
    """The spec repository commit the vendored schemas were copied from."""
    return _read_text("openbook-spec-commit").strip()


SPEC_VERSION = spec_version_stamp()
SPEC_COMMIT = spec_commit_stamp()


def parse_spec_version(text: str) -> str | None:
    m = SPEC_VERSION_RE.search(text)
    return m.group(1) if m else None


def schema_names() -> list[str]:
    return sorted(
        entry.name for entry in _PACKAGE.joinpath("schema").iterdir() if entry.name.endswith(".json")
    )


def schema_stems() -> list[str]:
    return [name.removesuffix(".schema.json") for name in schema_names()]


def vocabulary_text(name: str) -> str:
    """Raw text of one vendored vocabulary file (see ``VOCABULARY_NAMES``)."""
    return _PACKAGE.joinpath("vocabularies", name).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _registry() -> tuple[dict[str, dict], Registry]:
    schemas: dict[str, dict] = {}
    registry = Registry()
    for name in schema_names():
        schema = json.loads(_read_text(f"schema/{name}"))
        schemas[name] = schema
        res = Resource(contents=schema, specification=DRAFT202012)
        registry = registry.with_resource(name, res)
        if "$id" in schema:
            registry = registry.with_resource(schema["$id"], res)
    common = schemas["common.schema.json"]
    base = "https://openbook-data-standards.github.io/openbook/schema/"
    registry = registry.with_resource(
        base + "common.schema.json",
        Resource(contents=common, specification=DRAFT202012),
    )
    return schemas, registry


def schema(name_or_stem: str) -> dict:
    """The vendored schema for ``fixture`` or ``fixture.schema.json``."""
    schemas, _ = _registry()
    name = name_or_stem if name_or_stem.endswith(".json") else f"{name_or_stem}.schema.json"
    return schemas[name]


def schema_allows(stem: str, prop: str) -> bool:
    """True if the document schema for ``stem`` declares ``prop`` as a property."""
    schemas, _ = _registry()
    s = schemas.get(f"{stem}.schema.json")
    if s is None:
        return False
    return prop in s.get("properties", {})


def schema_allows_identifier(stem: str) -> bool:
    return schema_allows(stem, "identifier")


def _validator(s: dict) -> Draft202012Validator:
    _, registry = _registry()
    return Draft202012Validator(s, registry=registry)


def _messages(errors) -> list[str]:
    out = []
    for e in sorted(errors, key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in e.path)
        out.append(f"{e.message} at /{where}" if where else e.message)
    return out


def validate_document(stem: str, document: dict) -> list[str]:
    """Schema errors for one OpenBook document. Empty list = valid."""
    schemas, _ = _registry()
    s = schemas.get(f"{stem}.schema.json")
    if s is None:
        return [f"unknown schema stem {stem!r}"]
    return _messages(_validator(s).iter_errors(document))


def for_changes(document_schema: dict, full: bool) -> dict:
    """A document schema as it applies to an envelope's ``changes``.

    The envelope already carries ``openbookVersion``/``sequence``/``dateModified``
    so those are never required inside ``changes``. For snapshot/create the rest
    stays required; for update/change/snapshotComplete/heartbeat nothing is
    required (RFC 7386 Merge Patch). Mirrors the spec's ``tools/validate.py``.
    """
    s = copy.deepcopy(document_schema)
    s.pop("$id", None)
    req = [r for r in s.get("required", []) if r not in ENVELOPE_FIELDS] if full else []
    if req:
        s["required"] = req
    else:
        s.pop("required", None)
    return s


def is_envelope(obj: object) -> bool:
    """A message (has ``object`` and ``action``) rather than a document."""
    return isinstance(obj, dict) and "object" in obj and "action" in obj


def validate_envelope(envelope: dict) -> list[str]:
    """Errors for one change envelope. Empty list = valid.

    Validates the envelope against ``change.schema.json``, then ``changes``
    against the object's document schema (``OBJECT_SCHEMA``): in full for
    ``snapshot``/``create``, with ``required`` dropped for every other action.
    """
    schemas, _ = _registry()
    out = [f"envelope: {m}" for m in _messages(_validator(schemas["change.schema.json"]).iter_errors(envelope))]
    obj = envelope.get("object") if isinstance(envelope, dict) else None
    target = OBJECT_SCHEMA.get(obj) if isinstance(obj, str) else None
    if target is not None and f"{target}.schema.json" not in schemas:
        out.append(f"no schema for object {obj!r} (expected {target}.schema.json)")
        target = None
    changes = envelope.get("changes") if isinstance(envelope, dict) else None
    if target is not None and isinstance(changes, dict):
        full = envelope.get("action") in FULL_ACTIONS
        mode = "full" if full else "patch"
        v = _validator(for_changes(schemas[f"{target}.schema.json"], full))
        for e in sorted(v.iter_errors(changes), key=lambda e: list(e.path)):
            where = "/".join(str(p) for p in e.path)
            out.append(f"changes vs {target} ({mode}): {e.message} at /changes/{where}")
    return out


def document_stem(document: dict) -> str | None:
    """The one identifier-bearing schema stem this document validates against."""
    matches = [
        stem
        for stem in schema_stems()
        if schema_allows_identifier(stem) and not validate_document(stem, document)
    ]
    if len(matches) == 1:
        return matches[0]
    return None
