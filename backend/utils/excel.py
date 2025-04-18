import pandas as pd
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MAX_DATE_ROWS = 5
EXCLUDED_PREFIXES = ["open", "close", "flex"]
DATE_ROW_OFFSET = 1  # Row offset for Primary DM (row below date row)

def format_part(part: str) -> str:
    """Format a date part (e.g., '23/3' -> '23/03')."""
    if len(part) > 2:
        return f"{int(part[0:2]):02d}/{int(part[2:]):02d}"
    elif len(part) == 2:
        return f"{int(part[0]):02d}/{int(part[1]):02d}"
    return f"{int(part[0]):02d}/02"

def fix_title(title: str) -> str:
    """Fix the title of a sheet by formatting date parts."""
    parts = title.split('-')
    part1 = format_part(parts[0])
    part2 = format_part(parts[1])
    return f"{part1}-{part2}"

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
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    if date_str == "APRIL FOOLS!":
        return f"01/04/{current_year}"

    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")

    parts = date_str.split()
    if len(parts) != 2:
        raise ValueError(f"Invalid date format: {date_str}. Expected format: 'DDst/nd/rd/th Month' or 'YYYY-MM-DD'")

    month_map = {
        "Jan": "01", "January": "01",
        "Feb": "02", "February": "02",
        "Mar": "03", "March": "03",
        "Apr": "04", "April": "04",
        "May": "05", "May": "05",
        "Jun": "06", "June": "06",
        "Jul": "07", "July": "07",
        "Aug": "08", "August": "08",
        "Sep": "09", "September": "09",
        "Oct": "10", "October": "10",
        "Nov": "11", "November": "11",
        "Dec": "12", "December": "12"
    }

    day = ''.join(filter(str.isdigit, parts[0]))
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
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
    current_date = datetime.today().date()
    return date_obj.date() < current_date

def extract_shift_details(shift_time: str) -> Tuple[Optional[str], Optional[float]]:
    """Extract start time and duration from a shift time string.

    Args:
        shift_time (str): Shift time, e.g., 'HH:MM-HH:MM' or 'Name (HH:MM-HH:MM)'.

    Returns:
        Tuple[Optional[str], Optional[float]]: Start time (HH:MM) and duration in hours, or (None, None) if invalid.
    """
    if not shift_time:
        logger.warning("Empty shift time provided")
        return None, None

    # Try to extract shift time from parentheses, e.g., "Bob (09:00-15:30)"
    parenthetical_match = re.match(r".*\((\d{1,2}:\d{2}-\d{1,2}:\d{2})\).*", shift_time.strip())
    if parenthetical_match:
        shift_time = parenthetical_match.group(1)

    # Match standard shift time format: HH:MM-HH:MM
    match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", shift_time)
    if not match:
        logger.warning(f"Invalid shift format: {shift_time}")
        return None, None

    start_time_str, end_time_str = match.groups()
    time_format = "%H:%M"
    try:
        start_time = datetime.strptime(start_time_str, time_format)
        end_time = datetime.strptime(end_time_str, time_format)
        duration = (end_time - start_time).total_seconds() / 3600
        # Handle overnight shifts (e.g., 23:00-01:00)
        if duration < 0:
            duration += 24
        return start_time.strftime("%H:%M"), duration
    except Exception as e:
        logger.warning(f"Error parsing shift time '{shift_time}': {e}")
        return None, None

def find_dates(df: pd.DataFrame) -> List[Tuple[int, int, str]]:
    """Find date positions in the DataFrame."""
    date_positions = []
    for row_idx in range(min(MAX_DATE_ROWS, df.shape[0])):
        for col_idx in range(df.shape[1]):
            value = df.iloc[row_idx, col_idx]
            fixed_date = is_date_like(value)
            if fixed_date:
                date_positions.append((row_idx, col_idx, value))
        if any(row == row_idx for row, _, _ in date_positions):
            break
    return date_positions

def group_dates_into_sections(date_positions: List[Tuple[int, int, str]]) -> List[List[Tuple[int, int, str]]]:
    """Group date positions into sections based on column proximity."""
    if not date_positions:
        return []
    date_sections = []
    current_section = []
    date_positions.sort(key=lambda x: x[1])
    last_col = date_positions[0][1]
    for date_row, date_col, date in date_positions:
        if date_col - last_col > 1:
            date_sections.append(current_section)
            current_section = []
        current_section.append((date_row, date_col, date))
        last_col = date_col
    if current_section:
        date_sections.append(current_section)
    return date_sections

def find_shift_times(df: pd.DataFrame, start_col: int) -> List[Tuple[int, int, str]]:
    """Find shift time positions in the specified columns."""
    shift_time_positions = []
    search_cols = range(max(0, start_col - 1), start_col + 1)
    for row_idx in range(df.shape[0]):
        for col_idx in search_cols:
            value = df.iloc[row_idx, col_idx]
            if is_shift_time_like(value):
                shift_time_positions.append((row_idx, col_idx, value))
    return shift_time_positions

def is_date_like(value: Union[str, float, int]) -> Optional[str]:
    """Check if a value is a date-like string and return the fixed date if valid."""
    if pd.isna(value):
        return None
    try:
        fixed_date = fix_date(value)
        return fixed_date
    except ValueError:
        return None

