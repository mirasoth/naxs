"""Command-line interface for pynaxs.

Provides the ``pynaxs`` console script and the ``python -m pynaxs``
entry point, with a ``validate`` subcommand that validates NAXS v0.1
JSON documents from a file or a directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .validator import NaxsValidator


def _validate_path(path: str, validator: NaxsValidator, strict: bool = False) -> dict:
    """Validate a single JSON file and summarize the outcome.

    Args:
        path: Path of the file to validate.
        validator: Validator instance to run against the file.
        strict: When True, omit warnings from the returned summary
            (warnings never affect validity).

    Returns:
        A dict with keys ``path``, ``valid``, ``errors``,
        ``warnings``, ``error_count``, and ``warning_count``, where
        ``errors`` and ``warnings`` are lists of
        ``{path, message, rule}`` dicts.
    """
    result = validator.validate_file(path)
    return {
        "path": path,
        "valid": result.is_valid(),
        "errors": [
            {"path": e.path, "message": e.message, "rule": e.rule}
            for e in result.errors
        ],
        "warnings": [] if strict else [
            {"path": w.path, "message": w.message, "rule": w.rule}
            for w in result.warnings
        ],
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
    }


def _collect_json_files(path: str) -> list[str]:
    """Collect the JSON files to validate from a path.

    Args:
        path: A file path (returned as a single-element list) or a
            directory path (searched recursively for ``*.json``
            files, sorted for deterministic order).

    Returns:
        The list of file paths; empty when the path is neither an
        existing file nor a directory.
    """
    p = Path(path)
    if p.is_file():
        return [str(p)]
    if p.is_dir():
        return sorted(str(f) for f in p.rglob("*.json"))
    return []


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code: 0 when every validated document is valid,
        1 when no JSON files were found or at least one document is
        invalid.
    """
    parser = argparse.ArgumentParser(
        prog="pynaxs",
        description="Validate NAXS v0.1 architecture/block JSON documents.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="Validate NAXS JSON files")
    val.add_argument("path", help="Path to a JSON file or directory of JSON files")
    val.add_argument("--strict", action="store_true", help="Suppress warnings, only show errors")
    val.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    val.add_argument("--quiet", action="store_true", help="Only output on errors")

    args = parser.parse_args(argv)

    if args.command == "validate":
        files = _collect_json_files(args.path)
        if not files:
            print(f"No JSON files found at '{args.path}'", file=sys.stderr)
            return 1

        validator = NaxsValidator()
        results = []
        all_valid = True

        for f in files:
            r = _validate_path(f, validator, strict=args.strict)
            results.append(r)
            if not r["valid"]:
                all_valid = False

        if args.format == "json":
            output = {
                "total": len(results),
                "valid": sum(1 for r in results if r["valid"]),
                "invalid": sum(1 for r in results if not r["valid"]),
                "results": results,
            }
            print(json.dumps(output, indent=2))
        else:
            for r in results:
                if args.quiet and r["valid"]:
                    continue
                status = "✅" if r["valid"] else "❌"
                print(f"{status} {r['path']}")
                for e in r["errors"]:
                    print(f"  ERROR [{e['rule']}] {e['path']}: {e['message']}")
                for w in r["warnings"]:
                    print(f"  WARN  [{w['rule']}] {w['path']}: {w['message']}")

            valid_count = sum(1 for r in results if r["valid"])
            invalid_count = len(results) - valid_count
            print(f"\n{valid_count} valid, {invalid_count} invalid (out of {len(results)} total)")

        return 0 if all_valid else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
