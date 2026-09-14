"""The acme adapter run through the reusable contract suite.

This file doubles as the template a private adapter copies: subclass
``ContractSuite``, set the class attributes, done.
"""

from __future__ import annotations

import json

from conftest import CAPTURES, load

from openbook_translate.acme import AcmeTranslator
from openbook_translate.testing import ContractSuite

FIXTURE = load("fixture.example.json")
MARKET = load("market.example.json")
NO_SPORT = {k: v for k, v in FIXTURE.items() if k != "sport"}


class TestAcmeContract(ContractSuite):
    translator_cls = AcmeTranslator
    source_id = "acme-book"
    fixtures = [
        # raw bytes in
        (json.dumps({"id": "A-88213", "type": "fixture", "openbook": FIXTURE}).encode(), "A-88213"),
        # parsed dict in, sport resolved through the mapping table
        ({"id": "A-2", "type": "fixture", "sport": "SOCC", "openbook": NO_SPORT}, "A-2"),
        # unmapped sport: still maps (sport:unknown + x_acmeSportId), gap counted
        ({"id": "A-3", "type": "fixture", "sport": "CURL", "openbook": NO_SPORT}, "A-3"),
    ]
    quarantine_fixtures = [
        b"not json",
        b"[1, 2, 3]",
        {"type": "fixture", "openbook": FIXTURE},  # missing id
        {"id": "M-1", "type": "market", "openbook": MARKET},  # market has no identifier
    ]
    reverse_supported = True
    captures_dir = CAPTURES


class TestAcmeWithoutReverse(ContractSuite):
    """A translator whose ``reverse`` always quarantines still passes with ``reverse_supported = False``."""

    class _NoReverse(AcmeTranslator):
        def reverse(self, document):  # type: ignore[override]
            from openbook_translate.types import OTHER, Quarantine

            return Quarantine(b"", OTHER, adapter=self.name, detail="reverse not supported")

    translator_cls = _NoReverse
    fixtures = [({"id": "A-9", "type": "fixture", "openbook": FIXTURE}, "A-9")]
    reverse_supported = False