def is_shift_time_like(value: Union[str, float, int]) -> bool:
    """Check if a value is a shift time-like string."""
    if pd.isna(value):
        return False
    value_str = str(value).strip()
    if any(value_str.lower().startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return bool(re.match(r"^\d{1,2}:\d{2}-\d{1,2}:\d{2}$", value_str))

def find_shifts(data_frames: Dict[str, pd.DataFrame], names: Union[str, List[str]]) -> List[Dict]:
    """Find shifts for the specified names in the DataFrames.

    Args:
        data_frames (Dict[str, pd.DataFrame]): Dictionary of sheet titles to DataFrames.
        names (Union[str, List[str]]): Name(s) to search for.

    Returns:
        List[Dict]: List of shift dictionaries with keys 'Sheet', 'Date', 'Shift Time', 'Start Time', 'Duration', 'Name'.
    """
    if isinstance(names, str):
        names = [names]
    names = [name.lower() for name in names]
    results = []

    for sheet_title, df in data_frames.items():
        logger.info(f"Processing sheet: {sheet_title}")
        logger.info(f"DataFrame shape: {df.shape}")

        if df.empty:
            logger.warning("Skipping empty DataFrame")
            continue

        # Find dates
        date_positions = find_dates(df)
        logger.info(f"Dates found: {date_positions}")

        if not date_positions:
            logger.info("No dates found, skipping sheet")
            continue

        # Group dates into sections
        date_sections = group_dates_into_sections(date_positions)
        logger.info(f"Date sections: {date_sections}")

        for section in date_sections:
            if not section:
                continue

            start_col = section[0][1]

            # Find shift times
            shift_time_positions = find_shift_times(df, start_col)
            logger.info(f"Shift times for section {section}: {shift_time_positions}")

            if not shift_time_positions:
                logger.info("No shift times found, skipping section")
                continue

            for date_row, date_col, date in section:
                fixed_date = fix_date(date)
                logger.info(f"Checking date: {date} -> {fixed_date}")
                if is_date_in_past(fixed_date):
                    logger.info(f"Skipping past date: {fixed_date}")
                    continue

                # Check for Primary DM shift (row immediately below date row)
                primary_dm_row = date_row + DATE_ROW_OFFSET
                primary_dm_value = df.iloc[primary_dm_row, date_col] if primary_dm_row < df.shape[0] else None
                primary_dm_shift_time = None
                for shift_row, shift_col, shift_time in shift_time_positions:
                    if shift_row == primary_dm_row:
                        primary_dm_shift_time = shift_time
                        break

                # Check for embedded shift time in Primary DM cell
                embedded_shift_time = None
                if pd.notna(primary_dm_value):
                    if re.search(r"\(\d{1,2}:\d{2}-\d{1,2}:\d{2}\)", str(primary_dm_value)):
                        embedded_shift_time = primary_dm_value

                if pd.notna(primary_dm_value) and (primary_dm_shift_time or embedded_shift_time):
                    primary_dm_str = str(primary_dm_value).lower()
                    matching_names = [name for name in names if name in primary_dm_str]
                    for name in matching_names:
                        logger.info(f"Found Primary DM match for {name} at {date}")
                        # Prefer embedded shift time if present
                        shift_time_to_use = embedded_shift_time if embedded_shift_time else primary_dm_shift_time
                        start_time, duration = extract_shift_details(shift_time_to_use)
                        if start_time is not None and duration is not None:
                            results.append({
                                "Sheet": sheet_title,
                                "Date": fixed_date,
                                "Shift Time": shift_time_to_use,
                                "Start Time": start_time,
                                "Duration": duration,
                                "Name": name,
                                "Title": str(primary_dm_value)
                            })
                    if matching_names:
                        continue  # Skip other shifts if Primary DM is found

                # Check other shifts below the date row
                shift_found = set()  # Track names that have a shift on this date
                for shift_row, shift_col, shift_time in shift_time_positions:
                    if shift_row <= date_row:
                        continue
                    if all(name in shift_found for name in names):
                        break

                    cell_value = df.iloc[shift_row, date_col]
                    logger.info(f"Checking cell at row {shift_row}, col {date_col}: {cell_value}")
                    if pd.notna(cell_value):
                        cell_str = str(cell_value).lower()
                        matching_names = [name for name in names if name in cell_str and name not in shift_found]
                        for name in matching_names:
                            logger.info(f"Found match for {name} at {date}")
                            # Check for embedded shift time in cell, e.g., "Bob (09:00-15:30)"
                            shift_time_to_use = shift_time
                            if re.search(r"\(\d{1,2}:\d{2}-\d{1,2}:\d{2}\)", str(cell_value)):
                                shift_time_to_use = cell_value
                            start_time, duration = extract_shift_details(shift_time_to_use)
                            if start_time is None or duration is None:
                                continue
                            results.append({
                                "Sheet": sheet_title,
                                "Date": fixed_date,
                                "Shift Time": shift_time_to_use,
                                "Start Time": start_time,
                                "Duration": duration,
                                "Name": name,
                                "Title": str(cell_value)
                            })
                            shift_found.add(name)

    return results