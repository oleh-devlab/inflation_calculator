"""
Inflation Calculator — Public API.

Usage:
    from modules import InflationCalculator

    calc = InflationCalculator(
        records_filepath="data_records/default.json",
        inflation_rates_filepath="inflation_rates.json"
    )
    calc.add_record(Decimal("5000"), date(2023, 6, 1), "salary")
    report = calc.get_report()
"""

import os
import datetime
from decimal import Decimal, InvalidOperation

from .config import DEFAULT_DATA_FOLDER_NAME
from .logic import get_current_value, check_inflation_data_gaps
from .storage import (
    load_records_from_file,
    save_records_to_file,
    load_inflation_rates_from_file,
    save_inflation_rates_to_file,
)
from .exceptions import (
    InvalidAmountError,
    InvalidDateError,
    RecordNotFoundError,
    InvalidInflationRateError,
    StorageError,
)


class InflationCalculator:
    """
    Main API for the Inflation Calculator library.

    Encapsulates records management, inflation data, and calculations.
    The consumer provides file paths; the API handles all data operations.
    """

    def __init__(
        self,
        records_filepath: str,
        inflation_rates_filepath: str,
        *,
        auto_load: bool = True,
        auto_save: bool = True,
    ):
        """
        Initialize the calculator.

        Args:
            records_filepath: Path to the JSON file with user records.
            inflation_rates_filepath: Path to the JSON file with inflation rates.
            auto_load: If True, load data from files on init.
            auto_save: If True, persist changes to disk after every mutation.
        """
        self._records_filepath = os.path.abspath(records_filepath)
        self._inflation_rates_filepath = os.path.abspath(inflation_rates_filepath)
        self._auto_save = auto_save

        self._records: list[dict] = []
        self._inflation_rates: dict[str, Decimal] = {}

        # Ensure the directory for records exists
        records_dir = os.path.dirname(self._records_filepath)
        if records_dir:
            os.makedirs(records_dir, exist_ok=True)

        if auto_load:
            self.reload()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def records_filepath(self) -> str:
        """Absolute path to the current records file."""
        return self._records_filepath

    @property
    def inflation_rates_filepath(self) -> str:
        """Absolute path to the inflation rates file."""
        return self._inflation_rates_filepath

    # ------------------------------------------------------------------
    # Records — CRUD
    # ------------------------------------------------------------------

    def add_record(
        self,
        amount: Decimal | str | int | float,
        date: datetime.date,
        comment: str = "",
    ) -> dict:
        """
        Add a single record.

        Args:
            amount: Monetary amount (positive). Strings/ints/floats are
                    converted to Decimal automatically.
            date: Date the amount was received. Must not be in the future.
            comment: Optional comment.

        Returns:
            The created record dict with keys 'amount', 'date', 'comment'.

        Raises:
            InvalidAmountError: If amount is non-positive or unparsable.
            InvalidDateError: If date is in the future.
        """
        amount = self._parse_amount(amount)
        self._validate_date(date)

        record = {
            "amount": amount,
            "date": date,
            "comment": comment,
        }
        self._records.append(record)
        self._persist_records()
        return record

    def delete_record(self, index: int) -> dict:
        """
        Delete a record by its 0-based index.

        Returns:
            The deleted record dict.

        Raises:
            RecordNotFoundError: If index is out of range.
        """
        if not (0 <= index < len(self._records)):
            raise RecordNotFoundError(
                f"Record index {index} is out of range "
                f"(0..{len(self._records) - 1})."
            )
        removed = self._records.pop(index)
        self._persist_records()
        return removed

    def delete_all_records(self) -> int:
        """
        Delete every record.

        Returns:
            The number of records that were deleted.
        """
        count = len(self._records)
        self._records.clear()
        self._persist_records()
        return count

    def get_records(self) -> list[dict]:
        """Return a shallow copy of the records list."""
        return list(self._records)

    @property
    def records_count(self) -> int:
        """Number of records currently loaded."""
        return len(self._records)

    # ------------------------------------------------------------------
    # Inflation Data
    # ------------------------------------------------------------------

    def set_inflation_rate(
        self,
        year_month: str,
        rate_percent: Decimal | str | int | float,
    ) -> None:
        """
        Add or update an inflation rate for a given month.

        Args:
            year_month: Month key in "YYYY-MM" format (e.g. "2024-01").
            rate_percent: CPI-based value (e.g. 101.4 means 1.4% inflation).
                          Stored internally as a multiplier (101.4 → 1.014).

        Raises:
            InvalidInflationRateError: If the value or format is invalid.
        """
        # Validate year_month format
        try:
            datetime.datetime.strptime(year_month, "%Y-%m")
        except ValueError:
            raise InvalidInflationRateError(
                f"Invalid year-month format: '{year_month}'. Expected YYYY-MM."
            )

        # Parse and validate rate
        try:
            rate = Decimal(str(rate_percent))
        except (InvalidOperation, ValueError) as e:
            raise InvalidInflationRateError(
                f"Cannot parse rate '{rate_percent}': {e}"
            ) from e

        if rate <= 0:
            raise InvalidInflationRateError(
                f"Inflation rate must be > 0, got {rate}."
            )

        self._inflation_rates[year_month] = rate / Decimal("100")
        self._persist_inflation_rates()

    def get_inflation_rates(self) -> dict[str, Decimal]:
        """Return a shallow copy of the inflation rates dict."""
        return dict(self._inflation_rates)

    def check_data_gaps(self) -> str | None:
        """
        Check for missing months in the inflation database.

        Returns:
            A warning string if gaps are found, or None if data is complete.
        """
        return check_inflation_data_gaps(self._inflation_rates)

    # ------------------------------------------------------------------
    # Calculations
    # ------------------------------------------------------------------

    def calculate_current_value(
        self,
        amount: Decimal | str | int | float,
        date: datetime.date,
    ) -> Decimal:
        """
        Calculate today's value of a past amount, adjusted for inflation.

        Args:
            amount: Original monetary amount.
            date: Date the amount was received.

        Returns:
            Inflation-adjusted value as of today.
        """
        amount = self._parse_amount(amount)
        return get_current_value(amount, date, self._inflation_rates)

    def get_report(self) -> dict:
        """
        Generate a full report for all loaded records.

        Returns:
            A dict with structure:
            {
                "total_nominal": Decimal,
                "total_adjusted": Decimal,
                "loss_percent": Decimal,
                "oldest_date": datetime.date | None,
                "records": [
                    {
                        "amount": Decimal,
                        "date": datetime.date,
                        "comment": str,
                        "adjusted_value": Decimal,
                        "loss_percent": Decimal,
                    },
                    ...
                ]
            }
        """
        q = Decimal("0.01")

        if not self._records:
            return {
                "total_nominal": Decimal("0"),
                "total_adjusted": Decimal("0"),
                "loss_percent": Decimal("0"),
                "oldest_date": None,
                "records": [],
            }

        total_raw = sum(r["amount"] for r in self._records).quantize(q)
        oldest_date = min(r["date"] for r in self._records)

        detailed_records = []
        total_adjusted = Decimal(0)

        for r in self._records:
            adjusted = get_current_value(
                r["amount"], r["date"], self._inflation_rates
            )
            total_adjusted += adjusted

            loss = Decimal(0)
            if adjusted > r["amount"]:
                loss = (1 - (r["amount"] / adjusted)) * 100

            detailed_records.append(
                {
                    "amount": r["amount"],
                    "date": r["date"],
                    "comment": r.get("comment", ""),
                    "adjusted_value": adjusted.quantize(q),
                    "loss_percent": loss.quantize(q),
                }
            )

        total_adjusted = total_adjusted.quantize(q)

        total_loss = Decimal(0)
        if total_adjusted > total_raw and total_raw > 0:
            total_loss = (1 - (total_raw / total_adjusted)) * 100

        return {
            "total_nominal": total_raw,
            "total_adjusted": total_adjusted,
            "loss_percent": total_loss.quantize(q),
            "oldest_date": oldest_date,
            "records": detailed_records,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Explicitly save both records and inflation rates to disk."""
        save_records_to_file(self._records, self._records_filepath)
        save_inflation_rates_to_file(
            self._inflation_rates, self._inflation_rates_filepath
        )

    def reload(self) -> None:
        """Reload both records and inflation rates from disk."""
        self._records = load_records_from_file(self._records_filepath)
        self._inflation_rates = load_inflation_rates_from_file(
            self._inflation_rates_filepath
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_amount(amount: Decimal | str | int | float) -> Decimal:
        """Convert various numeric types to Decimal and validate."""
        try:
            result = Decimal(str(amount)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as e:
            raise InvalidAmountError(
                f"Cannot parse amount '{amount}': {e}"
            ) from e

        if result <= 0:
            raise InvalidAmountError(
                f"Amount must be positive, got {result}."
            )
        return result

    @staticmethod
    def _validate_date(date: datetime.date) -> None:
        """Validate that the date is not in the future."""
        if date > datetime.date.today():
            raise InvalidDateError(
                f"Date {date} is in the future."
            )

    def _persist_records(self) -> None:
        """Save records to disk if auto_save is enabled."""
        if self._auto_save:
            save_records_to_file(self._records, self._records_filepath)

    def _persist_inflation_rates(self) -> None:
        """Save inflation rates to disk if auto_save is enabled."""
        if self._auto_save:
            save_inflation_rates_to_file(
                self._inflation_rates, self._inflation_rates_filepath
            )
