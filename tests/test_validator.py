"""Unit tests for cardscan.validator.

All card numbers used here are publicly documented network test numbers.
"""

import unittest

from cardscan.validator import (
    analyze_context,
    detect_card_brand,
    is_luhn_valid,
    scan_text_advanced,
)

VISA = "4111111111111111"
MASTERCARD = "5555555555554444"
MASTERCARD_2_SERIES = "2221000000000009"
AMEX = "378282246310005"
DISCOVER = "6011111111111117"


class TestLuhn(unittest.TestCase):
    def test_valid_numbers(self):
        for number in (VISA, MASTERCARD, MASTERCARD_2_SERIES, AMEX, DISCOVER):
            with self.subTest(number=number):
                self.assertTrue(is_luhn_valid(number))

    def test_invalid_check_digit(self):
        self.assertFalse(is_luhn_valid("4111111111111112"))

    def test_ignores_separators(self):
        self.assertTrue(is_luhn_valid("4111-1111 1111-1111"))


class TestDetectCardBrand(unittest.TestCase):
    def test_known_brands(self):
        cases = {
            VISA: "Visa",
            MASTERCARD: "Mastercard",
            MASTERCARD_2_SERIES: "Mastercard",
            AMEX: "American Express",
            DISCOVER: "Discover",
            "6500000000000002": "Discover",
        }
        for number, brand in cases.items():
            with self.subTest(number=number):
                self.assertEqual(detect_card_brand(number), brand)

    def test_mastercard_ranges(self):
        cases = {
            "5100000000000008": "Mastercard",
            "2720999999999996": "Mastercard",
            "5600000000000003": "Unknown Card Network",
            "2220999999999991": "Unknown Card Network",
            "2721000000000004": "Unknown Card Network",
        }
        for number, brand in cases.items():
            with self.subTest(number=number):
                self.assertEqual(detect_card_brand(number), brand)

    def test_amex_prefix_requires_15_digits(self):
        self.assertEqual(detect_card_brand("3782822463100050"), "Unknown Card Network")

    def test_unknown_prefix(self):
        self.assertEqual(detect_card_brand("9876543210123456"), "Unknown Card Network")

    def test_additional_brands(self):
        cases = {
            "6440000000000005": "Discover",
            "6221260000000000": "Discover",
            "6229250000000003": "Discover",
            "6221250000000001": "UnionPay",
            "6200000000000005": "UnionPay",
            "3528000000000007": "JCB",
            "3589000000000003": "JCB",
            "30000000000004": "Diners Club",
            "36000000000008": "Diners Club",
            "38000000000006": "Diners Club",
        }
        for number, brand in cases.items():
            with self.subTest(number=number):
                self.assertEqual(detect_card_brand(number), brand)


class TestAnalyzeContext(unittest.TestCase):
    def test_styles(self):
        cases = {
            "4111111111111111": "Raw Continuous Block (No separators)",
            "4111-1111-1111-1111": "Standard Dashes (e.g., XXXX-XXXX-XXXX-XXXX)",
            "4111 1111 1111 1111": "Standard Spaces",
            "3782 822463 10005": "Amex Style Spaces",
            "4111 1111-1111 1111": "Mixed Format (Dashes and Spaces)",
        }
        for original, style in cases.items():
            with self.subTest(original=original):
                self.assertEqual(analyze_context(original), style)


class TestScanTextAdvanced(unittest.TestCase):
    def test_empty_and_clean_text(self):
        self.assertEqual(scan_text_advanced(""), [])
        self.assertEqual(scan_text_advanced("no card numbers here, just 12345"), [])

    def test_result_shape(self):
        [card] = scan_text_advanced(f"pay with {VISA} please")
        self.assertEqual(
            card,
            {
                "original": VISA,
                "cleaned": VISA,
                "brand": "Visa",
                "style": "Raw Continuous Block (No separators)",
            },
        )

    def test_rejects_luhn_invalid_numbers(self):
        self.assertEqual(scan_text_advanced("Order serial is 9876543210123456"), [])

    def test_finds_number_glued_to_words(self):
        [card] = scan_text_advanced(f"cardis{VISA}now")
        self.assertEqual(card["cleaned"], VISA)

    def test_finds_formatted_numbers(self):
        text = "visa 4111-1111-1111-1111 and amex 3782 822463 10005 today"
        cards = scan_text_advanced(text)
        self.assertEqual([c["cleaned"] for c in cards], [VISA, AMEX])
        self.assertEqual([c["original"] for c in cards], ["4111-1111-1111-1111", "3782 822463 10005"])

    def test_deduplicates_repeated_numbers(self):
        cards = scan_text_advanced(f"{VISA} again {VISA}")
        self.assertEqual(len(cards), 1)

    def test_reports_13_to_19_digit_numbers(self):
        for number in ("4222222222222", "4111111111111111110"):
            with self.subTest(number=number):
                [card] = scan_text_advanced(f"card {number} here")
                self.assertEqual(card["cleaned"], number)

    def test_rejects_numbers_outside_13_to_19_digits(self):
        # Both pass Luhn but are too short or too long to be card numbers.
        self.assertEqual(scan_text_advanced("411111111117"), [])
        self.assertEqual(scan_text_advanced("41111111111111111107"), [])

    def test_finds_formatted_19_digit_number(self):
        [card] = scan_text_advanced("card 4111 1111 1111 1111 110 here")
        self.assertEqual(card["original"], "4111 1111 1111 1111 110")

    def test_splits_adjacent_numbers(self):
        cases = {
            f"{VISA} {MASTERCARD}": [VISA, MASTERCARD],
            "4111 1111 1111 1111 5555 5555 5555 4444": [VISA, MASTERCARD],
            f"ref 1234 {VISA}": [VISA],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual([c["cleaned"] for c in scan_text_advanced(text)], expected)


if __name__ == "__main__":
    unittest.main()
