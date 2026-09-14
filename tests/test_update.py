from __future__ import annotations

from pathlib import Path

import pytest

from openbook_translate import spec as spec_mod
from openbook_translate import update as update_mod
from openbook_translate.cli import main


def _fake_spec(root: Path, *, version: str = "0.3.0-draft") -> Path:
    """A spec checkout that mirrors exactly what we vendor."""
    (root / "spec").mkdir(parents=True)
    (root / "schema").mkdir()
    (root / "vocabularies").mkdir()
    (root / "spec" / "openbook.md").write_text(f"Version `{version}` · today\n", encoding="utf-8")
    for path in spec_mod.SCHEMA_DIR.glob("*.json"):
        (root / "schema" / path.name).write_bytes(path.read_bytes())
    for name in spec_mod.VOCABULARY_NAMES:
        (root / "vocabularies" / name).write_bytes((spec_mod.VOCAB_DIR / name).read_bytes())
    return root


def test_in_sync_with_identical_checkout(tmp_path: Path) -> None:
    assert update_mod.check(spec_root=_fake_spec(tmp_path / "openbook")) == []


def test_detects_schema_added_removed_and_changed(tmp_path: Path) -> None:
    root = _fake_spec(tmp_path / "openbook")
    (root / "schema" / "wager.schema.json").write_text("{}")
    (root / "schema" / "toss.schema.json").unlink()
    (root / "schema" / "common.schema.json").write_text("{}")
    problems = update_mod.check(spec_root=root)
    assert "wager.schema.json: in spec, not vendored" in problems
    assert "toss.schema.json: vendored, not in spec" in problems
    assert "common.schema.json: differs from spec" in problems


def test_detects_vocabulary_drift(tmp_path: Path) -> None:
    root = _fake_spec(tmp_path / "openbook")
    (root / "vocabularies" / "sports.md").write_text("| `sport:curling` | Curling |\n")
    (root / "vocabularies" / "deprecated.json").unlink()
    problems = update_mod.check(spec_root=root)
    assert "vocabularies/sports.md: differs from spec" in problems
    assert "vocabularies/deprecated.json: could not read from spec" in problems


def test_detects_stamp_drift(tmp_path: Path) -> None:
    problems = update_mod.check(spec_root=_fake_spec(tmp_path / "openbook", version="0.4.0-draft"))
    assert problems == ["openbook-spec-version '0.3.0-draft' != spec '0.4.0-draft'"]


def test_fetch_mode_uses_remote_readers(monkeypatch: pytest.MonkeyPatch) -> None:
    vendored = set(spec_mod.schema_names())
    remote_names = vendored | {"wager.schema.json"}  # spec ships one we don't vendor

    def fake_get_bytes(url: str) -> bytes:
        name = url.rsplit("/", 1)[1]
        if url == spec_mod.REMOTE_SPEC_URL:
            return f"Version `{spec_mod.spec_version_stamp()}`\n".encode()
        if "/vocabularies/" in url:
            return (spec_mod.VOCAB_DIR / name).read_bytes()
        return (spec_mod.SCHEMA_DIR / name).read_bytes()

    monkeypatch.setattr(update_mod, "_get_bytes", fake_get_bytes)
    monkeypatch.setattr(update_mod, "_remote_schema_names", lambda: remote_names)
    problems = update_mod.check(fetch=True)
    assert problems == ["wager.schema.json: in spec, not vendored"]


def test_check_requires_a_mode() -> None:
    with pytest.raises(ValueError):
        update_mod.check()


def test_find_spec_root_finds_sibling_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    work = tmp_path / "work"
    (work / "openbook-translate" / "deep").mkdir(parents=True)
    _fake_spec(work / "openbook")
    assert update_mod.find_spec_root(work / "openbook-translate" / "deep") == work / "openbook"
    # the package's own schema dir is never mistaken for the spec
    assert update_mod.find_spec_root(tmp_path / "elsewhere") is None
    monkeypatch.chdir(work / "openbook-translate")
    assert update_mod.find_spec_root() == work / "openbook"


def test_cli_update_local(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _fake_spec(tmp_path / "openbook")
    assert main(["update", "--spec-root", str(root)]) == 0
    assert "in sync" in capsys.readouterr().out
    (root / "schema" / "common.schema.json").write_text("{}")
    assert main(["update", "--spec-root", str(root)]) == 1
    assert "differs from spec" in capsys.readouterr().err


def test_cli_update_local_without_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(update_mod, "find_spec_root", lambda start=None: None)
    monkeypatch.setattr("openbook_translate.cli.find_spec_root", lambda start=None: None)
    assert main(["update", "--local"]) == 2
    assert "no spec checkout" in capsys.readouterr().err
