import os
import sys

from modules.config import DATA_DIR, INFLATION_RATES_FILENAME
from modules.storage import load_records_from_file, load_inflation_rates_from_file
from modules.logic import check_inflation_data_gaps
from modules.ui import (
    add_record_loop,
    delete_record,
    show_processed_data,
    add_inflation_data_loop,
    settings_menu
)

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
    current_records_filepath = os.path.join(DATA_DIR, default_filename)
    
    records_storage = load_records_from_file(current_records_filepath)
    inflation_rates_storage = load_inflation_rates_from_file(INFLATION_RATES_FILENAME)

    menu_warning = check_inflation_data_gaps(inflation_rates_storage)

    while True:
        show_main_menu(menu_warning, current_records_filepath)
        choice = input("Your choice: ").strip()

        if choice == '1':
            add_record_loop(records_storage, current_records_filepath)
        
        elif choice == '2':
            delete_record(records_storage, current_records_filepath)
            
        elif choice == '3':
            show_processed_data(records_storage, inflation_rates_storage, current_records_filepath)
            
        elif choice == '4':
            add_inflation_data_loop(inflation_rates_storage)
            menu_warning = check_inflation_data_gaps(inflation_rates_storage)

        elif choice == '5':
            records_storage, current_records_filepath = settings_menu(records_storage, current_records_filepath)
        
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