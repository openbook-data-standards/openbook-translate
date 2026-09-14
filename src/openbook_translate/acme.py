"""The synthetic **acme** adapter: the contract's reference implementer.

Not a vendor. It exists so the contract suite has something to run against and
so adapter authors have a small, complete example of the tools: a mapping
table (``acme.tables.json``), the quarantine reason vocabulary, the gap
counter, and native-id stamping.

An acme record is::

    {"id": "A-88213", "type": "fixture", "openbook": {...}, "sport": "SOCC"}

``type`` is the vendored schema stem, ``openbook`` the document body, ``id``
the native id. ``sport`` is optional: a vendor sport code looked up in the
table. On a hit it fills ``openbook.sport`` when the body lacks one; on a miss
it fills ``sport:unknown``, stamps the code on ``x_acmeSportId`` and records a
gap. Nothing is dropped and nothing raises.
"""

from __future__ import annotations

import json
from importlib.resources import files

from openbook_translate.abc import Translator
from openbook_translate.gaps import GapCounter
from openbook_translate.identifier import native_id, with_native_id
from openbook_translate.spec import (
    document_stem,
    schema_allows,
    schema_allows_identifier,
    validate_document,
)
from openbook_translate.tables import MappingTable, Unmapped
from openbook_translate.types import (
    OTHER,
    PARSE_ERROR,
    SCHEMA_INVALID,
    Documents,
    Quarantine,
    Vendor,
)
from openbook_translate.vocab import SPORT_NAMES

TABLES_PATH = files("openbook_translate").joinpath("acme.tables.json")


class AcmeTranslator(Translator):
    """Synthetic adapter for contract tests. Not a vendor."""

    name = "acme"

    def __init__(self, tables: MappingTable | None = None, gaps: GapCounter | None = None) -> None:
        self.tables = tables or MappingTable.load(json.loads(TABLES_PATH.read_text(encoding="utf-8")))
        self.gaps = gaps or GapCounter()

    def translate(
        self,
        raw: bytes,
        *,
        source_id: str,
        parsed: dict | None = None,
    ) -> Documents | Quarantine:
        def quarantine(reason: str, detail: str) -> Quarantine:
            return Quarantine(raw, reason, source_id=source_id, adapter=self.name, detail=detail)

        record, err = _record(raw, parsed)
        if err:
            return quarantine(PARSE_ERROR, err)
        assert record is not None
        native = record.get("id")
        stem = record.get("type")
        body = record.get("openbook")
        if not isinstance(native, str) or not native:
            return quarantine(OTHER, "missing id")
        if not isinstance(stem, str) or not stem:
            return quarantine(OTHER, "missing type")
        if not isinstance(body, dict):
            return quarantine(OTHER, "missing openbook")
        if not schema_allows_identifier(stem):
            return quarantine(OTHER, f"{stem} has no identifier")
        document = with_native_id(body, self.name, native)
        # Stamp the authoritative source on any document type that declares a
        # `source` property (e.g. market), even if the vendor body omitted it,
        # mirroring how the native identifier is always stamped. Types without a
        # source property (fixture, publisher) are left untouched so we never add
        # a field their schema forbids.
        if schema_allows(stem, "source"):
            document["source"] = source_id
        vendor_sport = record.get("sport")
        if vendor_sport is not None and schema_allows(stem, "sport") and "sport" not in document:
            mapped = self.tables.lookup("sport", vendor_sport)
            if isinstance(mapped, Unmapped):
                self.gaps.record_unmapped(mapped, sample=native)
                document = mapped.stamp(document)
                document["sport"] = {"id": mapped.id, "name": SPORT_NAMES[mapped.id]}
            else:
                document["sport"] = {"id": mapped.id, "name": mapped.name or SPORT_NAMES[mapped.id]}
        errors = validate_document(stem, document)
        if errors:
            return quarantine(SCHEMA_INVALID, errors[0])
        return Documents(documents=(document,))

    def reverse(self, document: dict) -> Vendor | Quarantine:
        raw_doc = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        value = native_id(document, self.name)
        if not value:
            return Quarantine(raw_doc, OTHER, adapter=self.name, detail="missing native id")
        stem = document_stem(document)
        if stem is None:
            return Quarantine(raw_doc, OTHER, adapter=self.name, detail="unknown document type")
        parsed = {"id": value, "type": stem, "openbook": document}
        raw = json.dumps(parsed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return Vendor(raw=raw, parsed=parsed)


def _record(raw: bytes, parsed: dict | None) -> tuple[dict | None, str | None]:
    if parsed is not None:
        if not isinstance(parsed, dict):
            return None, "parsed is not a dict"
        return parsed, None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return None, str(e)
    if not isinstance(obj, dict):
        return None, "JSON is not an object"
    return obj, None
