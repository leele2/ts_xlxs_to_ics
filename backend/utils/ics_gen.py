from ics import Calendar, Event
import pytz
from datetime import datetime, timedelta
import hashlib
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def generate_uid(shift_date, employee_name):
    raw = f"{employee_name.lower()}_{shift_date}"
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return f"shift_{hash_val[:24]}"  # 24 characters = safe, unique, and valid

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

def upsert_shift(service, calendar_id, shift):
    local_tz = pytz.timezone("Australia/Sydney")

    # Parse shift details
    shift_date = datetime.strptime(shift["Date"], "%d/%m/%Y")
    shift_start_time = datetime.strptime(shift["Start Time"], "%H:%M").time()
    shift_start = local_tz.localize(datetime.combine(shift_date, shift_start_time))
    shift_end = shift_start + timedelta(hours=shift["Duration"])
    shift_summary = f"Shift - [{shift['Title']}]"

    # Define time range for the day
    day_start = local_tz.localize(datetime.combine(shift_date, datetime.min.time()))
    day_end = local_tz.localize(datetime.combine(shift_date, datetime.max.time()))

    # List events on that day
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=day_start.isoformat(),
            timeMax=day_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    # Check if any event has the same title
    existing_event = None
    for event in events_result.get("items", []):
        if event.get("summary") == shift_summary:
            existing_event = event
            break

    event_data = {
        "summary": shift_summary,
        "start": {
            "dateTime": shift_start.isoformat(),
            "timeZone": "Australia/Sydney",
        },
        "end": {
            "dateTime": shift_end.isoformat(),
            "timeZone": "Australia/Sydney",
        },
    }

    # Update or insert
    if existing_event:
        print(f"Updating shift on {shift['Date']}: {shift_summary}")
        service.events().update(
            calendarId=calendar_id, eventId=existing_event["id"], body=event_data
        ).execute()
    else:
        print(f"Creating shift on {shift['Date']}: {shift_summary}")
        service.events().insert(calendarId=calendar_id, body=event_data).execute()

def sync_gmail(shifts, name_to_search, data, logger):
    try:
        credentials = Credentials(token=data.google_token)
        service = build("calendar", "v3", credentials=credentials)
        # local_time_zone = pytz.timezone("Australia/Sydney")

        for shift in shifts:
            upsert_shift(service, "primary", shift)
            # shift_date = datetime.strptime(shift["Date"], "%d/%m/%Y")
            # start_time = datetime.strptime(shift["Start Time"], "%H:%M").time()
            # start_dt = datetime.combine(shift_date, start_time)
            # localized_start = local_time_zone.localize(start_dt)
            # localized_end = localized_start + timedelta(hours=shift["Duration"])
            # event = {
            #     "summary": f"Shift - [{shift['Title']}]",
            #     "start": {
            #         "dateTime": localized_start.isoformat(),
            #         "timeZone": "Australia/Sydney",
            #     },
            #     "end": {
            #         "dateTime": localized_end.isoformat(),
            #         "timeZone": "Australia/Sydney",
            #     },
            # }

            # service.events().insert(calendarId="primary", body=event).execute()

        logger.info("Events added to Google Calendar.")
    except Exception as e:
        logger.error(f"Google Calendar sync failed: {str(e)}")
