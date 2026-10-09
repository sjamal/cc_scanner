"""Command-line interface: scan files or standard input line by line."""

import argparse
import os
import sys

from .masker import redact_text
from .validator import scan_text_advanced


def _open_inputs(paths):
    """Yields (name, file) pairs. No paths or "-" means standard input."""
    for path in paths or ["-"]:
        if path == "-":
            yield "<stdin>", sys.stdin
        else:
            with open(path, encoding="utf-8", errors="replace", newline="") as f:
                yield path, f


def _silence_stdout():
    """Called when output is closed early (e.g. piped to head). Stops Python's flush error on exit."""
    os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())


def run(argv=None, stdout=None):
    """Runs the CLI and returns the exit code."""
    stdout = stdout or sys.stdout
    parser = argparse.ArgumentParser(
        prog="cardscan",
        description="Mask credit card numbers in text. Reads files or standard input.",
        epilog="Exit codes: 0 no cards found (or redact mode), 1 cards found, 2 error.",
    )
    parser.add_argument("files", nargs="*", help='files to scan ("-" for standard input)')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--report", action="store_true",
                      help="list where cards were found instead of printing redacted text")
    mode.add_argument("--check", action="store_true",
                      help="print nothing; exit 1 if any card is found")
    parser.add_argument("--known-brands-only", action="store_true",
                        help="ignore numbers that don't match a known card network")
    args = parser.parse_args(argv)

    found = False
    try:
        for name, f in _open_inputs(args.files):
            for line_no, line in enumerate(f, 1):
                if not (args.report or args.check):
                    stdout.write(redact_text(line, known_brands_only=args.known_brands_only))
                    continue
                cards = scan_text_advanced(line, known_brands_only=args.known_brands_only)
                if cards and args.check:
                    return 1
                for card in cards:
                    found = True
                    stdout.write(f"{name}:{line_no}: {card['brand']} ({card['style']})\n")
    except BrokenPipeError:
        _silence_stdout()
        return 1 if args.report else 0
    except OSError as e:
        print(f"cardscan: {e.filename}: {e.strerror}", file=sys.stderr)
        return 2

    return 1 if found else 0


def main():
    code = run()
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        _silence_stdout()
    sys.exit(code)
