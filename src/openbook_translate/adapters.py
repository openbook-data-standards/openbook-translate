from __future__ import annotations

from importlib.metadata import entry_points

from openbook_translate.abc import Translator


def load(name: str) -> Translator:
    matches = entry_points(group="openbook_translate.adapters").select(name=name)
    if not matches:
        raise KeyError(name)
    loaded = next(iter(matches)).load()
    if isinstance(loaded, type):
        return loaded()
    if isinstance(loaded, Translator):
        return loaded
    raise TypeError(f"{name} is not a Translator")
