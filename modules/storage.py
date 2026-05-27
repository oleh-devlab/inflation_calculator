import json
import os
import datetime
from decimal import Decimal
from .config import DATA_DIR, INFLATION_RATES_FILENAME

class CustomJSONEncoder(json.JSONEncoder):
    """
    Спеціальний кодувальник для JSON, який вміє обробляти
    об'єкти Decimal та datetime.date.
    """
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, datetime.date):
            return o.isoformat()
        return super().default(o)


def save_records_to_file(records: list, filepath: str):
    """Зберігає список записів (сум) у JSON-файл за вказаним шляхом."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, cls=CustomJSONEncoder, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Не вдалося зберегти записи у файл {filepath}: {e}")

def load_records_from_file(filepath: str) -> list:
    """Завантажує та конвертує дані записів (сум) з JSON-файлу."""
    if not os.path.exists(filepath):
        # Якщо файлу немає, повертаємо порожній список (новий профіль)
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
            print(f"[Інфо] Завантажено {len(processed_records)} записів з файлу '{os.path.basename(filepath)}'.")
            return processed_records
    except Exception as e:
        print(f"Помилка читання файлу {filepath}: {e}. Починаємо з порожнього списку.")
        return []

def save_inflation_rates_to_file(rates: dict, filename: str):
    """Зберігає словник коефіцієнтів інфляції у JSON-файл."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(rates, f, cls=CustomJSONEncoder, indent=4, ensure_ascii=False, sort_keys=True)
        print(f"[Інфо] Коефіцієнти інфляції збережено у {filename}.")
    except IOError as e:
        print(f"Не вдалося зберегти коефіцієнти інфляції: {e}")

def load_inflation_rates_from_file(filename: str) -> dict:
    """Завантажує та конвертує коефіцієнти інфляції з JSON-файлу."""
    if not os.path.exists(filename):
        return {} 

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            processed_rates = {key: Decimal(value) for key, value in raw_data.items()}
            print(f"[Інфо] Завантажено {len(processed_rates)} міс. коефіцієнтів інфляції.")
            return processed_rates
    except Exception as e:
        print(f"Помилка читання файлу інфляції {filename}: {e}. Починаємо з порожнього списку.")
        return {}
