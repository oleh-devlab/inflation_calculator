"""
Tests for the import_local_data script.

Run:
    python -m pytest tests/test_import_local_data.py -v
    or
    python -m unittest tests.test_import_local_data -v
"""

import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.import_local_data import parse_raw_data


class TestParseRawData(unittest.TestCase):
    """Tests for the parse_raw_data function."""

    # Typical Ministry of Finance data (2 years), identical to the table format
    SAMPLE_TWO_YEARS = (
        "2000\t104,6\t103,3\t102,0\t101,7\t102,1\t103,7"
        "\t99,9\t100,0\t102,6\t101,4\t100,4\t101,6\t125,8\n"
        "2001\t101,5\t100,6\t100,6\t101,5\t100,4\t100,6"
        "\t98,3\t99,8\t100,4\t100,2\t100,5\t101,6\t106,1"
    )

    # Expected multipliers — match inflation_rates.json
    EXPECTED_2000 = {
        "2000-01": "1.046", "2000-02": "1.033", "2000-03": "1.02",
        "2000-04": "1.017", "2000-05": "1.021", "2000-06": "1.037",
        "2000-07": "0.999", "2000-08": "1.0",   "2000-09": "1.026",
        "2000-10": "1.014", "2000-11": "1.004", "2000-12": "1.016",
    }

    EXPECTED_2001 = {
        "2001-01": "1.015", "2001-02": "1.006", "2001-03": "1.006",
        "2001-04": "1.015", "2001-05": "1.004", "2001-06": "1.006",
        "2001-07": "0.983", "2001-08": "0.998", "2001-09": "1.004",
        "2001-10": "1.002", "2001-11": "1.005", "2001-12": "1.016",
    }

    def test_two_years_count(self):
        """Two full years → 24 records."""
        result = parse_raw_data(self.SAMPLE_TWO_YEARS)
        self.assertEqual(len(result), 24)

    def test_two_years_values(self):
        """Values match the existing inflation_rates.json exactly."""
        result = parse_raw_data(self.SAMPLE_TWO_YEARS)
        expected = {**self.EXPECTED_2000, **self.EXPECTED_2001}
        self.assertEqual(result, expected)

    def test_key_format(self):
        """Keys have YYYY-MM format with leading zero."""
        result = parse_raw_data(self.SAMPLE_TWO_YEARS)
        for key in result:
            with self.subTest(key=key):
                self.assertRegex(key, r"^\d{4}-\d{2}$")

    def test_empty_input_raises(self):
        """Empty string → ValueError."""
        with self.assertRaises(ValueError):
            parse_raw_data("   ")

    def test_whitespace_only_raises(self):
        """Only whitespace/newlines → ValueError."""
        with self.assertRaises(ValueError):
            parse_raw_data("\n\n\t  \n")

    def test_incomplete_year_skipped(self):
        """Year with incomplete data is skipped without error."""
        incomplete = "2000\t104,6\t103,3\t102,0"
        result = parse_raw_data(incomplete)
        self.assertEqual(len(result), 0)

    def test_incomplete_year_among_complete(self):
        """Incomplete year is skipped, complete year is processed."""
        mixed = (
            "2000\t104,6\t103,3\n"  # incomplete
            "2001\t101,5\t100,6\t100,6\t101,5\t100,4\t100,6"
            "\t98,3\t99,8\t100,4\t100,2\t100,5\t101,6\t106,1"
        )
        result = parse_raw_data(mixed)
        self.assertEqual(len(result), 12)
        self.assertIn("2001-01", result)
        self.assertNotIn("2000-01", result)

    def test_round_value_100_0(self):
        """100,0 (no change) → multiplier "1.0"."""
        result = parse_raw_data(self.SAMPLE_TWO_YEARS)
        self.assertEqual(result["2000-08"], "1.0")

    def test_deflation_value(self):
        """Value < 100 (deflation, e.g. 98,3) → multiplier < 1."""
        result = parse_raw_data(self.SAMPLE_TWO_YEARS)
        self.assertEqual(result["2001-07"], "0.983")

    def test_high_inflation_value(self):
        """Three-digit value (e.g. 104,6) → multiplier > 1."""
        result = parse_raw_data(self.SAMPLE_TWO_YEARS)
        self.assertEqual(result["2000-01"], "1.046")

    def test_annual_summary_excluded(self):
        """13th value (annual summary) is not included in the result."""
        result = parse_raw_data(self.SAMPLE_TWO_YEARS)
        # 125,8 — 2000 annual summary, should not be in the result
        self.assertNotIn("1.258", result.values())
        # Only 12 months per year
        year_2000_keys = [k for k in result if k.startswith("2000")]
        self.assertEqual(len(year_2000_keys), 12)

    def test_single_year(self):
        """One full year → 12 records."""
        single = (
            "2007\t100,5\t100,6\t100,2\t100,0\t100,6\t102,2"
            "\t101,4\t100,6\t102,1\t102,9\t102,1\t102,1\t116,6"
        )
        result = parse_raw_data(single)
        self.assertEqual(len(result), 12)
        self.assertEqual(result["2007-06"], "1.022")
        self.assertEqual(result["2007-04"], "1.0")

    def test_tabs_and_spaces_mixed(self):
        """Data with tabs and spaces is parsed correctly."""
        messy = (
            "2000  104,6  103,3  102,0  101,7  102,1  103,7  "
            "99,9  100,0  102,6  101,4  100,4  101,6  125,8"
        )
        result = parse_raw_data(messy)
        self.assertEqual(len(result), 12)
        self.assertEqual(result["2000-01"], "1.046")


if __name__ == "__main__":
    unittest.main()
