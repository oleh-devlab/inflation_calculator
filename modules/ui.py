import os
import datetime
from decimal import Decimal

from .api import InflationCalculator
from .exceptions import (
    InvalidAmountError,
    InvalidDateError,
    RecordNotFoundError,
    StorageError,
    InvalidInflationRateError,
)


def print_records_list(calc: InflationCalculator, with_inflation: bool):
    records = calc.get_records()
    if not records:
        print("Records list is empty.")
        return
    
    print("-" * 50)
    q = Decimal('0.01') 
    
    for i, record in enumerate(records):
        comment_str = f" | {record.get('comment')}" if record.get('comment') else ""
        line = f"{i+1}. Amount: {record['amount']:.2f} UAH | Date: {record['date']}{comment_str}"
        if with_inflation:
            adjusted_val = calc.calculate_current_value(record['amount'], record['date'])
            loss_percent = Decimal(0)
            if adjusted_val > record['amount']:
                loss_percent = (1 - (record['amount'] / adjusted_val)) * 100
            
            line += f"\n   -> Today: {adjusted_val.quantize(q)} UAH | Loss: {loss_percent.quantize(q)}%"
        print(line)
    print("-" * 50)

def add_record_loop(calc: InflationCalculator):
    """Action 1: Adding records."""
    print(f"\n--- Adding new records (file: {os.path.basename(calc.records_filepath)}) ---")
    
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

        try:
            calc.add_record(amount, date_obj, comment)
            records_added_count += 1
            print(f"[Success] Added: {amount:.2f} UAH")
        except (InvalidAmountError, InvalidDateError, StorageError) as e:
            print(f"Error: {e}")

    if records_added_count == 0:
        print("Exiting without changes.")

def delete_record(calc: InflationCalculator):
    """Action 2: Deleting records."""
    print(f"\n--- Deleting records (file: {os.path.basename(calc.records_filepath)}) ---")
    
    if calc.records_count == 0:
        print("No records found.")
        return

    data_was_changed = False
    
    while True:
        print("\nCurrent records:")
        print_records_list(calc, with_inflation=False) 
        
        print(f"\nEnter number (1...{calc.records_count}), -1 (all), 0 (exit)")
        try:
            choice = int(input("Choice: "))
            if choice == 0: break
            
            if choice == -1:
                if input("Delete ALL? (yes/no): ").lower() == 'yes':
                    count = calc.delete_all_records()
                    data_was_changed = True
                    print(f"Cleared ({count} records deleted).")
                    break
            
            elif 1 <= choice <= calc.records_count:
                try:
                    removed = calc.delete_record(choice - 1)
                    data_was_changed = True
                    print(f"Deleted: {removed['amount']} UAH")
                    if calc.records_count == 0: break
                except RecordNotFoundError as e:
                    print(f"Error: {e}")
            else:
                print("Invalid number.")
        except ValueError:
            print("Enter an integer.")

    if data_was_changed:
        print("Changes saved.")

def show_processed_data(calc: InflationCalculator):
    """Action 3: Report."""
    filename = os.path.basename(calc.records_filepath)
    print(f"\n--- Data Analysis (Profile: {filename}) ---")
    
    report = calc.get_report()
    
    if not report["records"]:
        print("No data available.")
        return

    print(f"Total amount (nominal):         {report['total_nominal']} UAH")
    print(f"Oldest record:                  {report['oldest_date']}")
    print(f"Real value today:               {report['total_adjusted']} UAH")
    print(f"Purchasing power loss:           {report['loss_percent']}%")
    
    print("\nDetails:")
    print_records_list(calc, with_inflation=True)

def add_inflation_data_loop(calc: InflationCalculator):
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
    
    rates = calc.get_inflation_rates()
    
    while True:
        current_key = current_date.strftime("%Y-%m") 
        existing = f" (current: {rates[current_key]*100}) " if current_key in rates else ""
        
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
                
            calc.set_inflation_rate(current_key, rate_decimal)
            rates = calc.get_inflation_rates()  # refresh local copy
            added_count += 1
            
            # Next month
            year, month = current_date.year, current_date.month
            month += 1
            if month > 12: month, year = 1, year + 1
            current_date = datetime.date(year, month, 1)

        except InvalidInflationRateError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")

    if added_count > 0:
        print("Data saved.")

def settings_menu(calc: InflationCalculator, data_dir: str):
    """
    Action 5: Settings and file selection.
    Returns a new InflationCalculator if the profile was changed,
    or the same one if not.
    """
    while True:
        current_name = os.path.basename(calc.records_filepath)
        print(f"\n--- Settings (Current file: {current_name}) ---")
        print("1. Change/Create records file")
        print("0. Back to main menu")
        
        choice = input("Your choice: ").strip()
        
        if choice == '1':
            files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
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
                    else:
                        print("Name cannot be empty.")
            except ValueError:
                print("Invalid input.")
            
            if selected_file:
                # Save current records before switching
                try:
                    calc.save()
                except StorageError as e:
                    print(f"Warning: Could not save current data: {e}")
                
                new_filepath = os.path.join(data_dir, selected_file)
                new_calc = InflationCalculator(
                    records_filepath=new_filepath,
                    inflation_rates_filepath=calc.inflation_rates_filepath,
                )
                
                print(f"[Success] Switched to file: {selected_file}")
                return new_calc
                
        elif choice == '0':
            return calc
        else:
            print("Invalid choice.")
