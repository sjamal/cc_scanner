# Credit Card Detection and Masking Scanner

A lightweight, dependency-free Python library and command-line tool for scanning unstructured text (chat logs, form submissions, support tickets) to find credit card numbers someone pasted by accident and mask them.

Useful for keeping stray payment or credit card numbers out of logs, tickets and exports, which reduces what falls into PCI DSS scope. Masking keeps only the last four digits, in line with the PCI DSS display rule. This tool supports compliance work; it doesn't make a system compliant on its own.

```text
In:  But user typed cardis4111111111111111now and amex 3782-822463-10005 together.
Out: But user typed cardisXXXXXXXXXXXX1111now and amex XXXX-XXXXXX-X0005 together.
```

## Features

- Finds card numbers even when they're attached to surrounding words (`cardis4111…now`).
- Handles raw digits as well as space- and dash-separated formats.
- Checks every candidate with the [Luhn algorithm](https://en.wikipedia.org/wiki/Luhn_algorithm), so most ordinary serial and order numbers aren't masked.
- Identifies the card network (Visa, Mastercard, American Express, Discover, JCB, Diners Club, UnionPay).
- Masks every digit except the last four and keeps the original spaces and dashes.
- Command-line tool that reads files or piped input line by line, so file size doesn't affect memory use.

## Project layout

```text
cc_scanner/
├── cardscan/
│   ├── __init__.py    # Public API re-exports
│   ├── validator.py   # Detection: candidate scan, Luhn check, brand + format detection
│   ├── masker.py      # Redaction: masks digits while preserving separators
│   ├── cli.py         # Command-line tool
│   └── __main__.py    # Enables `python -m cardscan`
├── examples/
│   ├── sample_chat.txt  # Sample input with test card numbers
│   └── pre-commit       # Git hook that blocks commits containing card numbers
├── tests/
│   ├── test_validator.py
│   ├── test_masker.py
│   └── test_cli.py
├── main.py            # Runnable demo
├── pyproject.toml
└── LICENSE
```

## Requirements

Python 3.9+. The library itself uses only the standard library.

## Quick start

```bash
git clone https://github.com/sjamal/cc_scanner.git
cd cc_scanner
python3 main.py
```

To use it from another project or as a command, install it in editable mode:

```bash
pip install -e .
```

## Command-line usage

`pip install -e .` adds a `cardscan` command. Without installing, use `python3 -m cardscan` from the project folder.

```bash
cardscan chat.log > chat_clean.log          # Redact a file
cat chat.log | cardscan > chat_clean.log    # Redact piped input
cardscan a.txt b.csv > combined_clean.txt   # Redact several files, output joined
cardscan --report export.csv                # List where cards were found
cardscan --check upload.txt                 # No output, exit code only
```

| Option | Effect |
|---|---|
| *(none)* | Prints the input with card numbers masked. |
| `--report` | Prints `file:line: brand (style)` for each card found. Card digits are never printed. |
| `--check` | Prints nothing. Stops at the first card found. |
| `--known-brands-only` | Ignores numbers that don't match a known network. See [Reducing false positives](#reducing-false-positives). |

A file name of `-`, or no file name, reads standard input.

Exit codes:

| Code | Meaning |
|---|---|
| `0` | No cards found. Redact mode always returns `0` on success. |
| `1` | `--report` or `--check` found at least one card. |
| `2` | A file couldn't be read, or the options were invalid. |

Try it on the sample file:

```bash
cardscan --report examples/sample_chat.txt
# examples/sample_chat.txt:2: Visa (Standard Spaces)
# examples/sample_chat.txt:4: American Express (Standard Dashes (e.g., XXXX-XXXX-XXXX-XXXX))
# examples/sample_chat.txt:5: Mastercard (Raw Continuous Block (No separators))
```

### Using it with other tools

Any tool that can run a command or pipe text can use `cardscan`.

- **Log files:** `tail -f app.log | cardscan >> app_clean.log`
- **Spreadsheets:** export to CSV, run `cardscan sheet.csv > sheet_clean.csv`, re-import. Only cell text changes, so the CSV structure stays intact.
- **Word or PDF documents:** convert to text first (for example `textutil -convert txt doc.docx` on macOS, or `pdftotext file.pdf`), then pipe to `cardscan`.
- **Git:** [examples/pre-commit](examples/pre-commit) blocks commits whose added lines contain a card number. Install it in a repository with:

  ```bash
  cp examples/pre-commit .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
  ```

  The hook needs `cardscan` on the `PATH`.
- **Scripts and CI:** use `--check` and test the exit code.

  ```bash
  if ! cardscan --check upload.txt; then
      echo "Card number found" >&2
  fi
  ```

### Large inputs

Input is processed one line at a time and output is written as it goes, so memory use stays flat. A 21 MB, 500,000-line file takes about 2 seconds and under 25 MB of memory on a recent laptop.

## Library usage

```python
from cardscan import scan_text_advanced, redact_text

text = "Card on file: 4111-1111-1111-1111"

for card in scan_text_advanced(text):
    print(card["brand"], card["style"])
# Visa Standard Dashes (e.g., XXXX-XXXX-XXXX-XXXX)

print(redact_text(text))
# Card on file: XXXX-XXXX-XXXX-1111
```

## API reference

### `cardscan.validator`

| Function | Returns | Description |
|---|---|---|
| `scan_text_advanced(text, known_brands_only=False)` | `list[dict]` | Finds Luhn-valid 13–19 digit card numbers in `text`. Each result has `original` (the text as it appeared), `cleaned` (digits only), `brand` and `style`. Repeated numbers are reported once. |
| `is_luhn_valid(card_number)` | `bool` | Runs the Luhn checksum. Non-digit characters are ignored. |
| `detect_card_brand(number)` | `str` | Identifies the network from the prefix: `"Visa"`, `"Mastercard"`, `"American Express"`, `"Discover"`, `"JCB"`, `"Diners Club"`, `"UnionPay"` or `"Unknown Card Network"`. |
| `analyze_context(original_match)` | `str` | Describes how the number was formatted (raw, dashes, spaces, Amex-style spaces or mixed). |

> [!NOTE]
> The scanner checks 13–19 digit numbers, the full range of card lengths networks issue. Earlier versions only checked 15–16 digits. The wider range catches more real cards, such as 14-digit Diners Club and 19-digit Visa numbers. It also means more non-card numbers (account, tracking or reference numbers) that happen to pass the Luhn check may be flagged and masked.

### `cardscan.masker`

| Function | Returns | Description |
|---|---|---|
| `redact_text(text, known_brands_only=False)` | `str` | Returns `text` with every detected card number masked. |
| `mask_card_number(original_match)` | `str` | Replaces every digit except the last four with `X`. Separators are left in place. |

### Reducing false positives

`scan_text_advanced` and `redact_text` both accept `known_brands_only=True`. With it set, numbers whose prefix doesn't match a known card network are ignored. This cuts down on order numbers and serials that happen to pass the Luhn check, but cards from networks the scanner doesn't recognise will be left unmasked.

```python
redact_text("visa 4111111111111111 serial 9000000000000001", known_brands_only=True)
# 'visa XXXXXXXXXXXX1111 serial 9000000000000001'
```

## Running the tests

The tests use the standard library's `unittest`, so you don't need to install anything:

```bash
python3 -m unittest discover -s tests -t . -v
```

They also run under pytest:

```bash
pip install -e ".[test]"
pytest
```

All card numbers in the tests and demo are published network test numbers or made-up values that only pass the Luhn check. None are real cards.

## Known limitations

- The command-line tool scans one line at a time, so a card number split across two lines isn't detected.
- Detection relies on digit patterns plus the Luhn check, so by default a long number that happens to pass Luhn (about 1 in 10 random numbers) will be masked even if it isn't a card. Use `known_brands_only=True` to narrow this (see [Reducing false positives](#reducing-false-positives)).

## License

Released under the [MIT License](LICENSE).
