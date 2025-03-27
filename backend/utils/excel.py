import pandas as pd
import re

def format_part(part):
    if len(part) > 2:
        return str(int(part[0:2])) + '/' + str(int(part[2:]))
    elif len(part) == 2:
        return str(int(part[0])) + '/' + str(int(part[1]))
    return str(int(part[0])) + '/' + '2'

def fix_title(title):
    parts = title.split('-')
    part1 = format_part(parts[0])
    part2 = format_part(parts[1])
    return part1 + '-' + part2

def read_xls(xls_path):
    with pd.ExcelFile(xls_path) as xls:
        data_frames = {}
        for sheet in xls.sheet_names:
            sheet_obj = xls.book[sheet]
            if sheet_obj.sheet_state == "visible":
                try:
                    data_frames[fix_title(sheet_obj.title)] = pd.read_excel(
                        xls, sheet_name=sheet, header=None, index_col=None
                    )
                except Exception as e:
                    print(f"Error reading sheet {sheet_obj.title}: {e}")
    return data_frames

from datetime import datetime
from .helpers import fix_date, is_date_in_past

def find_shifts(data_frames, name):
    results = []

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

    def is_date_in_past(date_str: str) -> bool:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        current_date = datetime.today().date()
        return date_obj.date() < current_date

    def is_date_like(value):
        if pd.isna(value):
            return False
        try:
            fix_date(value)
            return True
        except ValueError:
            return False

    def is_shift_time_like(value):
        if pd.isna(value):
            return False
        value_str = str(value).strip()
        # Exclude labels like "Open", "Close", etc.
        if any(value_str.lower().startswith(prefix) for prefix in ["open", "close", "primary", "flex"]):
            return False
        return bool(re.match(r"^\d{1,2}:\d{2}-\d{1,2}:\d{2}$", value_str))

    def extract_shift_details(shift_time):
        match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", shift_time)
        if not match:
            raise ValueError(f"Invalid shift format: {shift_time}")
        start_time_str, end_time_str = match.groups()
        time_format = "%H:%M"
        start_time = datetime.strptime(start_time_str, time_format)
        end_time = datetime.strptime(end_time_str, time_format)
        duration = (end_time - start_time).total_seconds() / 3600
        return start_time.strftime("%H:%M"), duration

    for sheet_title, df in data_frames.items():
        print(f"Processing sheet: {sheet_title}")
        print(f"DataFrame shape: {df.shape}")

        date_positions = []
        for row_idx in range(min(5, df.shape[0])):
            for col_idx in range(df.shape[1]):
                value = df.iloc[row_idx, col_idx]
                if is_date_like(value):
                    date_positions.append((row_idx, col_idx, value))
        print(f"Dates found: {date_positions}")

        if not date_positions:
            print("No dates found, skipping sheet")
            continue

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
        print(f"Date sections: {date_sections}")

        for section in date_sections:
            if not section:
                continue

            start_col = section[0][1]
            end_col = section[-1][1]
            shift_time_positions = []
            search_cols = range(max(0, start_col - 1), start_col + 1)
            for row_idx in range(df.shape[0]):
                for col_idx in search_cols:
                    value = df.iloc[row_idx, col_idx]
                    if is_shift_time_like(value):
                        shift_time_positions.append((row_idx, col_idx, value))
            print(f"Shift times for section {section}: {shift_time_positions}")

            if not shift_time_positions:
                print("No shift times found, skipping section")
                continue

            for date_row, date_col, date in section:
                fixed_date = fix_date(date)
                print(f"Checking date: {date} -> {fixed_date}")
                if is_date_in_past(fixed_date):
                    print(f"Skipping past date: {fixed_date}")
                    continue

                shift_found = False
                for shift_row, shift_col, shift_time in shift_time_positions:
                    if shift_row <= date_row:
                        continue
                    if shift_found:
                        break

                    cell_value = df.iloc[shift_row, date_col]
                    print(f"Checking cell at row {shift_row}, col {date_col}: {cell_value}")
                    if pd.notna(cell_value):
                        cell_str = str(cell_value)
                        if name.lower() in cell_str.lower():
                            print(f"Found match for {name} at {date}, shift time {shift_time}")
                            start_time, duration = extract_shift_details(shift_time)
                            if start_time is None or duration is None:
                                continue
                            results.append({
                                "Sheet": sheet_title,
                                "Date": fixed_date,
                                "Shift Time": shift_time,
                                "Start Time": start_time,
                                "Duration": duration
                            })
                            shift_found = True

    return results