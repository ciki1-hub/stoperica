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

    # Add a timestamp and user identifier
    data['upload_time'] = datetime.now().isoformat()
    data['user_id'] = request.remote_addr  # Use IP as a simple user identifier

    sessions.append(data)
    return jsonify({"message": "Session uploaded successfully"}), 200

@app.route('/sessions', methods=['GET'])
def get_sessions():
    # Format sessions as plain text
    formatted_sessions = []
    for session in sessions:
        formatted_session = f"""
Session: {session.get('name', 'N/A')}
Date: {session.get('date', 'N/A')}
Total Time: {session.get('totalTime', 'N/A')}
Location: {session.get('location', 'N/A')}
Fastest Lap: {session.get('fastestLap', 'N/A')}
Slowest Lap: {session.get('slowestLap', 'N/A')}
Average Lap: {session.get('averageLap', 'N/A')}
Consistency: {session.get('consistency', 'N/A')}

"""
        # Add laps and sectors
        for i, lap in enumerate(session.get('laps', [])):
            formatted_session += f"Lap {i + 1}: {lap}\n"
            sectors = session.get('sectors', [])
            if i < len(sectors):
                for j, sector in enumerate(sectors[i]):
                    formatted_session += f"   Sector {j + 1}: {sector}\n"
            formatted_session += "\n"

        formatted_sessions.append(formatted_session)

    return "\n".join(formatted_sessions), 200, {'Content-Type': 'text/plain'}
