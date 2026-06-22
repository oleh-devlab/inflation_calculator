"""
Script for importing inflation data from a local source.

Parses "raw" data (a copy of a table from the Ministry of Finance website)
and saves monthly inflation multipliers to a JSON file compatible with the
main application.

Usage:
    python import_local_data.py                     # parses data from RAW_DATA_STRING
    python import_local_data.py --input raw.txt     # parses data from a file
"""

import argparse
import re
import sys
from decimal import Decimal, InvalidOperation

# Use the project's single config for paths
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from modules.config import DEFAULT_INFLATION_RATES_FILENAME
from modules.storage import load_inflation_rates_from_file, save_inflation_rates_to_file

INFLATION_RATES_FILENAME = os.path.join(_SCRIPT_DIR, DEFAULT_INFLATION_RATES_FILENAME)


# Number of months in a year + 1 annual summary
_EXPECTED_VALUES_PER_YEAR = 13

# Year in 20xx format
_YEAR_BLOCK_REGEX = re.compile(r"(20\d{2})(.+?)(?=20\d{2}|$)", flags=re.DOTALL)

# Inflation number: 2-3 digits, comma, 1 digit (e.g. "104,6" or "99,9")
_NUMBER_REGEX = re.compile(r"(\d{2,3},\d)")


# ---------------------------------------------------------------------------
# "Raw" data — paste a copy of the table from the Ministry of Finance website
# here, or pass a file via the --input argument
# ---------------------------------------------------------------------------
RAW_DATA_STRING = """

"""


def parse_raw_data(raw_text: str) -> dict[str, str]:
    """Parses raw inflation table text and returns a dictionary of multipliers.

    Args:
        raw_text: Text from the Ministry of Finance table (rows with years and values).

    Returns:
        Dictionary ``{"YYYY-MM": "multiplier", ...}``, where the multiplier is a
        Decimal-compatible string (e.g. ``"1.046"``).

    Raises:
        ValueError: If no data blocks are found in the text.
    """
    clean_text = raw_text.replace("\n", "")
    year_blocks = _YEAR_BLOCK_REGEX.findall(clean_text)

    if not year_blocks:
        raise ValueError(
            "No data blocks found. Please check the input text."
        )

    result: dict[str, str] = {}
    skipped_years: list[str] = []

    for year_str, numbers_str in year_blocks:
        numbers = _NUMBER_REGEX.findall(numbers_str)

        if len(numbers) != _EXPECTED_VALUES_PER_YEAR:
            skipped_years.append(f"{year_str} ({len(numbers)} values)")
            continue

        # First 12 values — months (January … December)
        for month_index, value_str in enumerate(numbers[:12], start=1):
            key = f"{year_str}-{month_index:02d}"

            try:
                multiplier = Decimal(value_str.replace(",", ".")) / Decimal("100")
                result[key] = str(multiplier)
            except InvalidOperation:
                print(f"  [!] Invalid value '{value_str}' for {key}, skipped.")

    if skipped_years:
        print(f"  [!] Skipped years: {', '.join(skipped_years)}")

    return result


def read_input_text(filepath: str | None) -> str:
    """Returns raw text: from a file or from the built-in constant."""
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            print(f"[Error] Failed to read file '{filepath}': {e}")
            sys.exit(1)

    return RAW_DATA_STRING


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import inflation data from a local source into JSON."
    )
    parser.add_argument(
        "--input", "-i",
        metavar="FILE",
        help="Path to a text file with raw data (instead of RAW_DATA_STRING).",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing file instead of overwriting.",
    )
    args = parser.parse_args()

    # 1. Read input data
    raw_text = read_input_text(args.input)

    if not raw_text.strip():
        print("[Error] Input data is empty.")
        print("  Paste data into RAW_DATA_STRING or pass a file via --input.")
        sys.exit(1)

    # 2. Parse
    print("Starting data parsing...")
    try:
        parsed = parse_raw_data(raw_text)
    except ValueError as e:
        print(f"[Error] {e}")
        sys.exit(1)

    print(f"Recognized {len(parsed)} monthly records.")

    # 3. Save (via the project's single storage module)
    if args.merge:
        existing = load_inflation_rates_from_file(INFLATION_RATES_FILENAME)
        # Convert Decimal → str for compatibility
        merged = {k: str(v) for k, v in existing.items()}
        merged.update(parsed)
        parsed = merged
        print(f"After merge: {len(parsed)} records total.")

    save_inflation_rates_to_file(parsed, INFLATION_RATES_FILENAME)
    print("Done! You can now run the main application.")


if __name__ == "__main__":
    main()