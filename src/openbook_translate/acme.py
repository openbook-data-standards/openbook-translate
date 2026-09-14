from __future__ import annotations

import json

from openbook_translate.abc import Translator
from openbook_translate.identifier import native_id, with_native_id
from openbook_translate.spec import document_stem, schema_allows_identifier, validate_document
from openbook_translate.types import Documents, Quarantine, Vendor


class AcmeTranslator(Translator):
    """Synthetic adapter for contract tests. Not a vendor."""

    name = "acme"

    def translate(
        self,
        raw: bytes,
        *,
        source_id: str,
        parsed: dict | None = None,
    ) -> Documents | Quarantine:
        record, err = _record(raw, parsed)
        if err:
            return Quarantine(raw=raw, reason=err)
        native = record.get("id")
        stem = record.get("type")
        body = record.get("openbook")
        if not isinstance(native, str) or not native:
            return Quarantine(raw=raw, reason="unmapped: missing id")
        if not isinstance(stem, str) or not stem:
            return Quarantine(raw=raw, reason="unmapped: missing type")
        if not isinstance(body, dict):
            return Quarantine(raw=raw, reason="unmapped: missing openbook")
        if not schema_allows_identifier(stem):
            return Quarantine(raw=raw, reason=f"unmapped: {stem} has no identifier")
        document = with_native_id(body, self.name, native)
        if "source" in document:
            document["source"] = source_id
        errors = validate_document(stem, document)
        if errors:
            return Quarantine(raw=raw, reason=f"unmapped: {errors[0]}")
        return Documents(documents=(document,))

    def reverse(self, document: dict) -> Vendor | Quarantine:
        raw_doc = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        value = native_id(document, self.name)
        if not value:
            return Quarantine(raw=raw_doc, reason="unmapped: missing native id")
        stem = document_stem(document)
        if stem is None:
            return Quarantine(raw=raw_doc, reason="unmapped: unknown document type")
        parsed = {"id": value, "type": stem, "openbook": document}
        raw = json.dumps(parsed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return Vendor(raw=raw, parsed=parsed)


def _record(raw: bytes, parsed: dict | None) -> tuple[dict | None, str | None]:
    if parsed is not None:
        if not isinstance(parsed, dict):
            return None, "unmapped: parsed is not a dict"
        return parsed, None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return None, f"unmapped: {e}"
    if not isinstance(obj, dict):
        return None, "unmapped: JSON is not an object"
    return obj, None
