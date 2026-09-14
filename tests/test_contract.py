from openbook_translate.acme import AcmeAdapter
from openbook_translate.adapter import Inbound, Quarantine, ReverseOk, TranslateOk
from openbook_translate.validate import iter_errors, native_keys

ADAPTERS = [AcmeAdapter()]


def test_happy_path_validates_and_round_trips():
    adapter = AcmeAdapter()
    inbound = Inbound(
        source=adapter.source_id,
        raw=b'{"acmeId":"EVT-1","home":"Arsenal","away":"Manchester City"}',
        parsed=None,
    )
    out = adapter.translate(inbound)
    assert isinstance(out, TranslateOk)
    assert out.documents
    for doc in out.documents:
        errs = iter_errors(doc)
        assert not errs, errs
        assert native_keys(doc), "success must carry native identifier"
        back = adapter.reverse(doc)
        assert isinstance(back, ReverseOk)
        assert back.raw
        again = adapter.translate(Inbound(adapter.source_id, back.raw, back.parsed))
        assert isinstance(again, TranslateOk)
        assert native_keys(again.documents[0])[0]["value"] == native_keys(doc)[0]["value"]


def test_unknown_is_quarantine_keeps_raw():
    adapter = AcmeAdapter()
    inbound = Inbound(source=adapter.source_id, raw=b"not-json{{{", parsed=None)
    out = adapter.translate(inbound)
    assert isinstance(out, Quarantine)
    assert out.inbound is not None
    assert out.inbound.raw == inbound.raw
    assert out.reason
