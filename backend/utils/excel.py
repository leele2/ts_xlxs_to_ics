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

def find_sunday_position(df):
    for row_idx in range(df.shape[0]):
        for col_idx in range(df.shape[1]):
            if str(df.iloc[row_idx, col_idx]).lower() == "sunday":
                return row_idx, col_idx
    return None, None

def extract_shift_details(shift_time):
    match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", shift_time)
    if not match:
        raise ValueError(f"Invalid shift format: {shift_time}")
    start_time_str, end_time_str = match.groups()
    time_format = "%H:%M"
    from datetime import datetime
    start_time = datetime.strptime(start_time_str, time_format)
    end_time = datetime.strptime(end_time_str, time_format)
    duration = (end_time - start_time).total_seconds() / 3600
    return start_time.strftime("%H:%M"), duration

def find_shifts(data_frames, name):
    results = []
    from .helpers import fix_date, is_date_in_past  # Import from helpers
    for sheet_title, df in data_frames.items():
        sunday_row, sunday_col = find_sunday_position(df)
        if sunday_row is None or sunday_col is None:
            continue
        shift_time_row = sunday_row + 1
        shift_col = sunday_col - 1
        date_row = sunday_row + 1
        date_col_start = sunday_col
        for col_idx in range(date_col_start, df.shape[1]):
            date = df.iloc[date_row, col_idx]
            for row_idx in range(shift_time_row, df.shape[0]):
                shift_time = df.iloc[row_idx, shift_col]
                if pd.notna(df.iloc[row_idx, col_idx]) and name.lower() in df.iloc[row_idx, col_idx].lower():
                    start_time, duration = extract_shift_details(shift_time)
                    fixed_date = fix_date(date)
                    if is_date_in_past(fixed_date):
                        continue
                    results.append({
                        "Sheet": sheet_title,
                        "Date": fixed_date,
                        "Shift Time": shift_time,
                        "Start Time": start_time,
                        "Duration": duration
                    })
    return results