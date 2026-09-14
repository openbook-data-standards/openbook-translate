from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openbook_translate.update import check, find_spec_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openbook-translate")
    sub = parser.add_subparsers(dest="cmd", required=True)
    upd = sub.add_parser("update", help="fail if vendored schemas or stamp drifted from the spec")
    upd.add_argument("--local", action="store_true", help="compare to a spec checkout, not GitHub")
    upd.add_argument("--spec-root", type=Path, help="spec repository root (implies --local)")
    args = parser.parse_args(argv)

    if args.cmd != "update":
        parser.error(f"unknown command {args.cmd}")

    spec_root = args.spec_root
    if spec_root is not None or args.local:
        spec_root = spec_root or find_spec_root()
        if spec_root is None:
            print("openbook-translate update: no spec checkout found", file=sys.stderr)
            return 2
        problems = check(spec_root=spec_root)
    else:
        problems = check(fetch=True)

    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        print("spec moved (notify only; no git writes)", file=sys.stderr)
        return 1
    where = spec_root if spec_root is not None else "GitHub main"
    print(f"openbook-translate update: in sync with {where}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
