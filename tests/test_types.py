from __future__ import annotations

import base64
from datetime import datetime, timezone

import pytest

from openbook_translate import types
from openbook_translate.types import REASONS, Documents, Quarantine


def test_reason_vocabulary() -> None:
    assert types.UNMAPPED_SPORT == "unmapped-sport"
    assert types.UNMAPPED_LEAGUE == "unmapped-league"
    assert types.UNMAPPED_MARKET_TYPE == "unmapped-market-type"
    assert types.UNMAPPED_SEGMENT == "unmapped-segment"
    assert types.UNMAPPED_PARTICIPANT == "unmapped-participant"
    assert types.SCHEMA_INVALID == "schema-invalid"
    assert types.PARSE_ERROR == "parse-error"
    assert types.OTHER == "other"
    assert len(REASONS) == 8


def test_quarantine_positional_is_backwards_compatible() -> None:
    q = Quarantine(b"raw", "other")
    assert q.raw == b"raw" and q.reason == "other"
    assert q.source_id is None and q.adapter is None and q.detail is None and q.received_at is None
    assert Quarantine(raw=b"raw", reason="other") == q


def test_quarantine_to_dict_round_trip() -> None:
    when = datetime(2026, 9, 19, 14, 37, 25, tzinfo=timezone.utc)
    q = Quarantine(b"\x00\xffbinary", "parse-error", source_id="kibl", adapter="kibl", detail={"line": 3}, received_at=when)
    d = q.to_dict()
    assert d["raw"] == base64.b64encode(b"\x00\xffbinary").decode()
    assert d["reason"] == "parse-error" and d["source_id"] == "kibl" and d["adapter"] == "kibl"
    assert d["detail"] == {"line": 3}
    assert d["received_at"] == "2026-09-19T14:37:25+00:00"
    back = Quarantine.from_dict({**d, "extra": "ignored"})
    assert back.raw == q.raw and back.reason == q.reason and back.detail == q.detail
    assert back.received_at == "2026-09-19T14:37:25+00:00"


def test_quarantine_is_frozen() -> None:
    q = Quarantine(b"", "other")
    with pytest.raises(AttributeError):
        q.reason = "x"  # type: ignore[misc]


def test_documents_must_not_be_empty() -> None:
    with pytest.raises(ValueError):
        Documents(documents=())
