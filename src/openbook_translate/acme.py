from __future__ import annotations

import json
from datetime import datetime, timezone

from openbook_translate.adapter import Adapter, Inbound, Quarantine, ReverseOk, TranslateOk

SPEC = "0.3.0-draft"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AcmeAdapter(Adapter):
    source_id = "acme"

    def translate(self, inbound: Inbound) -> TranslateOk | Quarantine:
        if inbound.source != self.source_id:
            return Quarantine(inbound, f"source {inbound.source!r} is not acme")
        parsed = inbound.parsed
        if parsed is None:
            try:
                loaded = json.loads(inbound.raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                return Quarantine(inbound, f"not JSON: {e}")
            if not isinstance(loaded, dict):
                return Quarantine(inbound, "JSON root must be an object")
            parsed = loaded
        native_id = parsed.get("acmeId")
        if not native_id:
            return Quarantine(inbound, "missing acmeId")
        home = parsed.get("home") or "Home"
        away = parsed.get("away") or "Away"
        stamp = parsed.get("startDate") or "2026-09-19T14:00:00Z"
        doc = {
            "openbookVersion": SPEC,
            "id": str(native_id),
            "sequence": 1,
            "dateModified": _now(),
            "name": f"{home} v {away}",
            "sport": {"id": "sport:soccer", "name": "Soccer"},
            "league": {
                "id": "LG-ACME",
                "name": "Acme League",
                "territory": "GB-ENG",
                "competitionType": "league",
            },
            "startDate": stamp,
            "participants": [
                {"id": "T-H", "name": home, "territory": "GB-ENG", "role": "home", "order": 1},
                {"id": "T-A", "name": away, "territory": "GB-ENG", "role": "away", "order": 2},
            ],
            "identifier": [{"propertyID": "acme", "value": str(native_id)}],
        }
        return TranslateOk([doc])

    def reverse(self, document: dict) -> ReverseOk | Quarantine:
        keys = document.get("identifier") or []
        native = None
        for k in keys:
            if k.get("propertyID") == "acme":
                native = k.get("value")
                break
        if not native:
            return Quarantine(None, "no identifier propertyID=acme", document)
        parts = document.get("participants") or []
        home = next((p["name"] for p in parts if p.get("role") == "home"), "Home")
        away = next((p["name"] for p in parts if p.get("role") == "away"), "Away")
        parsed = {
            "acmeId": native,
            "home": home,
            "away": away,
            "startDate": document.get("startDate"),
        }
        raw = json.dumps(parsed, separators=(",", ":")).encode("utf-8")
        return ReverseOk(raw=raw, parsed=parsed)
