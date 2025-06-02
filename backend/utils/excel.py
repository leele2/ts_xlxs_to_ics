import pandas as pd
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
EXCLUDED_PREFIXES = ["open", "close", "flex", "dm support"]
SPECIAL_DATES = {
    "APRIL FOOLS!": (1, 4),  # 1st April
    "XMAS EVE": (24, 12),  # 24th December
    "NEW YEARS DAY": (1, 1),  # 1st January
    # Add more as needed
}


def fix_title(title: str) -> str:
    """Fix the title of a sheet by formatting date parts."""
    return title


def read_xls(xls_path: str) -> Dict[str, pd.DataFrame]:
    """Read visible sheets from an Excel file into DataFrames."""
    data_frames = {}
    with pd.ExcelFile(xls_path) as xls:
        for sheet in xls.sheet_names:
            sheet_obj = xls.book[sheet]
            if sheet_obj.sheet_state != "visible":
                continue
            try:
                df = pd.read_excel(xls, sheet_name=sheet, header=None, index_col=None)
                if df.empty:
                    logger.warning(f"Skipping empty sheet: {sheet_obj.title}")
                    continue
                data_frames[fix_title(sheet_obj.title)] = df
            except Exception as e:
                logger.error(f"Error reading sheet {sheet_obj.title}: {e}")
    return data_frames


def fix_date(date_str: str) -> str:
    """Convert a date string to 'DD/MM/YYYY' format, handling special cases."""
    if isinstance(date_str, datetime):
        if date_str.date() == datetime.min.date():
            raise ValueError("Time value without date detected.")
        return date_str.strftime("%d/%m/%Y")
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    date_str_upper = str(date_str).strip().upper()
    if date_str_upper in SPECIAL_DATES:
        day, month = SPECIAL_DATES[date_str_upper]
        return f"{str(day).zfill(2)}/{str(month).zfill(2)}/{current_year}"

    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")

    parts = date_str.split()
    if len(parts) != 2:
        raise ValueError(
            f"Invalid date format: {date_str}. Expected format: 'DDst/nd/rd/th Month' or 'YYYY-MM-DD'"
        )

    month_map = {
        "Jan": "01",
        "January": "01",
        "Feb": "02",
        "February": "02",
        "Mar": "03",
        "March": "03",
        "Apr": "04",
        "April": "04",
        "May": "05",
        "May": "05",
        "Jun": "06",
        "June": "06",
        "Jul": "07",
        "July": "07",
        "Aug": "08",
        "August": "08",
        "Sep": "09",
        "September": "09",
        "Oct": "10",
        "October": "10",
        "Nov": "11",
        "November": "11",
        "Dec": "12",
        "December": "12",
    }

    day = "".join(filter(str.isdigit, parts[0]))
    if not day:
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


def is_date_in_past(date_str: str) -> bool:
    """Check if a date is in the past."""
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        return date_obj <= datetime.today().date()
    except ValueError:
        # Handle incorrectly formatted dates gracefully
        logger.warning(f"Invalid date format: {date_str}")
        return True


def extract_shift_details(shift_time: str) -> Tuple[Optional[str], Optional[float]]:
    """Extract start time and duration from a shift time string, handling prefixes and parentheses.

    Args:
        shift_time (str): Shift time, e.g., 'HH:MM-HH:MM', 'Open 09:00-17:00', or 'Bob (09:00-15:30)'.

    Returns:
        Tuple[Optional[str], Optional[float]]: Start time and duration in hours, or (None, None) if invalid.
    """
    if not shift_time:
        logger.warning("Empty shift time provided")
        return None, None

    shift_time = shift_time.strip().lower()

    # Remove known prefixes (e.g., "open", "close", etc.)
    for prefix in EXCLUDED_PREFIXES:
        if shift_time.startswith(prefix.lower()):
            shift_time = shift_time[len(prefix) :].strip()

    # Match standard shift time format: HH:MM-HH:MM
    match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", shift_time)
    if not match:
        return None, None

    start_time_str, end_time_str = match.groups()
    try:
        time_format = "%H:%M"
        start_time = datetime.strptime(start_time_str, time_format)
        end_time = datetime.strptime(end_time_str, time_format)
        duration = (end_time - start_time).total_seconds() / 3600
        if duration < 0:
            duration += 24  # Handle overnight shifts
        return start_time.strftime("%H:%M"), duration
    except Exception as e:
        logger.warning(f"Error parsing shift time '{shift_time}': {e}")
        return None, None


