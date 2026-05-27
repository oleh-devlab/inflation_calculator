import os
import datetime
from decimal import Decimal

from .logic import get_current_value
from .storage import save_records_to_file, save_inflation_rates_to_file, load_records_from_file
from .config import DATA_DIR, INFLATION_RATES_FILENAME

def print_records_list(records: list, with_inflation: bool, inflation_rates: dict):
    if not records:
        print("Records list is empty.")
        return
    
    print("-" * 50)
    q = Decimal('0.01') 
    
    for i, record in enumerate(records):
        comment_str = f" | {record.get('comment')}" if record.get('comment') else ""
        line = f"{i+1}. Amount: {record['amount']:.2f} UAH | Date: {record['date']}{comment_str}"
        if with_inflation:
            adjusted_val = get_current_value(record['amount'], record['date'], inflation_rates)
            loss_percent = Decimal(0)
            if adjusted_val > record['amount']:
                loss_percent = (1 - (record['amount'] / adjusted_val)) * 100
            
            line += f"\n   -> Today: {adjusted_val.quantize(q)} UAH | Loss: {loss_percent.quantize(q)}%"
        print(line)
    print("-" * 50)

def add_record_loop(records: list, current_filename_path: str):
    """Action 1: Adding records."""
    print(f"\n--- Adding new records (file: {os.path.basename(current_filename_path)}) ---")
    
    records_added_count = 0
    
    while True:
        while True:
            try:
                amount_str = input("\nEnter amount (or 0 to exit): ")
                if amount_str.strip() == '0':
                    break
                amount = Decimal(amount_str).quantize(Decimal('0.01'))
                if amount <= 0:
                    print("Amount must be positive.")
                    continue
                break
            except Exception as e:
                print(f"Input error: {e}")
        
        if amount_str.strip() == '0':
            break

        print(f"Hint: format YYYY-MM-DD (e.g. {datetime.date.today()})")
        while True:
            try:
                date_str = input("Enter the date received: ")
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj > datetime.date.today():
                    print("Date cannot be in the future.")
                    continue
                break
            except ValueError:
                print("Invalid format. Use YYYY-MM-DD.")

        comment = input("Comment (or 0 to skip): ").strip()
        if comment == '0': comment = ""

        records.append({'amount': amount, 'date': date_obj, 'comment': comment})
        records_added_count += 1
        print(f"[Success] Added: {amount:.2f} UAH")

    if records_added_count > 0:
        print(f"Saving data to {os.path.basename(current_filename_path)}...")
        save_records_to_file(records, current_filename_path)
    else:
        print("Exiting without changes.")

def delete_record(records: list, current_filename_path: str):
    """Action 2: Deleting records."""
    print(f"\n--- Deleting records (file: {os.path.basename(current_filename_path)}) ---")
    
    if not records:
        print("No records found.")
        return

    data_was_changed = False
    
    while True:
        print("\nCurrent records:")
        print_records_list(records, with_inflation=False, inflation_rates={}) 
        
        print("\nEnter number (1...N), -1 (all), 0 (exit)")
        try:
            choice = int(input("Choice: "))
            if choice == 0: break
            
            if choice == -1:
                if input("Delete ALL? (yes/no): ").lower() == 'yes':
                    records.clear()
                    data_was_changed = True
                    print("Cleared.")
                    break
            
            elif 1 <= choice <= len(records):
                rem = records.pop(choice - 1)
                data_was_changed = True
                print(f"Deleted: {rem['amount']} UAH")
                if not records: break
            else:
                print("Invalid number.")
        except ValueError:
            print("Enter an integer.")

    if data_was_changed:
        save_records_to_file(records, current_filename_path)
        print("Changes saved.")

def show_processed_data(records: list, inflation_rates: dict, current_filename_path: str):
    """Action 3: Report."""
    filename = os.path.basename(current_filename_path)
    print(f"\n--- Data Analysis (Profile: {filename}) ---")
    
    if not records:
        print("No data available.")
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
    
    print(f"Total amount (nominal):         {total_raw} UAH")
    print(f"Oldest record:                  {oldest_date}")
    print(f"Real value today:               {total_adjusted} UAH")
    print(f"Purchasing power loss:           {total_loss_percent.quantize(q)}%")
    
    print("\nDetails:")
    print_records_list(records, with_inflation=True, inflation_rates=inflation_rates)

