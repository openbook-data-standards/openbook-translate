from __future__ import annotations

from openbook_translate.acme import AcmeTranslator
from openbook_translate.gaps import Gap, GapCounter, GapSink, counter_of
from openbook_translate.tables import Unmapped


class ListSink:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, object]] = []

    def record(self, kind: str, vendor_value: str, sample: object | None = None) -> None:
        self.rows.append((kind, vendor_value, sample))


def test_record_and_report_sorted_by_count() -> None:
    g = GapCounter()
    g.record("sport", "CURL", sample={"id": 1})
    g.record("sport", "CURL", sample={"id": 2})  # first sample kept
    g.record("segment", "OT")
    g.record("market_type", 42)  # non-string vendor values are stringified
    g.record("sport", "BOWL")
    report = g.report()
    assert report[0] == Gap(kind="sport", vendor="CURL", count=2, sample={"id": 1})
    assert [(x.kind, x.vendor) for x in report[1:]] == [("market_type", "42"), ("segment", "OT"), ("sport", "BOWL")]
    assert g.report(top=1) == report[:1]
    assert g.total == 5 and len(g) == 4
    d = g.to_dict()
    assert d["total"] == 5 and d["distinct"] == 4 and d["gaps"][0]["vendor"] == "CURL"
    text = g.format()
    assert text.splitlines()[0] == "5 gap(s), 4 distinct"
    assert "CURL" in text
    g.clear()
    assert g.total == 0 and g.format() == "no gaps"


def test_sink_receives_every_record() -> None:
    sink = ListSink()
    assert isinstance(sink, GapSink)
    g = GapCounter(sink=sink)
    g.record("sport", "CURL", sample="A-1")
    g.record_unmapped(Unmapped(kind="segment", vendor="OT", id="segment:unknown:unknown", x_field="x_aSegmentId"))
    assert sink.rows == [("sport", "CURL", "A-1"), ("segment", "OT", None)]


def test_counter_of() -> None:
    t = AcmeTranslator()
    assert counter_of(t) is t.gaps
    assert counter_of(object()) is None

    class Fake:
        gaps = "not a counter"

    assert counter_of(Fake()) is None
