from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent / "data"
CAPTURES = Path(__file__).resolve().parent / "captures"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def fixture_doc() -> dict:
    return load("fixture.example.json")


@pytest.fixture(scope="session")
def market_doc() -> dict:
    return load("market.example.json")
