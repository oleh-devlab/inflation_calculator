"""
Скрипт імпорту даних інфляції з локального джерела.

Парсить «сирі» дані (копію таблиці з сайту МінФіну) та зберігає
помісячні коефіцієнти інфляції у JSON-файл, сумісний з основною програмою.

Використання:
    python import_local_data.py                     # парсить дані з RAW_DATA_STRING
    python import_local_data.py --input raw.txt     # парсить дані з файлу
"""

import argparse
import re
import sys
from decimal import Decimal, InvalidOperation

# Використовуємо єдиний конфіг проєкту для шляхів
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
from modules.config import INFLATION_RATES_FILENAME
from modules.storage import load_inflation_rates_from_file, save_inflation_rates_to_file


# Кількість місяців у році + 1 річний підсумок
_EXPECTED_VALUES_PER_YEAR = 13

# Рік у форматі 20xx
_YEAR_BLOCK_REGEX = re.compile(r"(20\d{2})(.+?)(?=20\d{2}|$)", flags=re.DOTALL)

# Число інфляції: 2-3 цифри, кома, 1 цифра (напр. "104,6" або "99,9")
_NUMBER_REGEX = re.compile(r"(\d{2,3},\d)")


# ---------------------------------------------------------------------------
# "Сирі" дані — вставте сюди копію таблиці з сайту МінФіну,
# або передайте файл через аргумент --input
# ---------------------------------------------------------------------------
RAW_DATA_STRING = """

"""


def parse_raw_data(raw_text: str) -> dict[str, str]:
    """Парсить сирий текст таблиці інфляції та повертає словник коефіцієнтів.

    Args:
        raw_text: Текст із таблиці МінФіну (рядки з роками та значеннями).

    Returns:
        Словник ``{"YYYY-MM": "коефіцієнт", ...}``, де коефіцієнт — рядок
        Decimal-сумісного числа (напр. ``"1.046"``).

    Raises:
        ValueError: Якщо у тексті не знайдено жодного блоку даних.
    """
    clean_text = raw_text.replace("\n", "")
    year_blocks = _YEAR_BLOCK_REGEX.findall(clean_text)

    if not year_blocks:
        raise ValueError(
            "Не знайдено жодного блоку даних. Перевірте вхідний текст."
        )

    result: dict[str, str] = {}
    skipped_years: list[str] = []

    for year_str, numbers_str in year_blocks:
        numbers = _NUMBER_REGEX.findall(numbers_str)

        if len(numbers) != _EXPECTED_VALUES_PER_YEAR:
            skipped_years.append(f"{year_str} ({len(numbers)} значень)")
            continue

        # Перші 12 значень — місяці (Січень … Грудень)
        for month_index, value_str in enumerate(numbers[:12], start=1):
            key = f"{year_str}-{month_index:02d}"

            try:
                multiplier = Decimal(value_str.replace(",", ".")) / Decimal("100")
                result[key] = str(multiplier)
            except InvalidOperation:
                print(f"  [!] Некоректне значення «{value_str}» для {key}, пропущено.")

    if skipped_years:
        print(f"  [!] Пропущено роки: {', '.join(skipped_years)}")

    return result


def read_input_text(filepath: str | None) -> str:
    """Повертає сирий текст: з файлу або з вбудованої константи."""
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            print(f"[Помилка] Не вдалося прочитати файл «{filepath}»: {e}")
            sys.exit(1)

    return RAW_DATA_STRING


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Імпорт даних інфляції з локального джерела у JSON."
    )
    parser.add_argument(
        "--input", "-i",
        metavar="FILE",
        help="Шлях до текстового файлу із сирими даними (замість RAW_DATA_STRING).",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Доповнити наявний файл замість перезаписування.",
    )
    args = parser.parse_args()

    # 1. Зчитуємо вхідні дані
    raw_text = read_input_text(args.input)

    if not raw_text.strip():
        print("[Помилка] Вхідні дані порожні.")
        print("  Вставте дані у RAW_DATA_STRING або передайте файл через --input.")
        sys.exit(1)

    # 2. Парсимо
    print("Починаю парсинг даних…")
    try:
        parsed = parse_raw_data(raw_text)
    except ValueError as e:
        print(f"[Помилка] {e}")
        sys.exit(1)

    print(f"Розпізнано {len(parsed)} місячних записів.")

    # 3. Зберігаємо (через єдиний storage-модуль проєкту)
    if args.merge:
        existing = load_inflation_rates_from_file(INFLATION_RATES_FILENAME)
        # Конвертуємо Decimal → str для сумісності
        merged = {k: str(v) for k, v in existing.items()}
        merged.update(parsed)
        parsed = merged
        print(f"Після злиття: {len(parsed)} записів загалом.")

    save_inflation_rates_to_file(parsed, INFLATION_RATES_FILENAME)
    print("Готово! Тепер можна запускати основну програму.")


if __name__ == "__main__":
    main()