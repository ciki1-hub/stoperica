from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from werkzeug.exceptions import HTTPException
import logging
import os
from time import sleep

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Keep this secret in production

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Flask application...")

# Database configuration (as you prefer)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mx_smolevo_user:9ai3RH9QBiCN6l0JbcgQ1EAMMvsJ07DO@dpg-cvd1h81u0jms739j2pig-a/mx_smolevo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 20,
}

# Initialize database
db = SQLAlchemy(app)

# Database model
class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    startTime = db.Column(db.String(20), nullable=False)
    fastestLap = db.Column(db.String(20), nullable=False)
    slowestLap = db.Column(db.String(20), nullable=False)
    averageLap = db.Column(db.String(20), nullable=False)
    consistency = db.Column(db.String(20), nullable=False)
    totalTime = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    dateTime = db.Column(db.String(30), nullable=False)
    laps = db.Column(db.JSON, nullable=False)
    sectors = db.Column(db.JSON, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "date": self.date,
            "startTime": self.startTime,
            "fastestLap": self.fastestLap,
            "slowestLap": self.slowestLap,
            "averageLap": self.averageLap,
            "consistency": self.consistency,
            "totalTime": self.totalTime,
            "location": self.location,
            "dateTime": self.dateTime,
            "laps": self.laps,
            "sectors": self.sectors
        }

# Create tables (if not exists)
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables initialized")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# Error handlers
@app.errorhandler(HTTPException)
def handle_http_error(e):
    logger.error(f"HTTP error {e.code}: {e.name}")
    return jsonify({"error": e.description}), e.code

@app.errorhandler(Exception)
def handle_general_error(e):
    logger.error(f"Unexpected error: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500

# Static files routes
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/screenshots/<path:filename>')
def screenshots(filename):
    return send_from_directory('static/screenshots', filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

# Main routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    logger.info("About page accessed")
    return render_template('about.html')

# Admin routes with hardcoded credentials as you prefer
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'Bitola123!@#1'
}

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if (username == ADMIN_CREDENTIALS['username'] and 
            password == ADMIN_CREDENTIALS['password']):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        
        return "Invalid credentials", 401

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    try:
        sessions = Session.query.order_by(Session.dateTime.desc()).all()
        return render_template('admin_dashboard.html', sessions=sessions)
    except SQLAlchemyError as e:
        logger.error(f"Failed to fetch sessions: {e}")
        return "Failed to load dashboard", 500

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/edit-session/<session_id>', methods=['GET', 'POST'])
def admin_edit_session(session_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    session_data = Session.query.get_or_404(session_id)

    if request.method == 'POST':
        try:
            for field in ['username', 'name', 'date', 'startTime', 'fastestLap',
                        'slowestLap', 'averageLap', 'consistency', 'totalTime',
                        'location', 'dateTime']:
                if field in request.form:
                    setattr(session_data, field, request.form[field])
            
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Failed to update session: {e}")
            return "Failed to update session", 500

    return render_template('edit_session.html', session=session_data)

@app.route('/admin/delete-session/<session_id>', methods=['DELETE'])
def admin_delete_session(session_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    session_data = Session.query.get_or_404(session_id)
    
    try:
        db.session.delete(session_data)
        db.session.commit()
        return jsonify({"message": "Session deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to delete session: {e}")
        return jsonify({"error": "Failed to delete session"}), 500

# API routes
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        username = request.args.get('username', default=None, type=str)
        search = request.args.get('search', default=None, type=str)

        query = Session.query

        if username:
            query = query.filter_by(username=username)
        if search:
            query = query.filter(Session.name.ilike(f'%{search}%'))

        paginated_sessions = query.order_by(Session.dateTime.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

        return jsonify({
            'sessions': [session.to_dict() for session in paginated_sessions.items],
            'total': paginated_sessions.total,
            'pages': paginated_sessions.pages,
            'current_page': paginated_sessions.page
        })
    except SQLAlchemyError as e:
        logger.error(f"Failed to fetch sessions: {e}")
        return jsonify({"error": "Failed to fetch sessions"}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = ['id', 'username', 'name', 'date', 'startTime', 
                         'fastestLap', 'slowestLap', 'averageLap', 'consistency',
                         'totalTime', 'location', 'dateTime', 'laps', 'sectors']
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

        new_session = Session(**data)
        db.session.add(new_session)
        db.session.commit()

        return jsonify(new_session.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to create session: {e}")
        return jsonify({"error": "Failed to create session"}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        username = request.headers.get('X-Username')
        if not username:
            return jsonify({"error": "Username header required"}), 400

        session_data = Session.query.get_or_404(session_id)
        
        if session_data.username != username:
            return jsonify({"error": "Unauthorized"}), 403

        db.session.delete(session_data)
        db.session.commit()

        return jsonify({"message": "Session deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to delete session: {e}")
        return jsonify({"error": "Failed to delete session"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
