"""``openbook-translate`` command line.

    run <adapter> <file|-> --source-id ID [--jsonl] [--parsed]   translate records
    validate <file...> [--stem S]                                 envelopes or documents
    gaps --adapter <name> --source-id ID <dir>                    gap report over captures
    update [--local] [--spec-root DIR]                            schema drift check

Adapters resolve through the ``openbook_translate.adapters`` entry-point group.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path

from openbook_translate.abc import Translator
from openbook_translate.adapters import load
from openbook_translate.captures import iter_captures
from openbook_translate.gaps import counter_of
from openbook_translate.spec import is_envelope, validate_document, validate_envelope
from openbook_translate.types import Documents, Quarantine
from openbook_translate.update import check, find_spec_root

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


def _load_adapter(parser: argparse.ArgumentParser, name: str) -> Translator:
    try:
        return load(name)
    except KeyError:
        parser.exit(EXIT_USAGE, f"{parser.prog}: no adapter {name!r} in entry-point group openbook_translate.adapters\n")
    except Exception as e:  # noqa: BLE001 - a broken plugin is a usage problem for the operator
        parser.exit(EXIT_USAGE, f"{parser.prog}: adapter {name!r} failed to load: {e}\n")


def _records(source: str, jsonl: bool) -> Iterator[bytes]:
    data = sys.stdin.buffer.read() if source == "-" else Path(source).read_bytes()
    if not jsonl:
        yield data
        return
    for line in data.splitlines():
        if line.strip():
            yield line


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def cmd_run(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    translator = _load_adapter(parser, args.adapter)
    documents = quarantines = 0
    for raw in _records(args.file, args.jsonl):
        parsed = None
        if args.parsed:
            try:
                obj = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                obj = None
            parsed = obj if isinstance(obj, dict) else None
        result = translator.translate(raw, source_id=args.source_id, parsed=parsed)
        if isinstance(result, Quarantine):
            quarantines += 1
            _emit({"quarantine": True, **result.to_dict()})
            continue
        assert isinstance(result, Documents)
        for doc in result.documents:
            documents += 1
            _emit(doc)
    sys.stdout.flush()
    if documents:
        return EXIT_OK
    if quarantines:
        return EXIT_FAIL
    print(f"{parser.prog} run: no records read", file=sys.stderr)
    return EXIT_USAGE


def _validate_file(path: Path, stem: str | None) -> list[str]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"cannot read JSON: {e}"]
    if is_envelope(obj):
        return validate_envelope(obj)
    if not isinstance(obj, dict):
        return ["not a JSON object"]
    return validate_document(stem or path.name.split(".")[0], obj)


def cmd_validate(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    failed = 0
    for name in args.files:
        path = Path(name)
        errors = _validate_file(path, args.stem)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for e in errors:
                print(f"  {e}")
        else:
            print(f"OK   {path}")
    return EXIT_FAIL if failed else EXIT_OK


def cmd_gaps(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    translator = _load_adapter(parser, args.adapter)
    directory = Path(args.dir)
    if not directory.exists():
        parser.exit(EXIT_USAGE, f"{parser.prog} gaps: {directory} does not exist\n")
    total = mapped = 0
    by_reason: dict[str, int] = {}
    unmapped: dict[str, list[str]] = {}
    for cap in iter_captures(directory):
        total += 1
        result = translator.translate(cap.raw, source_id=args.source_id)
        if isinstance(result, Quarantine):
            by_reason[result.reason] = by_reason.get(result.reason, 0) + 1
            unmapped.setdefault(result.reason, []).append(cap.label)
        else:
            mapped += 1
    print(f"{translator.name}: {total} record(s), {mapped} mapped, {total - mapped} quarantined")
    gaps = counter_of(translator)
    print("mapping gaps: " + (gaps.format(top=args.top) if gaps is not None else "adapter exposes no GapCounter as .gaps"))
    if by_reason:
        print("quarantines by reason:")
        for reason, n in sorted(by_reason.items(), key=lambda kv: (-kv[1], kv[0])):
            first = unmapped[reason][0]
            print(f"{n:>6}  {reason}  first={first}")
    if total == 0:
        print(f"{parser.prog} gaps: no *.json / *.jsonl captures under {directory}", file=sys.stderr)
        return EXIT_USAGE
    return EXIT_OK


def cmd_update(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    spec_root = args.spec_root
    if spec_root is not None or args.local:
        spec_root = spec_root or find_spec_root()
        if spec_root is None:
            print(f"{parser.prog} update: no spec checkout found", file=sys.stderr)
            return EXIT_USAGE
        problems = check(spec_root=spec_root)
    else:
        problems = check(fetch=True)

    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        print("spec moved (notify only; no git writes)", file=sys.stderr)
        return EXIT_FAIL
    where = spec_root if spec_root is not None else "GitHub main"
    print(f"{parser.prog} update: in sync with {where}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openbook-translate", description="Tools for OpenBook adapters: translate, validate, gap report, spec drift check.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="translate vendor records with an adapter; one JSON line per document or quarantine")
    run.add_argument("adapter", help="adapter name in the openbook_translate.adapters entry-point group")
    run.add_argument("file", help="vendor file, or - for stdin")
    run.add_argument("--source-id", required=True, help="OpenBook source id for this feed")
    run.add_argument("--jsonl", action="store_true", help="one record per line instead of one record per file")
    run.add_argument("--parsed", action="store_true", help="also parse each record as JSON and pass it as parsed=")
    run.set_defaults(func=cmd_run)

    val = sub.add_parser("validate", help="validate envelopes (object+action) or documents against the vendored schemas")
    val.add_argument("files", nargs="+", help="JSON files")
    val.add_argument("--stem", help="schema stem for documents (default: the file name before the first dot)")
    val.set_defaults(func=cmd_validate)

    gaps = sub.add_parser("gaps", help="run an adapter over a captures directory and print the gap report")
    gaps.add_argument("dir", help="directory of *.json / *.jsonl captures")
    gaps.add_argument("--adapter", required=True, help="adapter name")
    gaps.add_argument("--source-id", required=True, help="OpenBook source id for this feed")
    gaps.add_argument("--top", type=int, default=50, help="how many gaps to list (default 50)")
    gaps.set_defaults(func=cmd_gaps)

    upd = sub.add_parser("update", help="fail if vendored schemas, vocabularies or stamp drifted from the spec")
    upd.add_argument("--local", action="store_true", help="compare to a spec checkout, not GitHub")
    upd.add_argument("--spec-root", type=Path, help="spec repository root (implies --local)")
    upd.set_defaults(func=cmd_update)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(parser, args)


if __name__ == "__main__":
    raise SystemExit(main())
