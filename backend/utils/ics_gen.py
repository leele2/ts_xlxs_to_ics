from ics import Calendar, Event
import pytz
from datetime import datetime, timedelta
import hashlib
import uuid

def generate_uid(employee_name, shift_date):
    unique_string = f"{employee_name}{shift_date}"
    hash_val = hashlib.md5(unique_string.encode()).hexdigest()
    return str(uuid.UUID(hash_val[:32]))

def generate_ics(shifts, name_to_search):
    cal = Calendar()
    local_time_zone = pytz.timezone("Australia/Sydney")
    for shift in shifts:
        shift_date = datetime.strptime(shift["Date"], "%d/%m/%Y")
        start_time = datetime.strptime(shift["Start Time"], "%H:%M").time()
        start_dt = datetime.combine(shift_date, start_time)
        localized_start = local_time_zone.localize(start_dt)
        localized_end = localized_start + timedelta(hours=shift["Duration"])

        event_uid = generate_uid(shift_date, name_to_search.lower())

        event = Event()
        event.name = "shift [" + shift["Title"] + "]"
        event.begin = localized_start
        event.end = localized_end
        event.uid = event_uid
        cal.events.add(event)
    
    return cal.serialize()