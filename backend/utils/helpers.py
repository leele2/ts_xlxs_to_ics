from datetime import datetime

def is_date_in_past(date_str: str) -> bool:
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
    current_date = datetime.today().date()
    return date_obj.date() < current_date

def fix_date(date_str: str):
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    # Handle special cases
    if date_str == "APRIL FOOLS!":
        return f"01/04/{current_year}"

    # Split the string and validate the format
    parts = date_str.split()
    if len(parts) != 2:
        raise ValueError(f"Invalid date format: {date_str}. Expected format: 'DDst/nd/rd/th Month'")

    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
        "March": "03", "April": "04"
    }

    day = ''.join(filter(str.isdigit, parts[0]))
    if not day:  # Ensure day is not empty after filtering
        raise ValueError(f"Invalid day in date: {date_str}")

    month_name = parts[1]
    if month_name not in month_map:
        raise ValueError(f"Invalid month name in date: {date_str}")

    month_number = month_map[month_name]

    if current_month in [1, 2, 3] and month_number == "12":
        year = current_year - 1
    elif current_month in [10, 11, 12] and month_number == "01":
        year = current_year + 1
    else:
        year = current_year

    return f"{day.zfill(2)}/{month_number}/{year}"