from __future__ import annotations

from pathlib import Path

from conftest import CAPTURES

from openbook_translate.captures import iter_captures


def test_iter_captures_json_and_jsonl() -> None:
    caps = list(iter_captures(CAPTURES))
    assert [c.path.name for c in caps][:1] == ["fixture-a.json"]
    assert caps[0].line is None and caps[0].label.endswith("fixture-a.json")
    jsonl = [c for c in caps if c.path.suffix == ".jsonl"]
    assert [c.line for c in jsonl] == [1, 2, 3, 4, 5]
    assert jsonl[0].label.endswith("stream.jsonl:1")
    assert jsonl[-1].raw == b"this line is not json"


def test_iter_captures_single_file_and_blank_lines(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    f.write_text("\n{}\n\n  \n{}\n")
    assert [c.line for c in iter_captures(f)] == [2, 5]
    (tmp_path / "ignored.txt").write_text("x")
    assert [c.path.name for c in iter_captures(tmp_path)] == ["s.jsonl", "s.jsonl"]
