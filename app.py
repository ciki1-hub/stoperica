from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage for sessions (replace this with a database in production)
sessions = []

@app.route('/upload', methods=['POST'])
def upload_session():
    data = request.json  # Get JSON data from the request
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Ensure required fields are present
    required_fields = ["username", "name", "date", "startTime", "fastestLap", "slowestLap", "averageLap", "consistency", "totalTime", "location", "dateTime", "laps", "sectors"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Add a timestamp and user identifier
    data['upload_time'] = datetime.now().isoformat()
    data['user_id'] = request.remote_addr  # Use IP as a simple user identifier

    sessions.append(data)
    return jsonify({"message": "Session uploaded successfully"}), 200

@app.route('/sessions', methods=['GET'])
def get_sessions():
    username = request.args.get('username')  # Get the username from query parameters
    filtered_sessions = sessions

    # Filter sessions by username if provided
    if username:
        filtered_sessions = [session for session in sessions if session.get('username') == username]

    return jsonify(filtered_sessions), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
