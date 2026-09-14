from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import DATA

from openbook_translate import spec

EXAMPLES = sorted(DATA.glob("*.json"))
ENVELOPES = [p for p in EXAMPLES if spec.is_envelope(json.loads(p.read_text()))]
DOCUMENTS = [p for p in EXAMPLES if p not in ENVELOPES]


def test_package_data_is_inside_the_package() -> None:
    pkg = Path(spec.__file__).resolve().parent
    assert spec.SCHEMA_DIR == pkg / "schema"
    assert spec.STAMP_PATH == pkg / "openbook-spec-version"
    assert spec.COMMIT_PATH == pkg / "openbook-spec-commit"
    assert spec.VOCAB_DIR == pkg / "vocabularies"
    assert spec.STAMP_PATH.is_file() and spec.COMMIT_PATH.is_file()
    for name in spec.VOCABULARY_NAMES:
        assert (spec.VOCAB_DIR / name).is_file()


def test_stamp_and_commit() -> None:
    assert spec.spec_version_stamp() == spec.SPEC_VERSION == "0.3.0-draft"
    assert spec.spec_commit_stamp() == spec.SPEC_COMMIT
    assert len(spec.SPEC_COMMIT) == 40


def test_schema_names_cover_the_spec_objects() -> None:
    names = spec.schema_names()
    assert "common.schema.json" in names and "change.schema.json" in names
    for stem in set(spec.OBJECT_SCHEMA.values()):
        assert f"{stem}.schema.json" in names, stem
    for new in ("series", "stall", "toss"):
        assert f"{new}.schema.json" in names
    assert spec.schema("fixture")["$id"].endswith("fixture.schema.json")


def test_parse_spec_version() -> None:
    assert spec.parse_spec_version("# x\n\nVersion `0.3.0-draft` · 2026-09-12\n") == "0.3.0-draft"
    assert spec.parse_spec_version("nothing") is None


@pytest.mark.parametrize("path", ENVELOPES, ids=lambda p: p.name)
def test_spec_example_envelopes_are_valid(path: Path) -> None:
    assert spec.validate_envelope(json.loads(path.read_text())) == []


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: p.name)
def test_spec_example_documents_are_valid(path: Path) -> None:
    stem = path.name.split(".")[0]
    assert spec.validate_document(stem, json.loads(path.read_text())) == []


def test_example_sets_are_what_we_expect() -> None:
    assert len(EXAMPLES) == 21
    assert {p.name for p in ENVELOPES} >= {
        "fixture_update.example.json",
        "heartbeat.example.json",
        "snapshot_complete.example.json",
        "odds_change.example.json",
        "market_update.example.json",
    }


def test_conformance_invalid_missing_sequence() -> None:
    env = json.loads((DATA / "invalid" / "missing-sequence.json").read_text())
    errors = spec.validate_envelope(env)
    assert errors and "sequence" in errors[0]


def test_validate_envelope_full_for_create_patch_for_update(fixture_doc: dict) -> None:
    base = {
        "openbookVersion": "0.3.0-draft",
        "sequence": 1,
        "datePublished": "2026-09-19T13:05:00Z",
        "publisher": "acme-feeds",
        "object": "fixture",
        "sport": "soccer",
        "id": "EVT-1",
    }
    # update: a partial body is fine (Merge Patch)
    assert spec.validate_envelope({**base, "action": "update", "changes": {"startDate": "2026-09-19T14:15:00Z"}}) == []
    # create: the same partial body is missing required fields
    errors = spec.validate_envelope({**base, "action": "create", "changes": {"startDate": "2026-09-19T14:15:00Z"}})
    assert errors and any("required" in e and "changes vs fixture (full)" in e for e in errors)
    # create with the whole document minus envelope fields is fine
    body = {k: v for k, v in fixture_doc.items() if k not in spec.ENVELOPE_FIELDS}
    assert spec.validate_envelope({**base, "action": "create", "changes": body}) == []
    # snapshot never requires openbookVersion / sequence / dateModified inside changes
    assert spec.validate_envelope({**base, "action": "snapshot", "changes": body}) == []


def test_validate_envelope_reports_bad_values_inside_changes() -> None:
    env = {
        "openbookVersion": "0.3.0-draft",
        "sequence": 1,
        "datePublished": "2026-09-19T13:05:00Z",
        "publisher": "acme-feeds",
        "object": "fixture",
        "action": "update",
        "sport": "soccer",
        "id": "EVT-1",
        "changes": {"eventStatus": "not-a-status"},
    }
    errors = spec.validate_envelope(env)
    assert errors and errors[0].startswith("changes vs fixture (patch)")
    assert "/changes/eventStatus" in errors[0]


def test_validate_envelope_change_only_for_odds() -> None:
    env = {
        "openbookVersion": "0.3.0-draft",
        "sequence": 1,
        "datePublished": "2026-09-19T13:05:00Z",
        "publisher": "acme-feeds",
        "object": "fixture",
        "action": "change",
        "sport": "soccer",
        "changes": {},
    }
    assert spec.validate_envelope(env)
    assert spec.validate_envelope({**env, "object": "odds"}) == []


def test_for_changes() -> None:
    s = spec.schema("fixture")
    full = spec.for_changes(s, True)
    patch = spec.for_changes(s, False)
    assert "$id" not in full and "$id" not in patch
    assert "required" not in patch
    assert set(full["required"]) == set(s["required"]) - set(spec.ENVELOPE_FIELDS)
    assert "required" in s  # the vendored schema is untouched


def test_document_stem_and_helpers(fixture_doc: dict, market_doc: dict) -> None:
    assert spec.document_stem(fixture_doc) == "fixture"
    assert spec.document_stem(market_doc) is None  # market has no identifier
    assert spec.schema_allows_identifier("fixture") and not spec.schema_allows_identifier("market")
    assert spec.schema_allows("market", "source") and not spec.schema_allows("fixture", "source")
    assert spec.validate_document("nope", {}) == ["unknown schema stem 'nope'"]
    assert spec.is_envelope({"object": "fixture", "action": "update"})
    assert not spec.is_envelope(fixture_doc)
