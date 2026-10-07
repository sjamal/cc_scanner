# Credit Card Detection and Masking Scanner

A lightweight, dependency-free Python library for scanning unstructured text (chat logs, form submissions, support tickets) to find credit card numbers someone pasted by accident and mask them.

```text
In:  But user typed cardis4111111111111111now and amex 3782-822463-10005 together.
Out: But user typed cardisXXXXXXXXXXXX1111now and amex XXXX-XXXXXX-X0005 together.
```

## Features

- Finds card numbers even when they're attached to surrounding words (`cardis4111…now`).
- Handles raw digits as well as space- and dash-separated formats.
- Checks every candidate with the [Luhn algorithm](https://en.wikipedia.org/wiki/Luhn_algorithm), so ordinary serial and order numbers aren't masked.
- Identifies the card network (Visa, Mastercard, American Express, Discover).
- Masks every digit except the last four and keeps the original spaces and dashes.

## Project layout

```text
cc_scanner/
├── cardscan/
│   ├── __init__.py    # Public API re-exports
│   ├── validator.py   # Detection: regex scan, Luhn check, brand + format detection
│   └── masker.py      # Redaction: masks digits while preserving separators
├── tests/
│   ├── test_validator.py
│   └── test_masker.py
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

To use it from another project, install it in editable mode:

```bash
pip install -e .
```

## Usage

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
| `scan_text_advanced(text)` | `list[dict]` | Finds Luhn-valid 13–19 digit card numbers in `text`. Each result has `original` (the text as it appeared), `cleaned` (digits only), `brand` and `style`. Repeated numbers are reported once. |
| `is_luhn_valid(card_number)` | `bool` | Runs the Luhn checksum. Non-digit characters are ignored. |
| `detect_card_brand(number)` | `str` | Identifies the network from the prefix: `"Visa"`, `"Mastercard"`, `"American Express"`, `"Discover"` or `"Unknown Card Network"`. |
| `analyze_context(original_match)` | `str` | Describes how the number was formatted (raw, dashes, spaces, Amex-style spaces or mixed). |

> [!NOTE]
> The scanner checks 13–19 digit numbers, the full range of card lengths networks issue. Earlier versions only checked 15–16 digits. The wider range catches more real cards, such as 14-digit Diners Club and 19-digit Visa numbers. It also means more non-card numbers (account, tracking or reference numbers) that happen to pass the Luhn check may be flagged and masked.

### `cardscan.masker`

| Function | Returns | Description |
|---|---|---|
| `redact_text(text)` | `str` | Returns `text` with every detected card number masked. |
| `mask_card_number(original_match)` | `str` | Replaces every digit except the last four with `X`. Separators are left in place. |

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

All card numbers in the tests and demo are published network test numbers, not real cards.

## Known limitations


- Mastercard's 2-series check accepts `22`–`27`, while the real range is `2221`–`2720`.

- Discover's `644`–`649` and `622126`–`622925` ranges aren't recognised. JCB, Diners Club and UnionPay come back as `Unknown Card Network`.

- Detection relies on a regex plus the Luhn check, so a long number that happens to pass Luhn (about 1 in 10 random numbers) will be masked even if it isn't a card.

## License

Released under the [MIT License](LICENSE).
