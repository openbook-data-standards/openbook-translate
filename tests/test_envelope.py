from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from conftest import load

from openbook_translate import envelope as env
from openbook_translate.spec import SPEC_VERSION, validate_envelope


def test_change_envelope_matches_spec_example() -> None:
    expected = load("fixture_update.example.json")
    built = env.change_envelope(
        publisher="acme-feeds",
        sequence=104902,
        object="fixture",
        action="update",
        sport="sport:soccer",
        id="EVT-88213",
        changes={"startDate": "2026-09-19T14:15:00Z", "x_reason": "kick-off delayed 15 minutes"},
        date_published="2026-09-19T13:05:00Z",
    )
    assert built == expected
    assert list(built) == list(expected)  # same key order as the spec example
    assert validate_envelope(built) == []


def test_sport_is_bare_slug_and_defaults() -> None:
    e = env.change_envelope(publisher="p", sequence=1, object="fixture", action="update", sport="sport:soccer", changes={})
    assert e["sport"] == "soccer"
    assert e["openbookVersion"] == SPEC_VERSION
    assert e["datePublished"].endswith("Z")
    assert "id" not in e and "conflated" not in e
    assert validate_envelope(e) == []


def test_extension_fields_and_optionals() -> None:
    when = datetime(2026, 9, 19, 14, 37, 12, tzinfo=timezone.utc)
    e = env.change_envelope(
        publisher="p",
        sequence=2,
        object="odds",
        action="change",
        sport="soccer",
        id="EVT-1",
        changes=load("odds_change.example.json")["changes"],
        date_published=when,
        conflated=True,
        x={"reason": "late", "x_already": 1},
        msg_type="update",
        reason="price move",
        references=[1],
    )
    assert e["datePublished"] == "2026-09-19T14:37:12Z"
    assert e["x_reason"] == "late" and e["x_already"] == 1
    assert e["conflated"] is True and e["msgType"] == "update" and e["references"] == [1]
    assert validate_envelope(e) == []


def test_changes_must_be_dict() -> None:
    with pytest.raises(TypeError):
        env.change_envelope(publisher="p", sequence=1, object="fixture", action="update", sport="soccer", changes=[])  # type: ignore[arg-type]


def test_heartbeat_and_snapshot_complete_match_spec_examples() -> None:
    hb = env.heartbeat("acme-feeds", 104901, date_published="2026-09-19T14:37:25Z")
    assert hb == load("heartbeat.example.json")
    assert validate_envelope(hb) == []
    sc = env.snapshot_complete("acme-feeds", 104900, "fixture", "sport:soccer", id="EVT-88213", date_published="2026-09-19T14:37:20Z")
    assert sc == load("snapshot_complete.example.json")
    assert validate_envelope(sc) == []


def test_create_envelope_with_full_document_validates(fixture_doc: dict) -> None:
    body = {k: v for k, v in fixture_doc.items() if k not in ("openbookVersion", "sequence", "dateModified")}
    e = env.change_envelope(publisher="acme-feeds", sequence=3, object="fixture", action="create", sport="soccer", id=body["id"], changes=body)
    assert validate_envelope(e) == []


def test_merge_patch_minimal_diff() -> None:
    old = {"a": 1, "b": {"c": 1, "d": 2, "deep": {"x": 1}}, "l": [1, 2], "gone": 1, "same": "s"}
    new = {"a": 1, "b": {"c": 2, "deep": {"x": 1}}, "l": [1, 3], "new": True, "same": "s"}
    patch = env.merge_patch(old, new)
    assert patch == {"gone": None, "b": {"d": None, "c": 2}, "l": [1, 3], "new": True}
    assert env.apply_merge_patch(old, patch) == new
    assert env.merge_patch(new, new) == {}
    # lists are replaced whole, never diffed element-wise
    assert env.merge_patch({"l": [1, 2, 3]}, {"l": [1, 2]}) == {"l": [1, 2]}
    # type changes are changes even when == says otherwise (1 vs True)
    assert env.merge_patch({"v": 1}, {"v": True}) == {"v": True}


def test_apply_merge_patch_rfc7386_cases() -> None:
    # examples from RFC 7386 appendix A
    cases = [
        ({"a": "b"}, {"a": "c"}, {"a": "c"}),
        ({"a": "b"}, {"b": "c"}, {"a": "b", "b": "c"}),
        ({"a": "b"}, {"a": None}, {}),
        ({"a": "b", "b": "c"}, {"a": None}, {"b": "c"}),
        ({"a": ["b"]}, {"a": "c"}, {"a": "c"}),
        ({"a": "c"}, {"a": ["b"]}, {"a": ["b"]}),
        ({"a": {"b": "c"}}, {"a": {"b": "d", "c": None}}, {"a": {"b": "d"}}),
        ({"a": [{"b": "c"}]}, {"a": [1]}, {"a": [1]}),
        (["a", "b"], ["c", "d"], ["c", "d"]),
        ({"a": "b"}, ["c"], ["c"]),
        ({"a": "foo"}, None, None),
        ({"a": "foo"}, "bar", "bar"),
        ({"e": None}, {"a": 1}, {"e": None, "a": 1}),
        ([1, 2], {"a": "b", "c": None}, {"a": "b"}),
        ({}, {"a": {"bb": {"ccc": None}}}, {"a": {"bb": {}}}),
    ]
    for target, patch, result in cases:
        assert env.apply_merge_patch(target, patch) == result, (target, patch)


def test_apply_does_not_mutate() -> None:
    target = {"a": {"b": 1}}
    snapshot = json.loads(json.dumps(target))
    env.apply_merge_patch(target, {"a": {"b": None}})
    assert target == snapshot
