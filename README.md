# openbook-translate

Apache-2.0 library for mapping **one inbound vendor record** onto OpenBook
documents, and back. OpenBook is the target language; this package is not the
specification (Q96).

Vendored JSON Schema files stay **CC BY 4.0** (see `NOTICE`).

## Contract

`Translator` is an ABC. One record in. Two sync methods:

- `translate(raw, *, source_id, parsed=None)` — vendor bytes, optional already-parsed dict, and the OpenBook source id → OpenBook documents, or **quarantine** (`raw` + `reason`). Unmapped records quarantine. They do not raise and they are not skipped.
- `reverse(document)` — one OpenBook document → vendor bytes and an optional dict.

A successful map **MUST** put the native id on `identifier` (`propertyID` is the adapter name, `value` is the native id) so `reverse` can round-trip.

The official implementer is the synthetic **acme** adapter (contract tests only). Community adapters MAY be published as `openbook-translate-kibl` and similar. This project will not ship vendor adapters.

## Install

```bash
pip install -e '.[dev]'
pytest
```

Python 3.11+.

## acme record (tests only)

```json
{
  "id": "A-88213",
  "type": "fixture",
  "openbook": { }
}
```

`type` is the vendored schema stem (`fixture`, `participant`, …). `openbook` is the document body. `id` is the native id.

## Spec stamp

`openbook-spec-version` is the OpenBook version these schemas were copied from. `openbook-translate update` compares that stamp and the vendored `schema/*.json` to the spec. CI goes red when they moved. The command does not write git.

```bash
openbook-translate update          # GitHub spec main (CI)
openbook-translate update --local  # sibling spec checkout
```
