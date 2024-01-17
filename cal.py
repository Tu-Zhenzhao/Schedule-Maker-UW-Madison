from icalendar import Calendar, Event
import pytz
from datetime import datetime, timedelta
import re

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

    file_name = f"./{event_details['title'].replace(' ', '_').replace(':', '')}_{event_details['description'].replace(' ', '_')}.ics"
    with open(file_name, 'wb') as f:
        f.write(cal.to_ical())
    
    return file_name

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
    event_files = []

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

            file_name = create_ics_file(event_details, start_date, end_date)
            event_files.append(file_name)

    return event_files




def main():
    file_path = input("Enter the path to your schedule text file: ").strip()

    try:
        with open(file_path, 'r') as file:
            input_text = file.read()
    except FileNotFoundError:
        print("File not found. Please check the path and try again.")
        return

    start_date_input = input("Enter the start date (format: YYYY-MM-DD): ").strip()
    end_date_input = input("Enter the end date (format: YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_date_input, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_input, "%Y-%m-%d")
        if end_date < start_date:
            raise ValueError("End date must be after start date.")
    except ValueError as e:
        print(f"Invalid date input: {e}")
        return

    schedule = parse_input(input_text)
    ics_files = parse_and_create_ics_files(schedule, start_date, end_date)

    print("Generated .ics files:")
    for file in ics_files:
        print(file)

if __name__ == "__main__":
    main()

