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
