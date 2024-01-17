from flask import Flask, request, send_file
from flask_cors import CORS
import io
import datetime
import cal_web  # Import your cal_web script

app = Flask(__name__)
CORS(app)

@app.route('/generate-ics', methods=['POST'])
def generate_ics():
    data = request.json
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    text_input = data.get('schedule')

    # Convert dates from string to datetime objects
    try:
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        return f"Invalid date input: {e}", 400

    # Use your script's functionality to generate the .ics file
    schedule = cal_web.parse_input(text_input)
    zip_data = cal_web.parse_and_create_ics_files(schedule, start_date, end_date)

    # Convert the ZIP data to a file-like object
    zip_file = io.BytesIO(zip_data)
    zip_file.seek(0)

    return send_file(zip_file, as_attachment=True, attachment_filename='schedule.zip', mimetype='application/zip')

if __name__ == '__main__':
    app.run(debug=True)

