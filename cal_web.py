from icalendar import Calendar, Event
import pytz
from datetime import datetime, timedelta
import re
import io
import zipfile

def create_ics_file(event_details, start_date, end_date):
    cal = Calendar()
    event = Event()
    event.add('summary', event_details['title'])
    event.add('description', event_details['description'])
    event.add('location', event_details['location'])
    event.add('dtstart', event_details['start_datetime'])
    event.add('dtend', event_details['end_datetime'])
    event.add('rrule', {'freq': 'weekly', 'until': end_date, 'byday': event_details['day'][:2].upper()})
    cal.add_component(event)

    
    return cal.to_ical()

def parse_input(input_text):
    schedule = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    current_day = None
    lines = input_text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line in days:
            current_day = line
            schedule[current_day] = []
        elif current_day and line:
            # Assuming the next 4 lines are title, description, location, and time
            if i + 3 < len(lines):
                title = line
                description = lines[i + 1].strip()
                location = lines[i + 2].strip()
                time = lines[i + 3].strip()
                schedule[current_day].append({
                    'title': title,
                    'description': description,
                    'location': location,
                    'time': time
                })
                i += 3  # Skip the next 3 lines as they are part of the current event
        i += 1

    return schedule




def parse_and_create_ics_files(schedule, start_date, end_date):
    time_zone = pytz.timezone("America/Chicago")
    ical_data_list = []

    days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}

    for day, events in schedule.items():
        for event in events:
            start_time_str, end_time_str = event['time'].split(' to ')
            start_datetime = datetime.strptime(f"{start_date.strftime('%Y-%m-%d')} {start_time_str}", "%Y-%m-%d %I:%M %p")
            end_datetime = datetime.strptime(f"{start_date.strftime('%Y-%m-%d')} {end_time_str}", "%Y-%m-%d %I:%M %p")

            # Adjust for day of the week
            day_offset = (days_map[day] - start_datetime.weekday()) % 7
            start_datetime += timedelta(days=day_offset)
            end_datetime += timedelta(days=day_offset)

            # Adjust for time zone
            start_datetime = time_zone.localize(start_datetime)
            end_datetime = time_zone.localize(end_datetime)

            event_details = {
                'title': event['title'],
                'description': event['description'],
                'location': event['location'],
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'day': day[:2].upper()
            }

            ics_data = create_ics_file(event_details, start_date, end_date)
            ical_data_list.append(ics_data)

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, ical_data in enumerate(ical_data_list):
            # Generate a file name for each .ics file
            file_name = f"event_{i}.ics"
            zip_file.writestr(file_name, ical_data)

    # Prepare the ZIP file to be read
    zip_buffer.seek(0)
    return zip_buffer.getvalue()



def schedule_to_ics(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'text_input' in request_json and 'start_date' in request_json and 'end_date' in request_json:
        text_input = request_json['text_input']
        start_date_input = request_json['start_date']
        end_date_input = request_json['end_date']
    elif request_args and 'text_input' in request_args and 'start_date' in request_args and 'end_date' in request_args:
        text_input = request_args['text_input']
        start_date_input = request_args['start_date']
        end_date_input = request_args['end_date']
    else:
        return 'Missing input data', 400

    try:
        start_date = datetime.strptime(start_date_input, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_input, "%Y-%m-%d")
        if end_date < start_date:
            raise ValueError("End date must be after start date.")
    except ValueError as e:
        return f"Invalid date input: {e}", 400

    schedule = parse_input(text_input)
    ical_data = parse_and_create_ics_files(schedule, start_date, end_date)

    # Return the iCal data
    return (ical_data, 200, {'Content-Type': 'text/calendar', 'Content-Disposition': 'attachment; filename="schedule.ics"'})
