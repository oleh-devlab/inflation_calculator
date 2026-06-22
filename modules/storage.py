import json
import os
import datetime
from decimal import Decimal

from .exceptions import StorageError


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that can handle
    Decimal and datetime.date objects.
    """
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, datetime.date):
            return o.isoformat()
        return super().default(o)


def save_records_to_file(records: list, filepath: str):
    """Saves a list of records (amounts) to a JSON file at the specified path."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, cls=CustomJSONEncoder, indent=4, ensure_ascii=False)
    except IOError as e:
        raise StorageError(f"Failed to save records to file {filepath}: {e}") from e

def load_records_from_file(filepath: str) -> list:
    """Loads and converts record data (amounts) from a JSON file."""
    if not os.path.exists(filepath):
        return [] 

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            processed_records = []
            for record in raw_data:
                processed_records.append({
                    'amount': Decimal(record['amount']),
                    'date': datetime.date.fromisoformat(record['date']),
                    'comment': record.get('comment', '')
                })
            return processed_records
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise StorageError(f"Error reading file {filepath}: {e}") from e
    except IOError as e:
        raise StorageError(f"Cannot open file {filepath}: {e}") from e

def save_inflation_rates_to_file(rates: dict, filename: str):
    """Saves a dictionary of inflation multipliers to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(rates, f, cls=CustomJSONEncoder, indent=4, ensure_ascii=False, sort_keys=True)
    except IOError as e:
        raise StorageError(f"Failed to save inflation multipliers: {e}") from e

def load_inflation_rates_from_file(filename: str) -> dict:
    """Loads and converts inflation multipliers from a JSON file."""
    if not os.path.exists(filename):
        return {} 

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            processed_rates = {key: Decimal(value) for key, value in raw_data.items()}
            return processed_rates
    except (json.JSONDecodeError, ValueError) as e:
        raise StorageError(f"Error reading inflation file {filename}: {e}") from e
    except IOError as e:
        raise StorageError(f"Cannot open inflation file {filename}: {e}") from e
