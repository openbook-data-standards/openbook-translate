from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema"


def _load_schemas():
    schemas = {p.name: json.loads(p.read_text()) for p in SCHEMA_DIR.glob("*.json")}
    registry = Registry()
    for name, s in schemas.items():
        res = Resource(contents=s, specification=DRAFT202012)
        registry = registry.with_resource(name, res)
        if "$id" in s:
            registry = registry.with_resource(s["$id"], res)
    return schemas, registry


SCHEMAS, REGISTRY = _load_schemas()


def native_keys(doc: dict) -> list[dict]:
    keys = doc.get("identifier") or doc.get("x_identifier") or []
    if not isinstance(keys, list):
        return []
    return [k for k in keys if isinstance(k, dict) and k.get("propertyID") and k.get("value") is not None]


def guess_stem(doc: dict) -> str | None:
    if "object" in doc and "action" in doc:
        return "change"
    if "feeds" in doc and "ttl" in doc:
        return "discovery"
    if "sources" in doc and "baseCurrency" in doc:
        return "publisher"
    if "marketType" in doc and "outcomes" in doc:
        return "market"
    if "participants" in doc and "sport" in doc:
        return "fixture"
    if "gradeId" in doc or (doc.get("outcomes") and "basedOn" in doc):
        return "grade"
    if "scores" in doc or "currentSegment" in doc:
        return "score"
    return None


def iter_errors(doc: dict) -> list[str]:
    stem = guess_stem(doc)
    if not stem:
        return ["cannot guess OpenBook document type"]
    name = f"{stem}.schema.json"
    if name not in SCHEMAS:
        return [f"no schema {name}"]
    v = Draft202012Validator(SCHEMAS[name], registry=REGISTRY)
    return [e.message for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path))]
