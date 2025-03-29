from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import OperationalError
import logging
from time import sleep
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Required for session management

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

# Define the Session model with speed metrics
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
    topSpeed = db.Column(db.String, nullable=True)  # New field for top speed
    averageSpeed = db.Column(db.String, nullable=True)  # New field for average speed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # New field for creation timestamp

# Create the database tables and handle migrations
with app.app_context():
    # First create all tables
    db.create_all()
    
    # Then check and add any missing columns
    try:
        inspector = db.inspect(db.engine)
        if 'session' in inspector.get_table_names():
            columns = inspector.get_columns('session')
            column_names = [col['name'] for col in columns]
            
            if 'topSpeed' not in column_names:
                db.engine.execute('ALTER TABLE session ADD COLUMN topSpeed VARCHAR')
                app.logger.info("Added topSpeed column to database")
            
            if 'averageSpeed' not in column_names:
                db.engine.execute('ALTER TABLE session ADD COLUMN averageSpeed VARCHAR')
                app.logger.info("Added averageSpeed column to database")
                
            if 'created_at' not in column_names:
                db.engine.execute('ALTER TABLE session ADD COLUMN created_at TIMESTAMP')
                app.logger.info("Added created_at column to database")
    except Exception as e:
        app.logger.error(f"Error during database migration: {e}")

# Error handler for uncaught exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "An internal error occurred"}), 500

# Serve the index.html file
@app.route('/')
def index():
    return render_template('index.html')

# About page route
@app.route('/about')
def about():
    app.logger.info("About page accessed")
    return render_template('about.html')
    
@app.route('/privacy')
def privacy_policy():
    app.logger.info("Privacy policy page accessed")
    return render_template('privacy.html')

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Hardcoded admin credentials (not secure for production)
        if username == 'admin' and password == 'Bitola123!@#1':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials", 401

    return render_template('admin_login.html')

# Admin dashboard route
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # Fetch all sessions from the database
    sessions = Session.query.order_by(Session.created_at.desc()).all()
    app.logger.info(f"Sessions fetched: {len(sessions)}")
    return render_template('admin_dashboard.html', sessions=sessions)

# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Edit session route
@app.route('/admin/edit-session/<session_id>', methods=['GET', 'POST'])
def admin_edit_session(session_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    session_to_edit = Session.query.get(session_id)
    if not session_to_edit:
        return jsonify({"error": "Session not found"}), 404

    if request.method == 'POST':
        data = request.form
        session_to_edit.username = data.get('username', session_to_edit.username)
        session_to_edit.name = data.get('name', session_to_edit.name)
        session_to_edit.date = data.get('date', session_to_edit.date)
        session_to_edit.startTime = data.get('startTime', session_to_edit.startTime)
        session_to_edit.fastestLap = data.get('fastestLap', session_to_edit.fastestLap)
        session_to_edit.slowestLap = data.get('slowestLap', session_to_edit.slowestLap)
        session_to_edit.averageLap = data.get('averageLap', session_to_edit.averageLap)
        session_to_edit.consistency = data.get('consistency', session_to_edit.consistency)
        session_to_edit.totalTime = data.get('totalTime', session_to_edit.totalTime)
        session_to_edit.location = data.get('location', session_to_edit.location)
        session_to_edit.dateTime = data.get('dateTime', session_to_edit.dateTime)
        session_to_edit.laps = data.get('laps', session_to_edit.laps)
        session_to_edit.sectors = data.get('sectors', session_to_edit.sectors)
        session_to_edit.topSpeed = data.get('topSpeed', session_to_edit.topSpeed)
        session_to_edit.averageSpeed = data.get('averageSpeed', session_to_edit.averageSpeed)

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_session.html', session=session_to_edit)

# Delete session route
@app.route('/admin/delete-session/<session_id>', methods=['DELETE'])
def admin_delete_session(session_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    session_to_delete = Session.query.get(session_id)
    if not session_to_delete:
        return jsonify({"error": "Session not found"}), 404

    db.session.delete(session_to_delete)
    db.session.commit()

    return jsonify({"message": "Session deleted successfully"}), 200

# Handle session uploads
@app.route('/upload', methods=['POST'])
def upload_session():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = [
            "id", "username", "name", "date", "startTime", 
            "fastestLap", "slowestLap", "averageLap", "consistency",
            "totalTime", "location", "dateTime", "laps", "sectors"
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Check if a session with the same ID already exists
        existing_session = Session.query.get(data['id'])
        if existing_session:
            # Update the existing session with speed data
            existing_session.username = data['username']
            existing_session.name = data['name']
            existing_session.date = data['date']
            existing_session.startTime = data['startTime']
            existing_session.fastestLap = data['fastestLap']
            existing_session.slowestLap = data['slowestLap']
            existing_session.averageLap = data['averageLap']
            existing_session.consistency = data['consistency']
            existing_session.totalTime = data['totalTime']
            existing_session.location = data['location']
            existing_session.dateTime = data['dateTime']
            existing_session.laps = data['laps']
            existing_session.sectors = data['sectors']
            existing_session.topSpeed = data.get('topSpeed')
            existing_session.averageSpeed = data.get('averageSpeed')
            db.session.commit()
            return jsonify({"message": "Session updated successfully"}), 200
        else:
            # Insert a new session with speed data
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
                sectors=data['sectors'],
                topSpeed=data.get('topSpeed'),
                averageSpeed=data.get('averageSpeed')
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

            sessions = query.order_by(Session.created_at.desc()).paginate(
                page=page, 
                per_page=limit, 
                error_out=False
            )

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
                "sectors": session.sectors,
                "topSpeed": session.topSpeed,
                "averageSpeed": session.averageSpeed,
                "createdAt": session.created_at.isoformat() if session.created_at else None
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