def add_inflation_data_loop(inflation_rates: dict):
    """Action 4: Entering inflation data."""
    print("\n--- Enter Inflation Data ---")
    print("Example: for 1.4% inflation enter '101.4'")
    
    while True:
        try:
            d_str = input("Year-Month (YYYY-MM): ")
            start_date = datetime.datetime.strptime(d_str, "%Y-%m").date()
            break
        except ValueError:
            print("Format: YYYY-MM.")
            
    current_date = start_date
    added_count = 0
    
    while True:
        current_key = current_date.strftime("%Y-%m") 
        existing = f" (current: {inflation_rates[current_key]*100}) " if current_key in inflation_rates else ""
        
        rate_str = input(f"Inflation for {current_key}{existing} (0 to exit): ").strip()
        if rate_str == '0': break
        
        try:
            rate_decimal = Decimal(rate_str)
            if rate_decimal <= 0:
                print("Number must be > 0.")
                continue

            if rate_decimal < 80:
                print(f"[!] WARNING: You entered {rate_decimal}.")
                print(f"    This means prices FELL and money depreciated to {rate_decimal}% of nominal value.")
                print(f"    If inflation was {rate_decimal}%, you should have entered {100 + rate_decimal}.")
                confirm = input("    Are you sure you want to save this value? (yes/no): ").lower()
                if confirm != 'yes':
                    continue
                
            inflation_rates[current_key] = rate_decimal / Decimal('100')
            added_count += 1
            
            # Next month
            year, month = current_date.year, current_date.month
            month += 1
            if month > 12: month, year = 1, year + 1
            current_date = datetime.date(year, month, 1)

        except Exception as e:
            print(f"Error: {e}")

    if added_count > 0:
        save_inflation_rates_to_file(inflation_rates, INFLATION_RATES_FILENAME)
        print("Data saved.")

def settings_menu(current_records: list, current_filepath: str):
    """
    Action 5: Settings and file selection.
    Returns (new_records_list, new_filepath).
    """
    while True:
        current_name = os.path.basename(current_filepath)
        print(f"\n--- Settings (Current file: {current_name}) ---")
        print("1. Change/Create records file")
        print("0. Back to main menu")
        
        choice = input("Your choice: ").strip()
        
        if choice == '1':
            files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
            files.sort()
            
            print("\nAvailable files:")
            for idx, f_name in enumerate(files):
                marker = " <--- CURRENT" if f_name == current_name else ""
                print(f"{idx + 1}. {f_name}{marker}")
            print(f"{len(files) + 1}. [CREATE NEW FILE]")
            print("0. Cancel")
            
            sub_choice = input("Select number: ").strip()
            
            if sub_choice == '0':
                continue
                
            selected_file = None
            
            try:
                idx = int(sub_choice) - 1
                if 0 <= idx < len(files):
                    selected_file = files[idx]
                elif idx == len(files):
                    new_name = input("Enter name for the new file (without .json): ").strip()
                    if new_name:
                        if not new_name.endswith('.json'):
                            new_name += '.json'
                        selected_file = new_name
                        full_path = os.path.join(DATA_DIR, selected_file)
                        if not os.path.exists(full_path):
                            save_records_to_file([], full_path)
                    else:
                        print("Name cannot be empty.")
            except ValueError:
                print("Invalid input.")
            
            if selected_file:
                save_records_to_file(current_records, current_filepath)
                
                new_full_path = os.path.join(DATA_DIR, selected_file)
                new_records = load_records_from_file(new_full_path)
                
                print(f"[Success] Switched to file: {selected_file}")
                return new_records, new_full_path
                
        elif choice == '0':
            return current_records, current_filepath
        else:
            print("Invalid choice.")
