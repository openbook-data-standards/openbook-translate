from __future__ import annotations

import copy


def native_id(document: dict, adapter: str) -> str | None:
    for item in document.get("identifier") or []:
        if isinstance(item, dict) and item.get("propertyID") == adapter:
            value = item.get("value")
            if isinstance(value, str) and value:
                return value
    return None


def with_native_id(document: dict, adapter: str, value: str) -> dict:
    out = copy.deepcopy(document)
    items = [item for item in (out.get("identifier") or []) if isinstance(item, dict)]
    rest = [item for item in items if item.get("propertyID") != adapter]
    rest.append({"propertyID": adapter, "value": value})
    out["identifier"] = rest
    return out
