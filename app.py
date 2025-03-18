from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# In-memory storage for sessions (replace this with a database in production)
sessions = []

# Serve the index.html file
@app.route('/')
def index():
    return render_template('index.html')

# Handle session uploads
@app.route('/upload', methods=['POST'])
def upload_session():
    data = request.json  # Get JSON data from the request
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Ensure required fields are present
    required_fields = ["id", "username", "name", "date", "startTime", "fastestLap", "slowestLap", "averageLap", "consistency", "totalTime", "location", "dateTime", "laps", "sectors"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Add a timestamp
    data['upload_time'] = datetime.now().isoformat()

    sessions.append(data)  # Store the session
    return jsonify({"message": "Session uploaded successfully"}), 200

# Return all sessions
@app.route('/sessions', methods=['GET'])
def get_sessions():
    return jsonify(sessions), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
