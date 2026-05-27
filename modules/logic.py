import datetime
from decimal import Decimal
from .config import FALLBACK_ANNUAL_INFLATION_RATE

def check_inflation_data_gaps(rates: dict) -> str | None:
    """
    Перевіряє дані інфляції на пропущені місяці ("дірки").
    """
    if not rates:
        return "  [!] Увага: База даних інфляції порожня. (Використовується 8% річних)"

    all_keys = sorted(rates.keys())
    oldest_key_date = datetime.date.fromisoformat(all_keys[0] + "-01")
    
    today = datetime.date.today()
    first_of_this_month = today.replace(day=1)
    last_of_last_month = first_of_this_month - datetime.timedelta(days=1)
    
    missing_months = []
    
    loop_date = oldest_key_date
    while loop_date <= last_of_last_month:
        key = loop_date.strftime("%Y-%m")
        if key not in rates:
            missing_months.append(key)
        
        # Наступний місяць
        year, month = loop_date.year, loop_date.month
        month += 1
        if month > 12:
            month = 1
            year += 1
        loop_date = datetime.date(year, month, 1)

    if missing_months:
        if len(missing_months) > 7:
            return (f"  [!] Увага: Пропущено {len(missing_months)} міс. інфляції (починаючи з {missing_months[0]})\n"
                   f"      У розрахунках ці місяці будуть враховані як 0% інфляції!")
        else:
            return (f"  [!] Увага: Пропущено дані інфляції за: {', '.join(missing_months)}.\n"
                   f"      У розрахунках ці місяці будуть враховані як 0% інфляції!")
            
    return None

def get_current_value(amount: Decimal, date: datetime.date, inflation_rates: dict) -> Decimal:
    """Розраховує сьогоднішню вартість суми."""
    today = datetime.date.today()
    if date >= today:
        return amount

    # Випадок 1: Стара формула
    if not inflation_rates:
        days_diff = (today - date).days
        years_diff = Decimal(days_diff) / Decimal('365.25')
        multiplier = (Decimal(1) + FALLBACK_ANNUAL_INFLATION_RATE) ** years_diff
        return amount * multiplier

    current_amount = amount
    current_calc_date = date

    # Випадок 2: Гібридний розрахунок
    oldest_rate_key = min(inflation_rates.keys())
    oldest_known_date = datetime.date.fromisoformat(oldest_rate_key + "-01")

    if current_calc_date < oldest_known_date:
        days_diff = (oldest_known_date - current_calc_date).days
        years_diff = Decimal(days_diff) / Decimal('365.25')
        fallback_multiplier = (Decimal(1) + FALLBACK_ANNUAL_INFLATION_RATE) ** years_diff
        current_amount = current_amount * fallback_multiplier
        current_calc_date = oldest_known_date

    loop_date = datetime.date(current_calc_date.year, current_calc_date.month, 1)
    today_key = today.strftime("%Y-%m")

    while loop_date < today:
        loop_key = loop_date.strftime("%Y-%m")
        if loop_key == today_key:
            break
            
        if loop_key in inflation_rates:
            current_amount = current_amount * inflation_rates[loop_key]
        
        # Наступний місяць
        year, month = loop_date.year, loop_date.month
        month += 1
        if month > 12:
            month = 1
            year += 1
        loop_date = datetime.date(year, month, 1)

    return current_amount
