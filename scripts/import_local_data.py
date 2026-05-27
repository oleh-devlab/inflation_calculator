import re
import json
from decimal import Decimal
import os

# --- ОНОВЛЕНА ЛОГІКА ШЛЯХІВ ---
# Отримуємо абсолютний шлях до папки, де знаходиться цей скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))

# Назва файлу, який буде згенеровано (в тій самій папці)
OUTPUT_FILENAME = os.path.join(script_dir, 'inflation_rates.json')
# -------------------------------

# "Сирі" дані, копія таблиці на сайті МінФіну
RAW_DATA_STRING = """

"""

def parse_and_save():
    print(f"Починаю парсинг даних...")
    
    # Словник, який ми будемо зберігати у JSON
    inflation_data = {}
    
    # 1. Регулярний вираз для пошуку року (20xx) і даних, що йдуть за ним.
    #    (?=...) - це "positive lookahead", він шукає наступний рік, але не "з'їдає" його.
    year_block_regex = re.compile(r"(20\d{2})(.+?)(?=20\d{2}|$)", flags=re.DOTALL)
    
    # 2. Регулярний вираз для пошуку чисел інфляції (напр. "104,6" або "99,9")
    #    Він шукає 2 або 3 цифри, кому, і 1 цифру
    numbers_regex = re.compile(r"(\d{2,3},\d)")
    
    # Видаляємо всі переноси рядків для чистоти
    clean_data = RAW_DATA_STRING.replace("\n", "")
    
    year_blocks = year_block_regex.findall(clean_data)
    
    if not year_blocks:
        print("Помилка: не знайдено жодного блоку даних. Перевірте RAW_DATA_STRING.")
        return

    total_months_processed = 0

    # Обробляємо кожен знайдений рік
    for year_str, numbers_str in year_blocks:
        numbers = numbers_regex.findall(numbers_str)
        
        # Ми очікуємо 12 місяців + 1 річний підсумок = 13 чисел
        if len(numbers) != 13:
            print(f"Попередження: У році {year_str} знайдено {len(numbers)} чисел замість 13. Пропускаю цей рік.")
            continue
            
        print(f"Обробляю {year_str} рік...")
        
        # Беремо лише перші 12 значень (місяці)
        monthly_values = numbers[:12]
        
        # Місяці у даних йдуть з Грудня по Січень, але в описі сказано "до січня".
        # Давайте припустимо, що вони йдуть по порядку: Січень, Лютий...
        # 2000: Січ 104,6, Лют 103,3... Груд 101,6. 
        
        for i, value_str in enumerate(monthly_values):
            month_index = i + 1 # i = 0 -> month = 1 (Січень)
            
            # Створюємо ключ у форматі "YYYY-MM"
            month_str = f"{month_index:02d}" # 1 -> "01", 12 -> "12"
            data_key = f"{year_str}-{month_str}"
            
            # Конвертуємо "104,6" у "1.046"
            try:
                # 1. Замінюємо кому на крапку
                decimal_str = value_str.replace(',', '.')
                # 2. Створюємо Decimal
                value_dec = Decimal(decimal_str)
                # 3. Ділимо на 100, щоб отримати коефіцієнт
                multiplier_dec = value_dec / Decimal('100')
                
                # Зберігаємо у словник ЯК РЯДОК, 
                # бо наш основний скрипт очікує рядок і сам конвертує його в Decimal
                inflation_data[data_key] = str(multiplier_dec)
                total_months_processed += 1
                
            except Exception as e:
                print(f"Помилка конвертації: {e} для {data_key} зі значенням {value_str}")

    print("-" * 30)
    print(f"Парсинг завершено.")
    print(f"Успішно оброблено {len(year_blocks)} років.")
    print(f"Загалом {total_months_processed} місячних записів буде збережено.")
    
    # Збереження у файл
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            # indent=4 для красивого форматування
            # sort_keys=True щоб роки йшли по порядку
            json.dump(inflation_data, f, indent=4, sort_keys=True)
        print(f"\nДані успішно збережено у файл: {OUTPUT_FILENAME}")
        print("Тепер ви можете запускати свою основну програму!")
    except Exception as e:
        print(f"\n[ПОМИЛКА] Не вдалося зберегти файл: {e}")

# --- Запуск парсера ---
if __name__ == "__main__":
    parse_and_save()