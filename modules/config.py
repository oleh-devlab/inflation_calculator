import os
import sys
from decimal import Decimal, getcontext

# --- Configuration ---
def setup_config():
    getcontext().prec = 18 

setup_config()

FALLBACK_ANNUAL_INFLATION_RATE = Decimal('0.08')

# --- Robust logic for determining the script directory ---
def get_script_dir():
    try:
        # Go up one level since we are in modules/config.py
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass

    if sys.argv and sys.argv[0]:
        return os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    
    return os.getcwd()

script_dir = get_script_dir()

# --- PATH SYSTEM ---
DATA_FOLDER_NAME = 'data_records'
DATA_DIR = os.path.join(script_dir, DATA_FOLDER_NAME)

def init_directories():
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
        except OSError as e:
            print(f"[Error] Failed to create data directory: {e}")

# Initialize directories immediately on import
init_directories()

INFLATION_RATES_FILENAME = os.path.join(script_dir, 'inflation_rates.json')
