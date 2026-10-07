"""Unit tests for cardscan.masker.

All card numbers used here are publicly documented network test numbers.
"""

import unittest

from cardscan.masker import mask_card_number, redact_text


class TestMaskCardNumber(unittest.TestCase):
    def test_keeps_last_four_digits(self):
        self.assertEqual(mask_card_number("4111111111111111"), "XXXXXXXXXXXX1111")

    def test_preserves_dashes(self):
        self.assertEqual(mask_card_number("4111-1111-1111-1111"), "XXXX-XXXX-XXXX-1111")

    def test_preserves_amex_spacing(self):
        self.assertEqual(mask_card_number("3782 822463 10005"), "XXXX XXXXXX X0005")


class TestRedactText(unittest.TestCase):
    def test_redacts_cards_and_leaves_surrounding_text(self):
        text = "visa 4111-1111-1111-1111 and amex 378282246310005."
        self.assertEqual(
            redact_text(text),
            "visa XXXX-XXXX-XXXX-1111 and amex XXXXXXXXXXX0005.",
        )

    def test_redacts_number_glued_to_words(self):
        self.assertEqual(redact_text("cardis4111111111111111now"), "cardisXXXXXXXXXXXX1111now")

    def test_redacts_every_occurrence(self):
        self.assertEqual(
            redact_text("4111111111111111 / 4111111111111111"),
            "XXXXXXXXXXXX1111 / XXXXXXXXXXXX1111",
        )

    def test_leaves_luhn_invalid_numbers_untouched(self):
        text = "Order serial is 9876543210123456 (fake)."
        self.assertEqual(redact_text(text), text)

    def test_text_without_cards_is_unchanged(self):
        self.assertEqual(redact_text("hello world"), "hello world")


if __name__ == "__main__":
    unittest.main()
