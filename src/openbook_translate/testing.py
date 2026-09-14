"""Reusable contract tests for third-party adapters.

Subclass :class:`ContractSuite` in your own test module, point it at your
translator and give it fixtures::

    from pathlib import Path
    from openbook_translate.testing import ContractSuite
    from openbook_translate_kibl import KiblTranslator

    class TestKibl(ContractSuite):
        translator_cls = KiblTranslator
        source_id = "kibl"
        fixtures = [(Path("tests/data/fixture.json").read_bytes(), "EVT-1")]
        quarantine_fixtures = [b"not json", {"foo": "bar"}]
        captures_dir = Path("tests/captures")   # optional golden captures

pytest collects the ``test_*`` methods below against your class. Every method
asserts one clause of the Q96 contract; override ``make_translator`` or
``schema_stem_for`` when your adapter needs it. Requires pytest (a dev
dependency of your adapter, not of this package).
"""

from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, ClassVar

import pytest

from openbook_translate.abc import Translator
from openbook_translate.captures import iter_captures
from openbook_translate.gaps import GapCounter, counter_of
from openbook_translate.identifier import native_id
from openbook_translate.spec import document_stem, schema_allows_identifier, validate_document
from openbook_translate.types import Documents, Quarantine, Vendor

Fixture = tuple[bytes | dict, str]


@dataclass
class _State:
    translator: Translator
    quarantines: list[Quarantine] = field(default_factory=list)
    captures: tuple[int, int, int] | None = None  # records, mapped, quarantined


def _raw_and_parsed(inbound: bytes | dict) -> tuple[bytes, dict | None]:
    if isinstance(inbound, dict):
        return json.dumps(inbound, ensure_ascii=False).encode("utf-8"), inbound
    return inbound, None


def _describe(inbound: bytes | dict, limit: int = 80) -> str:
    text = json.dumps(inbound) if isinstance(inbound, dict) else inbound.decode("utf-8", "replace")
    return text if len(text) <= limit else text[: limit - 3] + "..."


