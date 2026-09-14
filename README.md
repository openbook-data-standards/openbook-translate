# openbook-translate

Apache-2.0 library for mapping **one inbound vendor record** onto OpenBook
documents, and back. OpenBook is the target language; this package is not the
specification (Q96). It ships the tools an adapter needs and never a vendor
adapter: vendored schemas and validation, controlled vocabularies, declarative
mapping tables, gap counting, envelope building, a reusable contract test
suite, and a CLI.

Vendored JSON Schema and vocabulary files stay **CC BY 4.0** (see `NOTICE`).
Schemas are from OpenBook spec version **`0.3.0-draft`**
(`openbook_translate.SPEC_VERSION`; the spec commit is `SPEC_COMMIT`).

## Contract

`Translator` is an ABC. One record in. Two sync methods:

- `translate(raw, *, source_id, parsed=None)`: vendor bytes, optional already-parsed dict, and the OpenBook source id, to OpenBook documents or **quarantine** (`raw` + `reason`). Unmapped records quarantine. They do not raise and they are not skipped.
- `reverse(document)`: one OpenBook document to vendor bytes and an optional dict.

A successful map **MUST** put the native id on `identifier` (`propertyID` is the adapter name, `value` is the native id) so `reverse` can round-trip.

The official implementer is the synthetic **acme** adapter (contract tests only). Community adapters MAY be published as `openbook-translate-kibl` and similar. This project will not ship vendor adapters and never decides vendor mappings.

## Install

