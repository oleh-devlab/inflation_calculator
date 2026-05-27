import os
import sys
from decimal import Decimal, getcontext

# --- Налаштування ---
def setup_config():
    getcontext().prec = 18 

setup_config()

FALLBACK_ANNUAL_INFLATION_RATE = Decimal('0.08')

# --- Надійна логіка для визначення директорії скрипта ---
def get_script_dir():
    try:
        # Піднімаємось на один рівень вище, оскільки знаходимось у modules/config.py
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass

    if sys.argv and sys.argv[0]:
        return os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    
    return os.getcwd()

script_dir = get_script_dir()

# --- СИСТЕМА ШЛЯХІВ ---
DATA_FOLDER_NAME = 'data_records'
DATA_DIR = os.path.join(script_dir, DATA_FOLDER_NAME)

def init_directories():
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
        except OSError as e:
            print(f"[Помилка] Не вдалося створити папку для даних: {e}")

# Викликаємо ініціалізацію одразу при імпорті
init_directories()

INFLATION_RATES_FILENAME = os.path.join(script_dir, 'inflation_rates.json')
