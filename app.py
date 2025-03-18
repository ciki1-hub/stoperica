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
    return jsonify(sessions), 200  # Return all sessions

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
