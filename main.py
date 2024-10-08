from flask import Flask, request, send_file, render_template
from flask_cors import CORS
import io
import datetime
import cal_web  # Import your cal_web script

app = Flask(__name__)
CORS(app)

#@app.route('/')
#def hello():
#    return 'Hello, World!'
@app.route('/')
def index():
    # return app.send_static_file('index.html')
    return render_template('index.html')  # Use your HTML file name here



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

    # Use script's functionality to generate the .ics file
    reformatted_text = cal_web.convert_schedule_format(text_input)
    schedule = cal_web.parse_input(reformatted_text)
    zip_data = cal_web.parse_and_create_ics_files(schedule, start_date, end_date)

    # Convert the ZIP data to a file-like object
    zip_file = io.BytesIO(zip_data)
    zip_file.seek(0)

    return send_file(zip_file, as_attachment=True, download_name='schedule.zip', mimetype='application/zip')

if __name__ == '__main__':
    app.run(debug=True)

