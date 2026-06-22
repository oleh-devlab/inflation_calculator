"""
Custom exceptions for the Inflation Calculator library.
"""


class InflationCalculatorError(Exception):
    """Base exception for all Inflation Calculator errors."""
    pass


class InvalidAmountError(InflationCalculatorError):
    """Raised when an invalid monetary amount is provided."""
    pass


class InvalidDateError(InflationCalculatorError):
    """Raised when an invalid or out-of-range date is provided."""
    pass


class RecordNotFoundError(InflationCalculatorError):
    """Raised when a record index is out of bounds."""
    pass


class InvalidInflationRateError(InflationCalculatorError):
    """Raised when an invalid inflation rate value is provided."""
    pass


class StorageError(InflationCalculatorError):
    """Raised when a file read/write operation fails."""
    pass
