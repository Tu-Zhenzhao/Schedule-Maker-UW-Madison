from icalendar import Calendar, Event
import pytz
from datetime import datetime, timedelta
import re
import io
import zipfile
from collections import defaultdict

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

def convert_schedule_format(new_format_text):
    # Dictionary to map abbreviations to full day names
    day_map = {
        'M': ['Monday'],
        'T': ['Tuesday'],
        'W': ['Wednesday'],
        'R': ['Thursday'],
        'F': ['Friday'],
        'MW': ['Monday', 'Wednesday'],
        'TR': ['Tuesday', 'Thursday'],
        'MWF': ['Monday', 'Wednesday', 'Friday'],
    }

    # Regular expressions to match course details
    course_regex = r'^(.*?):\s+(.*)$'
    meeting_regex = r'^(LEC|DIS)\s+([MTWRF]+)\s+(\d{1,2}:\d{2}\s+[APM]{2})\s*-\s*(\d{1,2}:\d{2}\s+[APM]{2})\s+(.*)$'

    # Parse the input text
    lines = new_format_text.strip().split('\n')
    schedule = defaultdict(list)
    current_course = None

    for line in lines:
        line = line.strip()

        # Check if the line matches a course
        course_match = re.match(course_regex, line)
        if course_match:
            current_course = course_match.group(0).strip()
            course_code = course_match.group(0).split(':', 1)[0].strip()
            course_title = course_match.group(0).split(':', 1)[1].strip()

            continue

        # Check if the line matches a meeting (LEC, DIS, etc.)
        meeting_match = re.match(meeting_regex, line)
        if meeting_match and current_course:
            meeting_type = meeting_match.group(1).strip()
            days = meeting_match.group(2).strip()
            start_time = meeting_match.group(3).strip()
            end_time = meeting_match.group(4).strip()
            location = meeting_match.group(5).strip()

            # For each day, add the meeting details to the schedule
            for day in day_map[days]:
                # For the exact format as previous
                # schedule[day].append(f"{current_course}\n{meeting_type}\n{location}\n{start_time} to {end_time}\n")
                
                # For the format I think it should be
                schedule[day].append(f"{course_code} {meeting_type}\n{course_title}\n{location}\n{start_time} to {end_time}\n")
            continue

    # Format the output in the required format
    output_lines = []
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        if day in schedule:
            output_lines.append(day)
            for event in schedule[day]:
                output_lines.append(event)
            # output_lines.append('')

    return '\n'.join(output_lines).strip()


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


# Function to take individual ics files and reformat them into a single ics file
# Inputs: 
#           ics_list, a list containing each of the ics files
#           output_file, the string path where the file is saved
# Returns:  
#           schedule_file, the combined ics file
#
def combine_ics_files(ics_list):
    combined_ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\n"
    timezone_included = False  # To track if VTIMEZONE has already been added
    
    for ics_data in ics_list:
        cal = Calendar.from_ical(ics_data)
        
        for component in cal.walk():
            if component.name == "VTIMEZONE":
                if not timezone_included:
                    combined_ics_content += component.to_ical().decode("utf-8") + "\n"
                    timezone_included = True
            
            elif component.name == "VEVENT":
                combined_ics_content += component.to_ical().decode("utf-8") + "\n"
    
    # Finish the .ics file with the standard footer
    combined_ics_content += "END:VCALENDAR\n"
    
    return combined_ics_content



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

            # Combine individual ics files into one master ics file
            schedule_file = combine_ics_files(ical_data_list)

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("your_schedule.ics", schedule_file)

    # Prepare the ZIP file to be read
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

###########
# Zhenzhao, is the below function necessary? I don't see you calling it anywhere
###########
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

    reformatted_text = convert_schedule_format(text_input)
    schedule = parse_input(reformatted_text)
    ical_data = parse_and_create_ics_files(schedule, start_date, end_date)

    # Return the iCal data
    return (ical_data, 200, {'Content-Type': 'text/calendar', 'Content-Disposition': 'attachment; filename="schedule.ics"'})
