"""Map one vendor record to OpenBook documents and back (Q96).

The contract is :class:`Translator`: one record in, sync ``translate`` /
``reverse``, quarantine never raises, native id on ``identifier``. Everything
else here is tooling for the adapters that implement it: vendored schemas and
validation (:mod:`spec`), controlled vocabularies (:mod:`vocab`), declarative
mapping tables (:mod:`tables`), gap counting (:mod:`gaps`), envelope building
(:mod:`envelope`), and a reusable contract test suite (:mod:`testing`).
"""

from openbook_translate.abc import Translator
from openbook_translate.acme import AcmeTranslator
from openbook_translate.spec import SPEC_COMMIT, SPEC_VERSION
from openbook_translate.types import Documents, Quarantine, Vendor

__version__ = "0.1.0"

__all__ = [
    "SPEC_COMMIT",
    "SPEC_VERSION",
    "AcmeTranslator",
    "Documents",
    "Quarantine",
    "Translator",
    "Vendor",
    "__version__",
]