class ContractSuite:
    """Contract tests for one :class:`Translator`. Subclass and set the class attributes."""

    translator_cls: ClassVar[type[Translator]]
    source_id: ClassVar[str] = "test-book"
    fixtures: ClassVar[list[Fixture]] = []
    """``(inbound raw bytes or parsed dict, expected native id)`` pairs that MUST map."""
    quarantine_fixtures: ClassVar[list[bytes | dict]] = []
    """Inputs that MUST quarantine (and never raise)."""
    reverse_supported: ClassVar[bool] = True
    captures_dir: ClassVar[Path | None] = None
    """Golden captures: every ``*.json`` / ``*.jsonl`` record here is translated."""

    # ---- hooks -----------------------------------------------------------

    def make_translator(self) -> Translator:
        return self.translator_cls()

    def schema_stem_for(self, document: dict) -> str | None:
        """Which vendored schema a document must validate against. Default: infer."""
        return document_stem(document)

    def translate(self, translator: Translator, inbound: bytes | dict) -> Documents | Quarantine:
        raw, parsed = _raw_and_parsed(inbound)
        return translator.translate(raw, source_id=self.source_id, parsed=parsed)

    # ---- pytest plumbing -------------------------------------------------

    @pytest.fixture
    def translator(self, request: pytest.FixtureRequest) -> Translator:
        """One translator per test class, so gaps accumulate across the run.

        Function-scoped on purpose (class-scoped instance-method fixtures are
        deprecated in pytest); the instance is cached on the class and the gap
        report is printed once when the class finishes."""
        cls = type(self)
        state: _State | None = cls.__dict__.get("_contract_state")
        if state is None:
            state = _State(translator=self.make_translator(), quarantines=[])
            setattr(cls, "_contract_state", state)
            class_node = request.node.getparent(pytest.Class)
            config = request.config

            def finish() -> None:
                self._print_gap_report(config, state)
                if cls.__dict__.get("_contract_state") is state:
                    delattr(cls, "_contract_state")

            (class_node or request.node).addfinalizer(finish)
        return state.translator

    def _note_quarantine(self, q: Quarantine) -> None:
        state: _State | None = type(self).__dict__.get("_contract_state")
        if state is not None:
            state.quarantines.append(q)

    def _print_gap_report(self, config: pytest.Config, state: _State) -> None:
        """Gap report for this class's run. Counts cover every translate call the
        suite made, so one fixture translated by several tests counts several times."""
        t = state.translator
        gaps = counter_of(t)
        by_reason: dict[str, int] = {}
        for q in state.quarantines:
            by_reason[q.reason] = by_reason.get(q.reason, 0) + 1
        lines = [f"gap report: {getattr(t, 'name', type(t).__name__)} ({self.source_id})"]
        if state.captures is not None:
            total, mapped, quarantined = state.captures
            lines.append(f"captures: {total} record(s), {mapped} mapped, {quarantined} quarantined")
        lines.append("mapping gaps: " + (gaps.format() if gaps is not None else "adapter exposes no GapCounter as .gaps"))
        if by_reason:
            lines.append("quarantines by reason: " + ", ".join(f"{k}={v}" for k, v in sorted(by_reason.items())))
        else:
            lines.append("quarantines: none")
        reporter = config.pluginmanager.get_plugin("terminalreporter")
        capman = config.pluginmanager.get_plugin("capturemanager")
        if reporter is None:  # pragma: no cover - only without a terminal
            print("\n".join(lines))
            return
        with capman.global_and_fixture_disabled() if capman is not None else nullcontext():
            reporter.ensure_newline()
            reporter.write_sep("-", lines[0])
            for line in lines[1:]:
                reporter.write_line(line)

    def _mapped(self, translator: Translator) -> list[tuple[Fixture, Documents]]:
        if not self.fixtures:
            pytest.skip("no fixtures declared")
        out = []
        for fx in self.fixtures:
            inbound, expected = fx
            result = self.translate(translator, inbound)
            assert isinstance(result, Documents), (
                f"fixture for {expected!r} did not map: {result!r} ({_describe(inbound)})"
            )
            out.append((fx, result))
        return out

    # ---- the contract ----------------------------------------------------

    def test_translator_has_name(self, translator: Translator) -> None:
        assert isinstance(translator, Translator)
        assert isinstance(getattr(translator, "name", None), str) and translator.name

    def test_fixtures_translate(self, translator: Translator) -> None:
        for (_, expected), result in self._mapped(translator):
            assert result.documents, f"empty Documents for {expected!r}"
            for doc in result.documents:
                assert isinstance(doc, dict)

    def test_documents_validate(self, translator: Translator) -> None:
        for (_, expected), result in self._mapped(translator):
            for doc in result.documents:
                stem = self.schema_stem_for(doc)
                assert stem is not None, f"cannot tell which schema the document for {expected!r} is (override schema_stem_for)"
                errors = validate_document(stem, doc)
                assert not errors, f"document for {expected!r} invalid against {stem}: {errors[0]}"

    def test_documents_carry_native_id(self, translator: Translator) -> None:
        """Every document whose schema has ``identifier`` carries the native id, and
        at least one document per record does (types like market have no
        identifier property and are excused)."""
        for (_, expected), result in self._mapped(translator):
            carried = 0
            for doc in result.documents:
                stem = self.schema_stem_for(doc)
                got = native_id(doc, translator.name)
                if got == expected:
                    carried += 1
                    continue
                if stem is not None and not schema_allows_identifier(stem) and "identifier" not in doc:
                    continue
                pytest.fail(
                    f"identifier[{{propertyID: {translator.name!r}}}] is {got!r}, expected {expected!r}"
                    + (f" (document type {stem})" if stem else "")
                )
            assert carried, f"no document for {expected!r} carries the native id on identifier"

    def test_quarantine_fixtures_quarantine(self, translator: Translator) -> None:
        if not self.quarantine_fixtures:
            pytest.skip("no quarantine fixtures declared")
        for inbound in self.quarantine_fixtures:
            raw, _ = _raw_and_parsed(inbound)
            try:
                result = self.translate(translator, inbound)
            except Exception as e:  # noqa: BLE001 - the contract: quarantine never raises
                pytest.fail(f"translate raised {e!r} for {_describe(inbound)}; it must return Quarantine")
            assert isinstance(result, Quarantine), f"expected Quarantine, got {result!r} for {_describe(inbound)}"
            assert result.raw == raw, "Quarantine.raw must be the inbound bytes untouched"
            assert isinstance(result.reason, str) and result.reason
            self._note_quarantine(result)

    def test_reverse(self, translator: Translator) -> None:
        for (_, expected), result in self._mapped(translator):
            for doc in result.documents:
                try:
                    back = translator.reverse(doc)
                except Exception as e:  # noqa: BLE001
                    pytest.fail(f"reverse raised {e!r}; it must return Vendor or Quarantine")
                if not self.reverse_supported:
                    assert isinstance(back, Quarantine), f"reverse_supported is False but reverse returned {back!r}"
                    self._note_quarantine(back)
                    continue
                assert isinstance(back, Vendor), f"reverse did not round-trip for {expected!r}: {back!r}"
                assert isinstance(back.raw, bytes)
                again = translator.translate(back.raw, source_id=self.source_id, parsed=back.parsed)
                assert isinstance(again, Documents), f"translate(reverse(x)) did not map for {expected!r}: {again!r}"
                ids = {native_id(d, translator.name) for d in again.documents}
                assert expected in ids, f"round trip lost the native id {expected!r}: {ids}"

    def test_captures(self, translator: Translator) -> None:
        if self.captures_dir is None:
            pytest.skip("no captures_dir declared")
        captures = list(iter_captures(self.captures_dir))
        assert captures, f"no *.json / *.jsonl captures under {self.captures_dir}"
        mapped = quarantined = 0
        problems: list[str] = []
        for cap in captures:
            try:
                result = translator.translate(cap.raw, source_id=self.source_id)
            except Exception as e:  # noqa: BLE001
                problems.append(f"{cap.label}: translate raised {e!r}")
                continue
            if isinstance(result, Quarantine):
                quarantined += 1
                self._note_quarantine(result)
                continue
            assert isinstance(result, Documents), f"{cap.label}: {result!r}"
            mapped += 1
            for doc in result.documents:
                stem = self.schema_stem_for(doc)
                if stem is None:
                    problems.append(f"{cap.label}: cannot tell which schema the document is")
                    continue
                errors = validate_document(stem, doc)
                if errors:
                    problems.append(f"{cap.label}: invalid against {stem}: {errors[0]}")
        state: _State | None = type(self).__dict__.get("_contract_state")
        if state is not None:
            state.captures = (len(captures), mapped, quarantined)
        assert not problems, "\n".join(problems)


__all__ = ["ContractSuite", "Fixture", "GapCounter"]
