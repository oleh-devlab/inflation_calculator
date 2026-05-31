# inflation_calculator
![AI Generated](https://img.shields.io/badge/AI%20Generated-95%25-blueviolet)

This project is an inflation calculator that calculates the inflation rate between two dates.

## Features

- **Inflation-adjusted value calculation** — computes today's value of a past amount using monthly CPI data
- **Multiple profiles** — manage separate record sets via JSON-based profiles in `data_records/`
- **Inflation data import** — bulk-import monthly rates from raw text with the `import_local_data.py` script
- **Gap detection** — warns about missing months in the inflation database and falls back to an 8 % annual rate
- **Interactive CLI menu** — add / delete records, view reports, manage inflation data, and switch profiles
- **No external dependencies** — runs on the Python standard library only

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/oleh-devlab/inflation_calculator.git
   cd inflation_calculator
   ```

2. **Verify Python version**

   Python 3.10+ is required (the project uses `match` / `|` union-type syntax).

   ```bash
   python --version
   ```

3. **Install dependencies**

   The project has no external dependencies; all modules are from the Python standard library.

## Usage

### Running the application

```bash
python main.py
```

The interactive menu allows you to:

| Key | Action |
|-----|--------|
| `1` | Add new records |
| `2` | Delete records |
| `3` | Generate a report |
| `4` | Manage the inflation database |
| `5` | Settings / Change profile |
| `0` | Exit |

### Importing inflation data

Use the helper script to bulk-import monthly CPI rates from a text file or pasted data:

```bash
python scripts/import_local_data.py
```

### Running tests

```bash
python -m pytest tests/
```

## Project Structure

```
inflation_calculator/
├── main.py                        # Application entry point (CLI menu)
├── inflation_rates.json           # Monthly inflation rates database
├── inflation_rates.json.example   # Example data file
├── requirements.txt               # Dependencies (none)
├── modules/
│   ├── __init__.py
│   ├── config.py                  # Paths, constants, Decimal precision
│   ├── logic.py                   # Core calculations & gap detection
│   ├── storage.py                 # JSON read / write helpers
│   └── ui.py                      # Interactive CLI
├── scripts/
│   └── import_local_data.py       # Bulk CPI data importer
├── tests/
│   ├── __init__.py
│   └── test_import_local_data.py  # Unit tests for the importer
└── data_records/
    └── default.json               # Default user profile
```

## Details and Comments

### Interface and Language
The application interface and code are written in English. It uses the Ukrainian hryvnia (UAH) as its default currency.

### Data Source
Currently, data for each month is retrieved either via the import_local_data.py script or the main.py submenu. Plans are in place to provide access to an API or to allow the download of a ready-made JSON file containing all the data. The repository includes an example covering several months, based on [the Ministry of Finance website](https://index.minfin.com.ua/ua/economy/index/inflation/).

## About the development process

This project was created as an experiment in AI-assisted development (rapid prototyping).
Over 95% of the code was written by artificial intelligence (LLM). The code was generated and reviewed with a focus on functionality rather than production-level architecture.