From a release tag (see [Release](#release)). Slim images without git use the tarball form.

```bash
# git form
pip install "openbook-translate @ git+https://github.com/openbook-data-standards/openbook-translate@v0.1.0"

# tarball form (no git needed)
pip install "https://github.com/openbook-data-standards/openbook-translate/archive/refs/tags/v0.1.0.tar.gz"
```

In `pyproject.toml`:

```toml
dependencies = [
  "openbook-translate @ git+https://github.com/openbook-data-standards/openbook-translate@v0.1.0",
]
```

Python 3.11+. Runtime dependencies: `jsonschema`, `referencing`. Schemas, vocabularies and the spec stamp are package data, so a wheel install works the same as a checkout.

For development:

```bash
pip install -e '.[dev]'
pytest
```

## For adapter authors

The walkthrough uses acme. Replace `acme` with your adapter name throughout.

### 1. A mapping table is data, not code

`tables.py` loads a JSON table and validates every id against the spec vocabularies at load time (unknown ids and duplicate vendor keys raise `TableError` with every problem listed):

```json
{
  "adapter": "acme",
  "sport":       [{"vendor": "SOCC", "id": "sport:soccer", "name": "Soccer"}],
  "segment":     [{"vendor": "1H",   "id": "segment:soccer:1st-half"}],
  "market_type": [{"vendor": "ML",   "id": "market:moneyline"}],
  "side":        [{"vendor": "1",    "id": "home"}]
}
```

```python
from openbook_translate.tables import MappingTable, Unmapped

tables = MappingTable.load("acme.tables.json")
hit = tables.lookup("sport", "SOCC")     # Mapped(id="sport:soccer", name="Soccer", ...)
miss = tables.lookup("sport", "CURL")    # Unmapped(id="sport:unknown", vendor="CURL", x_field="x_acmeSportId")
```

A miss is not an error: `Unmapped` carries the catch-all id and the `x_` field to stamp the vendor value into (`miss.stamp(document)`), so nothing is lost and the gap can be counted. Kinds are `sport`, `segment`, `market_type`, `side`. Vendor values are matched as strings.

### 2. Vocabulary helpers

`vocab.py` parses the spec's `sports.md`, `segments.md` and `market_types.md` at import. Catch-alls are exactly `sport:unknown`, `segment:unknown:unknown`, `market:unknown`. Numbered families (`inning-<n>`, `set-<n>-game-<m>`) are matched as regexes.

```python
from openbook_translate import vocab

vocab.sport_or_unknown("soccer")                   # "sport:soccer"
vocab.segment_or_unknown("baseball", "inning-11")  # "segment:baseball:inning-11"
vocab.market_or_unknown("bananas")                 # "market:unknown"
vocab.MARKET_TYPES["market:total"].shape           # "over-under"
vocab.is_known_segment("segment:tennis:set-2-game-7")  # True
```

### 3. Count the gaps

```python
from openbook_translate.gaps import GapCounter

class KiblTranslator(Translator):
    name = "kibl"
    def __init__(self):
        self.tables = MappingTable.load(...)
        self.gaps = GapCounter()          # exposed as .gaps so the suite and CLI find it

    def translate(self, raw, *, source_id, parsed=None):
        ...
        sport = self.tables.lookup("sport", record["sportCode"])
        if isinstance(sport, Unmapped):
            self.gaps.record_unmapped(sport, sample=record["id"])
            body = sport.stamp(body)
        body["sport"] = {"id": sport.id, "name": ...}
```

`GapCounter.report(top=50)` sorts by count; `to_dict()` is JSON-safe. Pass a `GapSink` (anything with `record(kind, vendor_value, sample=None)`) to persist counts in your own store.

### 4. Quarantine with a reason from the vocabulary

```python
from openbook_translate.types import PARSE_ERROR, SCHEMA_INVALID, UNMAPPED_SPORT, Quarantine

return Quarantine(raw, PARSE_ERROR, source_id=source_id, adapter=self.name, detail=str(err))
```

`raw` and `reason` are positional as before; `source_id`, `adapter`, `detail`, `received_at` are optional. `Quarantine.to_dict()` base64-encodes `raw` for a log or a queue. Reasons: `unmapped-sport`, `unmapped-league`, `unmapped-market-type`, `unmapped-segment`, `unmapped-participant`, `schema-invalid`, `parse-error`, `other`.

### 5. Build envelopes

```python
from openbook_translate.envelope import change_envelope, merge_patch, heartbeat, snapshot_complete
from openbook_translate.spec import validate_envelope

patch = merge_patch(previous_fixture, fixture)       # minimal RFC 7386 patch, null tombstones
env = change_envelope(publisher="acme-feeds", sequence=seq, object="fixture", action="update",
                      sport="sport:soccer", id=fixture["id"], changes=patch)
assert validate_envelope(env) == []
heartbeat("acme-feeds", seq + 1)
snapshot_complete("acme-feeds", seq + 2, "fixture", "soccer", id=fixture["id"])
```

`validate_envelope` checks the envelope against `change.schema.json`, then `changes` against the object's schema: in full for `snapshot`/`create`, as a Merge Patch (nothing required) for every other action, and never requiring `openbookVersion`/`sequence`/`dateModified` inside `changes`. `validate_document(stem, doc)` validates one document.

### 6. Run the contract suite against your adapter

Subclass `ContractSuite` in your tests. pytest collects it.

```python
from pathlib import Path
from openbook_translate.testing import ContractSuite
from openbook_translate_kibl import KiblTranslator

class TestKibl(ContractSuite):
    translator_cls = KiblTranslator
    source_id = "kibl"
    fixtures = [                                   # (inbound raw bytes or parsed dict, expected native id)
        (Path("tests/data/fixture-1.json").read_bytes(), "EVT-1"),
        ({"id": "EVT-2", ...}, "EVT-2"),
    ]
    quarantine_fixtures = [b"not json", {"unknown": "shape"}]   # MUST quarantine, never raise
    reverse_supported = True                      # False: reverse must return Quarantine
    captures_dir = Path("tests/captures")         # optional golden captures
```

It asserts, per fixture: `translate` returns `Documents`; every document validates against its schema (`document_stem`, or override `schema_stem_for(doc)`); documents carry `identifier[{propertyID: name, value: expected}]`; each quarantine fixture returns `Quarantine` without raising; and `reverse(translate(x))` returns `Vendor` whose re-translation yields the same native id (or, with `reverse_supported = False`, `reverse` returns `Quarantine`). With `captures_dir`, every `*.json` file (one record) and every `*.jsonl` line under it is translated: all documents must validate and nothing may raise; quarantine is allowed but counted. Each class prints a gap report at the end of its run. See `tests/test_contract_acme.py`.

### 7. CLI

Adapters resolve through the `openbook_translate.adapters` entry-point group. In your `pyproject.toml`:

```toml
[project.entry-points."openbook_translate.adapters"]
kibl = "openbook_translate_kibl:KiblTranslator"
```

```bash
openbook-translate run acme feed.jsonl --source-id acme-book --jsonl   # one JSON line per document, one per quarantine ("quarantine": true)
cat record.json | openbook-translate run acme - --source-id acme-book --parsed
openbook-translate validate examples/*.json                             # envelope if it has object+action, else document by file stem
openbook-translate validate doc.json --stem fixture
openbook-translate gaps tests/captures --adapter acme --source-id acme-book
```

Exit codes: `run` 0 if any document, 1 if only quarantine, 2 on usage; `validate` 0 if all valid, 1 otherwise; `gaps` 0, 2 on usage.

## acme record (tests only)

```json
{
  "id": "A-88213",
  "type": "fixture",
  "sport": "SOCC",
  "openbook": { }
}
```

`type` is the vendored schema stem (`fixture`, `participant`, ...). `openbook` is the document body. `id` is the native id. `sport` is optional: a vendor code resolved through `acme.tables.json`; a miss becomes `sport:unknown` plus `x_acmeSportId` and a counted gap.

## Spec stamp

`openbook_translate/openbook-spec-version` is the OpenBook version these schemas were copied from; `openbook-spec-commit` is the spec commit. `openbook-translate update` compares the stamp, the vendored `schema/*.json` and the vendored `vocabularies/*` to the spec. CI goes red when they moved. The command does not write git.

```bash
openbook-translate update                        # GitHub spec main (CI)
openbook-translate update --local                # sibling ../openbook checkout
openbook-translate update --spec-root ../openbook
```

To re-vendor: copy `schema/*.json` and `vocabularies/{sports.md,segments.md,market_types.md,deprecated.json}` from the spec into `src/openbook_translate/`, set the two stamp files, and run `update --local` until it passes.

## Release

Releases are git tags `vX.Y.Z` on `main`. Each release names the spec version its schemas came from (this README, `SPEC_VERSION`, and `openbook-spec-version` all say the same thing). Install from a tag as shown in [Install](#install). There are no PyPI uploads.

| Release | Spec version | Notes |
| --- | --- | --- |
| `v0.1.0` | `0.3.0-draft` | First release: contract, acme, vocab, tables, gaps, envelope, contract suite, CLI. |