def is_date_like(value: Union[str, float, int]) -> Optional[str]:
    """Check if a value is a date-like string and return the fixed date if valid."""
    if pd.isna(value):
        return None
    value_str = str(value).strip()
    # Ignore pure time strings like "10:00:00"
    if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", value_str):
        return None

    try:
        fixed_date = fix_date(value_str)
        return fixed_date
    except ValueError:
        return None


def is_shift_time_like(value: Union[str, float, int]) -> bool:
    """Check if a value is a shift time-like string, even if it has a prefix like 'Open'."""
    if pd.isna(value):
        return False

    value_str = str(value).strip().lower()

    # Remove known prefixes if present
    for prefix in EXCLUDED_PREFIXES:
        if value_str.startswith(prefix.lower()):
            value_str = value_str[len(prefix) :].strip()

    return bool(re.match(r"^\d{1,2}:\d{2}-\d{1,2}:\d{2}$", value_str))


def search_name_and_extract_shift(
    df: pd.DataFrame, name: str, grid_size: int = 30
) -> List[Dict[str, Union[str, float]]]:
    """Search for a name in a grid and extract the corresponding date and shift time."""
    name = name.lower()
    results = []

    rows, cols = df.shape
    for r in range(min(rows, grid_size)):
        for c in range(min(cols, grid_size)):
            cell = df.iat[r, c]
            if pd.isna(cell):
                continue
            if name in str(cell).lower():
                logger.info(f"Found name '{name}' at ({r}, {c}) - cell {cell}")

                # Search upwards for a date
                found_date = None
                for ur in range(r - 1, -1, -1):
                    date_candidate = df.iat[ur, c]
                    if is_date_like(date_candidate):
                        found_date = fix_date(date_candidate)
                        break

                found_shift = None
                start_time = None
                duration = None
                # Try extracting from parentheses in the same cell
                match = re.search(r"\((\d{1,2}:\d{2}-\d{1,2}:\d{2})\)", str(cell))
                if match:
                    shift_str = match.group(1)
                    found_shift = shift_str
                    start_time, duration = extract_shift_details(shift_str)
                else:
                    # Scan leftward for a shift time
                    for lc in range(c - 1, -1, -1):
                        shift_candidate = df.iat[r, lc]
                        start_time, duration = extract_shift_details(
                            str(shift_candidate)
                        )
                        if start_time and duration is not None:
                            found_shift = str(shift_candidate)
                            break

                if found_date and start_time and duration is not None:
                    if not is_date_in_past(found_date):
                        results.append(
                            {
                                "Date": found_date,
                                "Shift Time": found_shift,
                                "Start Time": start_time,
                                "Duration": duration,
                                "Name": name,
                                "Title": str(cell),
                            }
                        )
                else:
                    logger.warning(
                        f"Missing date or valid shift for name '{name}' at ({r}, {c})"
                    )

    return results


def find_shifts(
    data_frames: Dict[str, pd.DataFrame], names: Union[str, List[str]]
) -> List[Dict]:
    if isinstance(names, str):
        names = [names]

    results = []
    for sheet_title, df in data_frames.items():
        logger.info(f"Searching in sheet: {sheet_title}")
        for name in names:
            results.extend(
                [
                    {**res, "Sheet": sheet_title, "Name": name}
                    for res in search_name_and_extract_shift(df, name)
                ]
            )
    results.sort(key=lambda s: datetime.strptime(s["Date"], "%d/%m/%Y"))
    return results
