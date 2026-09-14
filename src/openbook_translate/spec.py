from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = PACKAGE_ROOT / "schema"
STAMP_PATH = PACKAGE_ROOT / "openbook-spec-version"
SPEC_VERSION_RE = re.compile(r"Version `([^`]+)`")
REMOTE_SPEC_URL = (
    "https://raw.githubusercontent.com/openbook-data-standards/openbook/main/spec/openbook.md"
)
REMOTE_SCHEMA_URL = (
    "https://raw.githubusercontent.com/openbook-data-standards/openbook/main/schema/{name}"
)


def spec_version_stamp() -> str:
    return STAMP_PATH.read_text(encoding="utf-8").strip()


def parse_spec_version(text: str) -> str | None:
    m = SPEC_VERSION_RE.search(text)
    return m.group(1) if m else None


def schema_names() -> list[str]:
    return sorted(p.name for p in SCHEMA_DIR.glob("*.json"))


@lru_cache(maxsize=1)
def _registry() -> tuple[dict[str, dict], Registry]:
    schemas: dict[str, dict] = {}
    registry = Registry()
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schemas[path.name] = schema
        res = Resource(contents=schema, specification=DRAFT202012)
        registry = registry.with_resource(path.name, res)
        if "$id" in schema:
            registry = registry.with_resource(schema["$id"], res)
    common = schemas["common.schema.json"]
    base = "https://openbook-data-standards.github.io/openbook/schema/"
    registry = registry.with_resource(
        base + "common.schema.json",
        Resource(contents=common, specification=DRAFT202012),
    )
    return schemas, registry


def schema_allows_identifier(stem: str) -> bool:
    schemas, _ = _registry()
    name = f"{stem}.schema.json"
    schema = schemas.get(name)
    if schema is None:
        return False
    return "identifier" in schema.get("properties", {})


def validate_document(stem: str, document: dict) -> list[str]:
    schemas, registry = _registry()
    name = f"{stem}.schema.json"
    schema = schemas.get(name)
    if schema is None:
        return [f"unknown schema stem {stem!r}"]
    validator = Draft202012Validator(schema, registry=registry)
    return [e.message for e in validator.iter_errors(document)]


def document_stem(document: dict) -> str | None:
    matches = [
        stem
        for name in schema_names()
        for stem in [name.removesuffix(".schema.json")]
        if schema_allows_identifier(stem) and not validate_document(stem, document)
    ]
    if len(matches) == 1:
        return matches[0]
    return None
