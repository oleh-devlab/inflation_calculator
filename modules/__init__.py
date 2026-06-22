# Inflation Calculator — Public API
#
# Usage:
#     from modules import InflationCalculator
#     calc = InflationCalculator("records.json", "rates.json")

from .api import InflationCalculator
from .exceptions import (
    InflationCalculatorError,
    InvalidAmountError,
    InvalidDateError,
    RecordNotFoundError,
    InvalidInflationRateError,
    StorageError,
)

__all__ = [
    "InflationCalculator",
    "InflationCalculatorError",
    "InvalidAmountError",
    "InvalidDateError",
    "RecordNotFoundError",
    "InvalidInflationRateError",
    "StorageError",
]
