from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage for sessions (replace this with a database in production)
sessions = []

@app.route('/upload', methods=['POST'])
def upload_session():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Add a timestamp and user identifier (you can modify this to include user-specific data)
    data['upload_time'] = datetime.now().isoformat()
    data['user_id'] = request.remote_addr  # Use IP as a simple user identifier

    sessions.append(data)
    return jsonify({"message": "Session uploaded successfully"}), 200

@app.route('/sessions', methods=['GET'])
def get_sessions():
    user_id = request.args.get('user_id')
    if user_id:
        user_sessions = [session for session in sessions if session.get('user_id') == user_id]
        return jsonify(user_sessions), 200
    return jsonify(sessions), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
