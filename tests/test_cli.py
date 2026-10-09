"""Tests for cardscan.cli.

All card numbers used here are publicly documented network test numbers.
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from cardscan.cli import run

TEXT = "visa 4111-1111-1111-1111\nnothing here\namex 378282246310005\n"


def _run(argv, stdin=""):
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(stdin)):
        code = run(argv, stdout=out)
    return code, out.getvalue()


class TestRedactMode(unittest.TestCase):
    def test_redacts_stdin(self):
        code, out = _run([], TEXT)
        self.assertEqual(code, 0)
        self.assertEqual(out, "visa XXXX-XXXX-XXXX-1111\nnothing here\namex XXXXXXXXXXX0005\n")

    def test_dash_reads_stdin(self):
        self.assertEqual(_run(["-"], TEXT), _run([], TEXT))

    def test_reads_multiple_files(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.txt"), os.path.join(d, "b.txt")
            with open(a, "w") as f:
                f.write("4111111111111111\n")
            with open(b, "w") as f:
                f.write("no cards\n")
            code, out = _run([a, b])
        self.assertEqual(code, 0)
        self.assertEqual(out, "XXXXXXXXXXXX1111\nno cards\n")

    def test_keeps_text_without_trailing_newline(self):
        self.assertEqual(_run([], "card 4111111111111111")[1], "card XXXXXXXXXXXX1111")

    def test_known_brands_only(self):
        _, out = _run(["--known-brands-only"], "serial 9000000000000001\n")
        self.assertEqual(out, "serial 9000000000000001\n")


class TestReportMode(unittest.TestCase):
    def test_lists_location_brand_and_style(self):
        code, out = _run(["--report"], TEXT)
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "<stdin>:1: Visa (Standard Dashes (e.g., XXXX-XXXX-XXXX-XXXX))",
            "<stdin>:3: American Express (Raw Continuous Block (No separators))",
        ])

    def test_never_prints_card_digits(self):
        _, out = _run(["--report"], TEXT)
        self.assertNotIn("4111", out)
        self.assertNotIn("378282246310005", out)

    def test_exit_zero_when_clean(self):
        self.assertEqual(_run(["--report"], "nothing\n"), (0, ""))


class TestCheckMode(unittest.TestCase):
    def test_exit_one_and_no_output_when_found(self):
        self.assertEqual(_run(["--check"], TEXT), (1, ""))

    def test_exit_zero_when_clean(self):
        self.assertEqual(_run(["--check"], "nothing\n"), (0, ""))


class TestErrors(unittest.TestCase):
    def test_missing_file_exits_two(self):
        with mock.patch("sys.stderr", io.StringIO()) as err:
            code, _ = _run(["does-not-exist.txt"])
        self.assertEqual(code, 2)
        self.assertIn("does-not-exist.txt", err.getvalue())

    def test_report_and_check_are_exclusive(self):
        with mock.patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
            _run(["--report", "--check"])


class TestModuleEntryPoint(unittest.TestCase):
    def test_python_m_cardscan(self):
        result = subprocess.run(
            [sys.executable, "-m", "cardscan"],
            input="4111111111111111\n", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "XXXXXXXXXXXX1111\n")


if __name__ == "__main__":
    unittest.main()
