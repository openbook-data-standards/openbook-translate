from __future__ import annotations

import json

import pytest

from openbook_translate import SPEC_COMMIT, SPEC_VERSION, __version__
from openbook_translate.abc import Translator
from openbook_translate.acme import AcmeTranslator
from openbook_translate.adapters import load
from openbook_translate.identifier import native_id
from openbook_translate.types import (
    OTHER,
    PARSE_ERROR,
    REASONS,
    SCHEMA_INVALID,
    Documents,
    Quarantine,
    Vendor,
)


def _raw(obj: dict) -> bytes:
    return json.dumps(obj).encode("utf-8")


def test_package_constants() -> None:
    assert __version__ == "0.1.0"
    assert SPEC_VERSION == "0.3.0-draft"
    assert len(SPEC_COMMIT) == 40 and all(c in "0123456789abcdef" for c in SPEC_COMMIT)


def test_abc_is_abstract() -> None:
    assert issubclass(AcmeTranslator, Translator)
    with pytest.raises(TypeError):
        Translator()  # type: ignore[abstract]


def test_acme_translate_stamps_identifier(fixture_doc: dict) -> None:
    t = AcmeTranslator()
    result = t.translate(
        _raw({"id": "A-88213", "type": "fixture", "openbook": fixture_doc}),
        source_id="acme-book",
    )
    assert isinstance(result, Documents)
    doc = result.documents[0]
    assert native_id(doc, "acme") == "A-88213"
    # the vendor's other identifiers survive
    assert {"propertyID": "sportradar", "value": "sr:match:8412480"} in doc["identifier"]


def test_acme_uses_parsed_not_bytes(fixture_doc: dict) -> None:
    t = AcmeTranslator()
    result = t.translate(
        b"this is not json",
        source_id="acme-book",
        parsed={"id": "A-1", "type": "fixture", "openbook": fixture_doc},
    )
    assert isinstance(result, Documents)
    assert native_id(result.documents[0], "acme") == "A-1"


def test_unmapped_quarantines_does_not_raise() -> None:
    t = AcmeTranslator()
    raw = b"not-json"
    result = t.translate(raw, source_id="acme-book")
    assert isinstance(result, Quarantine)
    assert result.raw == raw
    assert result.reason == PARSE_ERROR
    assert result.reason in REASONS
    assert result.source_id == "acme-book"
    assert result.adapter == "acme"
    assert result.detail


@pytest.mark.parametrize(
    ("record", "detail"),
    [
        ({"type": "fixture", "openbook": {}}, "missing id"),
        ({"id": "A-1", "openbook": {}}, "missing type"),
        ({"id": "A-1", "type": "fixture"}, "missing openbook"),
        ({"id": "A-1", "type": "nope", "openbook": {}}, "no identifier"),
    ],
)
def test_malformed_records_quarantine_with_other(record: dict, detail: str) -> None:
    result = AcmeTranslator().translate(_raw(record), source_id="acme-book")
    assert isinstance(result, Quarantine)
    assert result.reason == OTHER
    assert detail in str(result.detail)


def test_schema_invalid_quarantines(fixture_doc: dict) -> None:
    broken = dict(fixture_doc)
    del broken["startDate"]
    result = AcmeTranslator().translate(
        _raw({"id": "A-1", "type": "fixture", "openbook": broken}), source_id="acme-book"
    )
    assert isinstance(result, Quarantine)
    assert result.reason == SCHEMA_INVALID
    assert "startDate" in str(result.detail)


def test_market_has_no_identifier_quarantine(market_doc: dict) -> None:
    t = AcmeTranslator()
    result = t.translate(
        _raw({"id": "M-1", "type": "market", "openbook": market_doc}),
        source_id="acme-book",
    )
    assert isinstance(result, Quarantine)
    assert result.reason == OTHER
    assert "identifier" in str(result.detail)


def test_round_trip_native_id(fixture_doc: dict) -> None:
    t = AcmeTranslator()
    inbound = {"id": "A-88213", "type": "fixture", "openbook": fixture_doc}
    mapped = t.translate(_raw(inbound), source_id="acme-book")
    assert isinstance(mapped, Documents)
    back = t.reverse(mapped.documents[0])
    assert isinstance(back, Vendor)
    assert back.parsed is not None
    assert back.parsed["id"] == "A-88213"
    assert back.parsed["type"] == "fixture"
    again = t.translate(back.raw, source_id="acme-book", parsed=back.parsed)
    assert isinstance(again, Documents)
    assert native_id(again.documents[0], "acme") == "A-88213"


def test_reverse_without_native_id_quarantines(fixture_doc: dict) -> None:
    result = AcmeTranslator().reverse(fixture_doc)
    assert isinstance(result, Quarantine)
    assert result.reason == OTHER


def test_acme_sport_table_hit_and_gap(fixture_doc: dict) -> None:
    body = {k: v for k, v in fixture_doc.items() if k != "sport"}
    t = AcmeTranslator()
    hit = t.translate(_raw({"id": "A-1", "type": "fixture", "sport": "SOCC", "openbook": body}), source_id="b")
    assert isinstance(hit, Documents)
    assert hit.documents[0]["sport"] == {"id": "sport:soccer", "name": "Soccer"}
    assert "x_acmeSportId" not in hit.documents[0]
    assert t.gaps.total == 0

    miss = t.translate(_raw({"id": "A-2", "type": "fixture", "sport": "CURL", "openbook": body}), source_id="b")
    assert isinstance(miss, Documents), miss
    doc = miss.documents[0]
    assert doc["sport"] == {"id": "sport:unknown", "name": "Unknown"}
    assert doc["x_acmeSportId"] == "CURL"
    report = t.gaps.report()
    assert len(report) == 1 and report[0].kind == "sport" and report[0].vendor == "CURL" and report[0].count == 1
    assert report[0].sample == "A-2"


def test_entry_point_acme() -> None:
    t = load("acme")
    assert t.name == "acme"


def test_entry_point_unknown() -> None:
    with pytest.raises(KeyError):
        load("does-not-exist")
