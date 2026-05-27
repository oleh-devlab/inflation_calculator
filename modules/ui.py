import os
import datetime
from decimal import Decimal

from .logic import get_current_value
from .storage import save_records_to_file, save_inflation_rates_to_file, load_records_from_file
from .config import DATA_DIR, INFLATION_RATES_FILENAME

def print_records_list(records: list, with_inflation: bool, inflation_rates: dict):
    if not records:
        print("Список записів порожній.")
        return
    
    print("-" * 50)
    q = Decimal('0.01') 
    
    for i, record in enumerate(records):
        comment_str = f" | {record.get('comment')}" if record.get('comment') else ""
        line = f"{i+1}. Сума: {record['amount']:.2f} грн | Дата: {record['date']}{comment_str}"
        if with_inflation:
            adjusted_val = get_current_value(record['amount'], record['date'], inflation_rates)
            loss_percent = Decimal(0)
            if adjusted_val > record['amount']:
                loss_percent = (1 - (record['amount'] / adjusted_val)) * 100
            
            line += f"\n   -> Сьогодні: {adjusted_val.quantize(q)} грн | Втрата: {loss_percent.quantize(q)}%"
        print(line)
    print("-" * 50)

def add_record_loop(records: list, current_filename_path: str):
    """Дія 1: Додавання записів."""
    print(f"\n--- Додавання нових записів (файл: {os.path.basename(current_filename_path)}) ---")
    
    records_added_count = 0
    
    while True:
        while True:
            try:
                amount_str = input("\nВведіть суму (або 0 для виходу): ")
                if amount_str.strip() == '0':
                    break
                amount = Decimal(amount_str).quantize(Decimal('0.01'))
                if amount <= 0:
                    print("Сума має бути додатною.")
                    continue
                break
            except Exception as e:
                print(f"Помилка вводу: {e}")
        
        if amount_str.strip() == '0':
            break

        print(f"Підказка: формат YYYY-MM-DD (наприклад, {datetime.date.today()})")
        while True:
            try:
                date_str = input("Введіть дату отримання: ")
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj > datetime.date.today():
                    print("Дата не може бути у майбутньому.")
                    continue
                break
            except ValueError:
                print("Неправильний формат. Використовуйте YYYY-MM-DD.")

        comment = input("Коментар (або 0 пропустити): ").strip()
        if comment == '0': comment = ""

        records.append({'amount': amount, 'date': date_obj, 'comment': comment})
        records_added_count += 1
        print(f"[Успіх] Додано: {amount:.2f} грн")

    if records_added_count > 0:
        print(f"Збереження даних у {os.path.basename(current_filename_path)}...")
        save_records_to_file(records, current_filename_path)
    else:
        print("Вихід без змін.")

def delete_record(records: list, current_filename_path: str):
    """Дія 2: Видалення записів."""
    print(f"\n--- Видалення записів (файл: {os.path.basename(current_filename_path)}) ---")
    
    if not records:
        print("Немає записів.")
        return

    data_was_changed = False
    
    while True:
        print("\nПоточні записи:")
        print_records_list(records, with_inflation=False, inflation_rates={}) 
        
        print("\nВведіть номер (1...N), -1 (все), 0 (вихід)")
        try:
            choice = int(input("Вибір: "))
            if choice == 0: break
            
            if choice == -1:
                if input("Видалити ВСЕ? (так/ні): ").lower() == 'так':
                    records.clear()
                    data_was_changed = True
                    print("Очищено.")
                    break
            
            elif 1 <= choice <= len(records):
                rem = records.pop(choice - 1)
                data_was_changed = True
                print(f"Видалено: {rem['amount']} грн")
                if not records: break
            else:
                print("Неправильний номер.")
        except ValueError:
            print("Введіть ціле число.")

    if data_was_changed:
        save_records_to_file(records, current_filename_path)
        print("Зміни збережено.")

def show_processed_data(records: list, inflation_rates: dict, current_filename_path: str):
    """Дія 3: Звіт."""
    filename = os.path.basename(current_filename_path)
    print(f"\n--- Аналіз даних (Профіль: {filename}) ---")
    
    if not records:
        print("Немає даних.")
        return

    q = Decimal('0.01')
    total_raw = sum(r['amount'] for r in records).quantize(q)
    oldest_date = min(r['date'] for r in records)
    
    total_adjusted = Decimal(0)
    for r in records:
        total_adjusted += get_current_value(r['amount'], r['date'], inflation_rates)
    total_adjusted = total_adjusted.quantize(q)
        
    total_loss_percent = Decimal(0)
    if total_adjusted > total_raw and total_raw > 0:
        total_loss_percent = (1 - (total_raw / total_adjusted)) * 100
    
    print(f"Загальна сума (номінал):      {total_raw} грн")
    print(f"Найстаріший запис:            {oldest_date}")
    print(f"Реальна вартість сьогодні:    {total_adjusted} грн")
    print(f"Втрата купівельної спроможності: {total_loss_percent.quantize(q)}%")
    
    print("\nДетально:")
    print_records_list(records, with_inflation=True, inflation_rates=inflation_rates)

