from __future__ import annotations

import json
from pathlib import Path

import pytest

from openbook_translate.tables import KINDS, Mapped, MappingTable, TableError, Unmapped, catch_all, x_field_name

TABLE = {
    "adapter": "acme",
    "sport": [{"vendor": "SOCC", "id": "sport:soccer", "name": "Soccer", "x": {"code": 1}}],
    "segment": [{"vendor": "1H", "id": "segment:soccer:1st-half"}, {"vendor": "I12", "id": "segment:baseball:inning-12"}],
    "market_type": [{"vendor": "ML", "id": "market:moneyline"}],
    "side": [{"vendor": 1, "id": "home"}],
}


def test_load_from_dict_and_lookup() -> None:
    t = MappingTable.load(TABLE)
    assert t.adapter == "acme" and len(t) == 5 and t.kinds() == list(KINDS)
    hit = t.lookup("sport", "SOCC")
    assert hit == Mapped(kind="sport", vendor="SOCC", id="sport:soccer", name="Soccer", x={"code": 1})
    assert t.lookup("segment", "I12").id == "segment:baseball:inning-12"
    # vendor values are matched as strings, so ints in the feed still hit
    assert t.lookup("side", 1).id == "home" and t.lookup("side", "1").id == "home"


def test_load_from_path(tmp_path: Path) -> None:
    p = tmp_path / "t.json"
    p.write_text(json.dumps(TABLE))
    assert MappingTable.load(p).lookup("market_type", "ML").id == "market:moneyline"
    assert MappingTable.load(str(p), adapter="other").lookup("sport", "X").x_field == "x_otherSportId"


def test_unmapped_carries_catch_all_and_x_field() -> None:
    t = MappingTable.load(TABLE)
    miss = t.lookup("sport", "CURL")
    assert miss == Unmapped(kind="sport", vendor="CURL", id="sport:unknown", x_field="x_acmeSportId")
    assert t.lookup("segment", "OT").id == "segment:unknown:unknown"
    assert t.lookup("market_type", "ZZ").id == "market:unknown"
    assert t.lookup("side", "9").id == "other"
    assert t.lookup("market_type", "ZZ").x_field == "x_acmeMarketTypeId"
    stamped = miss.stamp({"a": 1})
    assert stamped == {"a": 1, "x_acmeSportId": "CURL"}


def test_x_field_name_camelizes_adapter() -> None:
    assert x_field_name("acme", "sport") == "x_acmeSportId"
    assert x_field_name("acme-feeds", "segment") == "x_acmeFeedsSegmentId"
    assert x_field_name("Big Book 2", "side") == "x_bigBook2SideId"
    for kind in KINDS:
        assert catch_all(kind)


def test_validation_collects_every_problem() -> None:
    with pytest.raises(TableError) as ei:
        MappingTable.load(
            {
                "adapter": "a",
                "sport": [
                    {"vendor": "X", "id": "sport:nope"},
                    {"vendor": "X", "id": "sport:soccer"},
                    {"id": "sport:soccer"},
                    {"vendor": "Y"},
                    "not an object",
                ],
                "segment": [{"vendor": "Q", "id": "segment:soccer:9th-half"}],
                "market_type": [{"vendor": "M", "id": "moneyline"}],
                "side": [{"vendor": "S", "id": "left"}],
                "league": [],
            }
        )
    problems = ei.value.problems
    assert any("sport:nope" in p for p in problems)
    assert any("duplicate vendor key 'X'" in p for p in problems)
    assert any('missing "vendor"' in p for p in problems)
    assert any('missing "id"' in p for p in problems)
    assert any("entry must be an object" in p for p in problems)
    assert any("9th-half" in p for p in problems)
    assert any("'moneyline' is not a known market_type id" in p for p in problems)
    assert any("'left' is not a known side id" in p for p in problems)
    assert any("unknown kind 'league'" in p for p in problems)


def test_adapter_name_required() -> None:
    with pytest.raises(TableError, match="adapter name missing"):
        MappingTable.load({"sport": []})
    with pytest.raises(TableError):
        MappingTable.load([])  # type: ignore[arg-type]


def test_unknown_kind_lookup_raises() -> None:
    with pytest.raises(KeyError):
        MappingTable.load(TABLE).lookup("league", "x")


def test_acme_table_ships_in_package() -> None:
    from openbook_translate.acme import TABLES_PATH

    t = MappingTable.load(json.loads(TABLES_PATH.read_text(encoding="utf-8")))
    assert t.adapter == "acme" and t.lookup("sport", "SOCC").id == "sport:soccer"
