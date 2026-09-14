from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import CAPTURES, DATA

from openbook_translate.cli import main

FIXTURE = json.loads((DATA / "fixture.example.json").read_text())


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    try:
        code = main(list(argv))
    except SystemExit as e:  # argparse usage errors
        code = int(e.code or 0)
    out, err = capsys.readouterr()
    return code, out, err


def test_run_documents_exit_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "rec.json"
    f.write_text(json.dumps({"id": "A-1", "type": "fixture", "openbook": FIXTURE}))
    code, out, _ = _run(capsys, "run", "acme", str(f), "--source-id", "acme-book")
    assert code == 0
    lines = [json.loads(line) for line in out.splitlines()]
    assert len(lines) == 1 and "quarantine" not in lines[0]
    assert {"propertyID": "acme", "value": "A-1"} in lines[0]["identifier"]


def test_run_jsonl_mixed_exit_0_and_quarantine_lines(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "rec.jsonl"
    f.write_text(json.dumps({"id": "A-1", "type": "fixture", "openbook": FIXTURE}) + "\n\nnot json\n")
    code, out, _ = _run(capsys, "run", "acme", str(f), "--source-id", "acme-book", "--jsonl", "--parsed")
    assert code == 0
    lines = [json.loads(line) for line in out.splitlines()]
    assert len(lines) == 2
    assert "quarantine" not in lines[0]
    assert lines[1]["quarantine"] is True and lines[1]["reason"] == "parse-error" and lines[1]["source_id"] == "acme-book"


def test_run_only_quarantine_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "bad.json"
    f.write_text("garbage")
    code, out, _ = _run(capsys, "run", "acme", str(f), "--source-id", "acme-book")
    assert code == 1
    assert json.loads(out)["quarantine"] is True


def test_run_stdin(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import io
    import sys

    payload = json.dumps({"id": "A-7", "type": "fixture", "openbook": FIXTURE}).encode()
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(payload)))
    code, out, _ = _run(capsys, "run", "acme", "-", "--source-id", "acme-book")
    assert code == 0 and '"value":"A-7"' in out


def test_run_usage_errors_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "rec.json"
    f.write_text("{}")
    code, _, err = _run(capsys, "run", "no-such-adapter", str(f), "--source-id", "x")
    assert code == 2 and "no adapter" in err
    code, _, _ = _run(capsys, "run", "acme", str(f))  # missing --source-id
    assert code == 2
    empty = tmp_path / "empty.jsonl"
    empty.write_text("\n")
    code, _, err = _run(capsys, "run", "acme", str(empty), "--source-id", "x", "--jsonl")
    assert code == 2 and "no records" in err


def test_validate_mixed(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(
        capsys,
        "validate",
        str(DATA / "fixture_update.example.json"),
        str(DATA / "market.example.json"),
        str(DATA / "invalid" / "missing-sequence.json"),
    )
    assert code == 1
    assert out.count("OK  ") == 2 and "FAIL" in out and "sequence" in out


def test_validate_all_examples_ok(capsys: pytest.CaptureFixture[str]) -> None:
    files = sorted(str(p) for p in DATA.glob("*.json"))
    code, out, _ = _run(capsys, "validate", *files)
    assert code == 0 and "FAIL" not in out


def test_validate_stem_override(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "whatever.json"
    f.write_text(json.dumps(FIXTURE))
    code, out, _ = _run(capsys, "validate", str(f))
    assert code == 1 and "unknown schema stem 'whatever'" in out
    code, _, _ = _run(capsys, "validate", str(f), "--stem", "fixture")
    assert code == 0
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    code, out, _ = _run(capsys, "validate", str(bad))
    assert code == 1 and "cannot read JSON" in out


def test_gaps_report(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "gaps", str(CAPTURES), "--adapter", "acme", "--source-id", "acme-book")
    assert code == 0
    assert "acme: 6 record(s), 4 mapped, 2 quarantined" in out
    assert "sport" in out and "CURL" in out and "     2  sport" in out
    assert "quarantines by reason" in out and "parse-error" in out and "other" in out


def test_gaps_usage_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = _run(capsys, "gaps", str(tmp_path / "missing"), "--adapter", "acme", "--source-id", "x")
    assert code == 2 and "does not exist" in err
    code, _, err = _run(capsys, "gaps", str(tmp_path), "--adapter", "acme", "--source-id", "x")
    assert code == 2 and "no *.json" in err


def test_no_command_is_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, _, _ = _run(capsys)
    assert code == 2
