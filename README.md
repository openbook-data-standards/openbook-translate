# openbook-translate

Python kernel: unknown vendor record → OpenBook documents, and reverse.

Not the OpenBook specification. Spec: https://github.com/openbook-data-standards/openbook

Apache-2.0. Vendored schemas are CC BY 4.0 (see NOTICE).

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

While this repo is private: `pip install git+ssh://git@github.com/openbook-data-standards/openbook-translate.git`

Subclass `Adapter`, implement `translate` and `reverse`. Official implementer: synthetic `acme`. Community vendor packages are welcome; this project will not ship 487/KIBL/LinePros adapters.
