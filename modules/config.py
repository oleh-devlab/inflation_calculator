from decimal import Decimal, getcontext

# --- Decimal precision ---
getcontext().prec = 18

# --- Constants ---
FALLBACK_ANNUAL_INFLATION_RATE = Decimal('0.08')

DEFAULT_DATA_FOLDER_NAME = 'data_records'
DEFAULT_INFLATION_RATES_FILENAME = 'inflation_rates.json'
