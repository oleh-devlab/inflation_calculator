import os
import sys

from modules import InflationCalculator
from modules.config import DEFAULT_DATA_FOLDER_NAME, DEFAULT_INFLATION_RATES_FILENAME
from modules.ui import (
    add_record_loop,
    delete_record,
    show_processed_data,
    add_inflation_data_loop,
    settings_menu
)

# --- Path setup (consumer responsibility) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, DEFAULT_DATA_FOLDER_NAME)
INFLATION_RATES_FILEPATH = os.path.join(SCRIPT_DIR, DEFAULT_INFLATION_RATES_FILENAME)


def show_main_menu(warning_message: str | None, current_filename: str):
    print("\n-==== Inflation Impact Calculator ====-")
    print(f"    (Profile: {os.path.basename(current_filename)})")
    if warning_message:
        print(warning_message)
    print("------------------------------------------")
    print("1. Add new records")
    print("2. Delete records")
    print("3. Report")
    print("---")
    print("4. Inflation (database)")
    print("5. Settings / Change profile")
    print("0. Exit")
    print("------------------------------------------")

def main():
    default_filename = "default.json"
    default_records_filepath = os.path.join(DATA_DIR, default_filename)

    calc = InflationCalculator(
        records_filepath=default_records_filepath,
        inflation_rates_filepath=INFLATION_RATES_FILEPATH,
    )

    menu_warning = calc.check_data_gaps()

    while True:
        show_main_menu(menu_warning, calc.records_filepath)
        choice = input("Your choice: ").strip()

        if choice == '1':
            add_record_loop(calc)
        
        elif choice == '2':
            delete_record(calc)
            
        elif choice == '3':
            show_processed_data(calc)
            
        elif choice == '4':
            add_inflation_data_loop(calc)
            menu_warning = calc.check_data_gaps()

        elif choice == '5':
            calc = settings_menu(calc, DATA_DIR)
        
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")