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

# Return paginated and filtered sessions
@app.route('/sessions', methods=['GET'])
def get_sessions():
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    search = request.args.get('search', default='', type=str)

    # Filter sessions by username (case-insensitive)
    filtered_sessions = [session for session in sessions if search.lower() in session['username'].lower()]

    # Paginate the filtered sessions
    start = (page - 1) * limit
    end = start + limit
    paginated_sessions = filtered_sessions[start:end]

    # Calculate total pages
    total_pages = (len(filtered_sessions) + limit - 1) // limit

    return jsonify({
        'sessions': paginated_sessions,
        'totalPages': total_pages
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