def add_inflation_data_loop(inflation_rates: dict):
    """Дія 4: Введення інфляції."""
    print("\n--- Введення інфляції ---")
    print("Приклад: для інфляції 1.4% введіть '101.4'")
    
    while True:
        try:
            d_str = input("Рік-Місяць (YYYY-MM): ")
            start_date = datetime.datetime.strptime(d_str, "%Y-%m").date()
            break
        except ValueError:
            print("Формат YYYY-MM.")
            
    current_date = start_date
    added_count = 0
    
    while True:
        current_key = current_date.strftime("%Y-%m") 
        existing = f" (поточне: {inflation_rates[current_key]*100}) " if current_key in inflation_rates else ""
        
        rate_str = input(f"Інфляція за {current_key}{existing} (0 вихід): ").strip()
        if rate_str == '0': break
        
        try:
            rate_decimal = Decimal(rate_str)
            if rate_decimal <= 0:
                print("Число має бути > 0.")
                continue

            if rate_decimal < 80:
                print(f"[!] УВАГА: Ви ввели {rate_decimal}.")
                print(f"    Це означає, що ціни ВПАЛИ, а гроші знецінилися до {rate_decimal}% від номіналу.")
                print(f"    Якщо інфляція була {rate_decimal}%, ви мали ввести {100 + rate_decimal}.")
                confirm = input("    Ви впевнені, що хочете зберегти саме це число? (так/ні): ").lower()
                if confirm != 'так':
                    continue
                
            inflation_rates[current_key] = rate_decimal / Decimal('100')
            added_count += 1
            
            # Наступний місяць
            year, month = current_date.year, current_date.month
            month += 1
            if month > 12: month, year = 1, year + 1
            current_date = datetime.date(year, month, 1)

        except Exception as e:
            print(f"Помилка: {e}")

    if added_count > 0:
        save_inflation_rates_to_file(inflation_rates, INFLATION_RATES_FILENAME)
        print("Дані збережено.")

def settings_menu(current_records: list, current_filepath: str):
    """
    Дія 5: Налаштування та вибір файлу.
    Повертає (new_records_list, new_filepath).
    """
    while True:
        current_name = os.path.basename(current_filepath)
        print(f"\n--- Налаштування (Поточний файл: {current_name}) ---")
        print("1. Змінити/Створити файл записів")
        print("0. Назад у головне меню")
        
        choice = input("Ваш вибір: ").strip()
        
        if choice == '1':
            files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
            files.sort()
            
            print("\nДоступні файли:")
            for idx, f_name in enumerate(files):
                marker = " <--- ПОТОЧНИЙ" if f_name == current_name else ""
                print(f"{idx + 1}. {f_name}{marker}")
            print(f"{len(files) + 1}. [СТВОРИТИ НОВИЙ ФАЙЛ]")
            print("0. Скасувати")
            
            sub_choice = input("Оберіть номер: ").strip()
            
            if sub_choice == '0':
                continue
                
            selected_file = None
            
            try:
                idx = int(sub_choice) - 1
                if 0 <= idx < len(files):
                    selected_file = files[idx]
                elif idx == len(files):
                    new_name = input("Введіть назву для нового файлу (без .json): ").strip()
                    if new_name:
                        if not new_name.endswith('.json'):
                            new_name += '.json'
                        selected_file = new_name
                        full_path = os.path.join(DATA_DIR, selected_file)
                        if not os.path.exists(full_path):
                            save_records_to_file([], full_path)
                    else:
                        print("Назва не може бути порожньою.")
            except ValueError:
                print("Некоректне введення.")
            
            if selected_file:
                save_records_to_file(current_records, current_filepath)
                
                new_full_path = os.path.join(DATA_DIR, selected_file)
                new_records = load_records_from_file(new_full_path)
                
                print(f"[Успіх] Переключено на файл: {selected_file}")
                return new_records, new_full_path
                
        elif choice == '0':
            return current_records, current_filepath
        else:
            print("Невірний вибір.")
