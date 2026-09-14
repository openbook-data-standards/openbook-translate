from __future__ import annotations

import json
from pathlib import Path

import pytest

from openbook_translate.abc import Translator
from openbook_translate.acme import AcmeTranslator
from openbook_translate.adapters import load
from openbook_translate.identifier import native_id
from openbook_translate.types import Documents, Quarantine, Vendor

DATA = Path(__file__).resolve().parent / "data"
FIXTURE = json.loads((DATA / "fixture.example.json").read_text(encoding="utf-8"))
MARKET = json.loads((DATA / "market.example.json").read_text(encoding="utf-8"))


def _raw(obj: dict) -> bytes:
    return json.dumps(obj).encode("utf-8")


def test_abc_is_abstract() -> None:
    assert issubclass(AcmeTranslator, Translator)
    with pytest.raises(TypeError):
        Translator()  # type: ignore[abstract]


def test_acme_translate_stamps_identifier() -> None:
    t = AcmeTranslator()
    result = t.translate(
        _raw({"id": "A-88213", "type": "fixture", "openbook": FIXTURE}),
        source_id="acme-book",
    )
    assert isinstance(result, Documents)
    doc = result.documents[0]
    assert native_id(doc, "acme") == "A-88213"


def test_acme_uses_parsed_not_bytes() -> None:
    t = AcmeTranslator()
    result = t.translate(
        b"this is not json",
        source_id="acme-book",
        parsed={"id": "A-1", "type": "fixture", "openbook": FIXTURE},
    )
    assert isinstance(result, Documents)
    assert native_id(result.documents[0], "acme") == "A-1"


def test_unmapped_quarantines_does_not_raise() -> None:
    t = AcmeTranslator()
    raw = b"not-json"
    result = t.translate(raw, source_id="acme-book")
    assert isinstance(result, Quarantine)
    assert result.raw == raw
    assert result.reason.startswith("unmapped:")


def test_market_has_no_identifier_quarantine() -> None:
    t = AcmeTranslator()
    result = t.translate(
        _raw({"id": "M-1", "type": "market", "openbook": MARKET}),
        source_id="acme-book",
    )
    assert isinstance(result, Quarantine)
    assert "identifier" in result.reason


def test_round_trip_native_id() -> None:
    t = AcmeTranslator()
    inbound = {"id": "A-88213", "type": "fixture", "openbook": FIXTURE}
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


def test_reverse_without_native_id_quarantines() -> None:
    t = AcmeTranslator()
    result = t.reverse(FIXTURE)
    assert isinstance(result, Quarantine)


def test_entry_point_acme() -> None:
    t = load("acme")
    assert t.name == "acme"


def test_update_detects_stamp_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from openbook_translate import spec as spec_mod
    from openbook_translate import update as update_mod

    spec_root = tmp_path / "spec"
    (spec_root / "spec").mkdir(parents=True)
    (spec_root / "schema").mkdir()
    (spec_root / "spec" / "openbook.md").write_text("Version `0.3.0-draft`\n", encoding="utf-8")
    for path in spec_mod.SCHEMA_DIR.glob("*.json"):
        (spec_root / "schema" / path.name).write_bytes(path.read_bytes())

    monkeypatch.setattr(update_mod, "spec_version_stamp", lambda: "not-a-version")
    problems = update_mod.check(spec_root=spec_root)
    assert any("openbook-spec-version" in p for p in problems)
