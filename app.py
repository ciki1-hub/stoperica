from flask import Flask, request, jsonify, render_template  # Add render_template here
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure the PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mx_smolevo_user:9ai3RH9QBiCN6l0JbcgQ1EAMMvsJ07DO@dpg-cvd1h81u0jms739j2pig-a/mx_smolevo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the Session model
class Session(db.Model):
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String, nullable=False)  # Associate sessions with a user
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    startTime = db.Column(db.String, nullable=False)
    fastestLap = db.Column(db.String, nullable=False)
    slowestLap = db.Column(db.String, nullable=False)
    averageLap = db.Column(db.String, nullable=False)
    consistency = db.Column(db.String, nullable=False)
    totalTime = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    dateTime = db.Column(db.String, nullable=False)
    laps = db.Column(db.JSON, nullable=False)
    sectors = db.Column(db.JSON, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Serve the index.html file
@app.route('/')
def index():
    return render_template('index.html')  # Render the index.html template

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

    # Create a new session object
    session = Session(
        id=data['id'],
        username=data['username'],  # Associate the session with the user
        name=data['name'],
        date=data['date'],
        startTime=data['startTime'],
        fastestLap=data['fastestLap'],
        slowestLap=data['slowestLap'],
        averageLap=data['averageLap'],
        consistency=data['consistency'],
        totalTime=data['totalTime'],
        location=data['location'],
        dateTime=data['dateTime'],
        laps=data['laps'],
        sectors=data['sectors']
    )

    # Save the session to the database
    db.session.add(session)
    db.session.commit()

    return jsonify({"message": "Session uploaded successfully"}), 200

# Handle session deletion
@app.route('/delete-session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        # Get the username from the request headers
        username = request.headers.get('Username')
        if not username:
            return jsonify({"error": "Username header is required"}), 400

        # Find the session by ID
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        # Ensure the current user owns the session
        if session.username != username:
            return jsonify({"error": "You are not authorized to delete this session"}), 403

        # Delete the session from the database
        db.session.delete(session)
        db.session.commit()

        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Return paginated and filtered sessions
@app.route('/sessions', methods=['GET'])
def get_sessions():
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    search = request.args.get('search', default='', type=str)

    # Base query
    query = Session.query

    # Filter by username (case-insensitive)
    if search:
        query = query.filter(Session.username.ilike(f'%{search}%'))

    # Paginate the results
    sessions = query.paginate(page=page, per_page=limit, error_out=False)

    # Convert sessions to a list of dictionaries
    sessions_list = [{
        "id": session.id,
        "username": session.username,
        "name": session.name,
        "date": session.date,
        "startTime": session.startTime,
        "fastestLap": session.fastestLap,
        "slowestLap": session.slowestLap,
        "averageLap": session.averageLap,
        "consistency": session.consistency,
        "totalTime": session.totalTime,
        "location": session.location,
        "dateTime": session.dateTime,
        "laps": session.laps,
        "sectors": session.sectors
    } for session in sessions.items]

    return jsonify({
        'sessions': sessions_list,
        'totalPages': sessions.pages
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
