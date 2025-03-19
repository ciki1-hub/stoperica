from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import OperationalError
import logging
from time import sleep

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.info("Starting Flask application...")

# Configure the PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mx_smolevo_user:9ai3RH9QBiCN6l0JbcgQ1EAMMvsJ07DO@dpg-cvd1h81u0jms739j2pig-a/mx_smolevo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 20,
}

# Initialize the database
db = SQLAlchemy(app)

# Define the Session model
class Session(db.Model):
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String, nullable=False)
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

# Error handler for uncaught exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "An internal error occurred"}), 500

# Serve the index.html file
@app.route('/')
def index():
    return "Welcome to the Stopwatch App"

# Handle session uploads
@app.route('/upload', methods=['POST'])
def upload_session():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = ["id", "username", "name", "date", "startTime", "fastestLap", "slowestLap", "averageLap", "consistency", "totalTime", "location", "dateTime", "laps", "sectors"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        session = Session(
            id=data['id'],
            username=data['username'],
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

        db.session.add(session)
        db.session.commit()

        return jsonify({"message": "Session uploaded successfully"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error uploading session: {e}")
        return jsonify({"error": str(e)}), 500

# Handle session deletion
@app.route('/delete-session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        username = request.headers.get('Username')
        if not username:
            return jsonify({"error": "Username header is required"}), 400

        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        if session.username != username:
            return jsonify({"error": "You are not authorized to delete this session"}), 403

        db.session.delete(session)
        db.session.commit()

        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting session: {e}")
        return jsonify({"error": str(e)}), 500

# Return paginated and filtered sessions
@app.route('/sessions', methods=['GET'])
def get_sessions():
    retries = 3
    for attempt in range(retries):
        try:
            page = request.args.get('page', default=1, type=int)
            limit = request.args.get('limit', default=10, type=int)
            search = request.args.get('search', default='', type=str)

            query = Session.query
            if search:
                query = query.filter(Session.username.ilike(f'%{search}%'))

            sessions = query.paginate(page=page, per_page=limit, error_out=False)

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
        except OperationalError as e:
            if attempt < retries - 1:
                sleep(1)  # Wait before retrying
                continue
            else:
                return jsonify({"error": "Database connection failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
