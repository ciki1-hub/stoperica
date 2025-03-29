from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import OperationalError
import logging
from time import sleep
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mx_smolevo_user:9ai3RH9QBiCN6l0JbcgQ1EAMMvsJ07DO@dpg-cvd1h81u0jms739j2pig-a/mx_smolevo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 20,
}

db = SQLAlchemy(app)

# Session Model
class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    fastest_lap = db.Column(db.String(20), nullable=False)
    slowest_lap = db.Column(db.String(20), nullable=False)
    average_lap = db.Column(db.String(20), nullable=False)
    consistency = db.Column(db.String(20), nullable=False)
    total_time = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_time = db.Column(db.String(30), nullable=False)
    laps = db.Column(db.JSON, nullable=False)
    sectors = db.Column(db.JSON, nullable=False)
    top_speed = db.Column(db.String(20), nullable=True)
    average_speed = db.Column(db.String(20), nullable=True)
    is_uploaded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Session {self.id} - {self.name}>"

# Create tables
with app.app_context():
    db.create_all()

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # In production, use proper authentication and password hashing
        if username == 'admin' and password == 'secure_password_here':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "Invalid credentials", 401
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    sessions = Session.query.order_by(Session.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin_dashboard.html', sessions=sessions)

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
        session_data.name = request.form.get('name', session_data.name)
        session_data.username = request.form.get('username', session_data.username)
        session_data.location = request.form.get('location', session_data.location)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_session.html', session=session_data)

@app.route('/admin/delete-session/<session_id>', methods=['POST'])
def admin_delete_session(session_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    session_to_delete = Session.query.get_or_404(session_id)
    db.session.delete(session_to_delete)
    db.session.commit()
    
    return jsonify({"message": "Session deleted successfully"}), 200

# API Endpoints
@app.route('/api/upload', methods=['POST'])
def upload_session():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = [
            'id', 'username', 'name', 'date', 'startTime', 'fastestLap',
            'slowestLap', 'averageLap', 'consistency', 'totalTime', 'location',
            'dateTime', 'laps', 'sectors', 'topSpeed', 'averageSpeed'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

        # Check for existing session
        existing_session = Session.query.get(data['id'])
        
        if existing_session:
            # Update existing session
            existing_session.username = data['username']
            existing_session.name = data['name']
            existing_session.date = data['date']
            existing_session.start_time = data['startTime']
            existing_session.fastest_lap = data['fastestLap']
            existing_session.slowest_lap = data['slowestLap']
            existing_session.average_lap = data['averageLap']
            existing_session.consistency = data['consistency']
            existing_session.total_time = data['totalTime']
            existing_session.location = data['location']
            existing_session.date_time = data['dateTime']
            existing_session.laps = data['laps']
            existing_session.sectors = data['sectors']
            existing_session.top_speed = data['topSpeed']
            existing_session.average_speed = data['averageSpeed']
            existing_session.is_uploaded = True
        else:
            # Create new session
            new_session = Session(
                id=data['id'],
                username=data['username'],
                name=data['name'],
                date=data['date'],
                start_time=data['startTime'],
                fastest_lap=data['fastestLap'],
                slowest_lap=data['slowestLap'],
                average_lap=data['averageLap'],
                consistency=data['consistency'],
                total_time=data['totalTime'],
                location=data['location'],
                date_time=data['dateTime'],
                laps=data['laps'],
                sectors=data['sectors'],
                top_speed=data['topSpeed'],
                average_speed=data['averageSpeed'],
                is_uploaded=True
            )
            db.session.add(new_session)
        
        db.session.commit()
        return jsonify({"message": "Session processed successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtering parameters
        username = request.args.get('username')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = Session.query
        
        if username:
            query = query.filter(Session.username.ilike(f'%{username}%'))
        
        if date_from:
            query = query.filter(Session.date >= date_from)
        
        if date_to:
            query = query.filter(Session.date <= date_to)
        
        # Order by most recent first
        query = query.order_by(Session.created_at.desc())
        
        # Paginate results
        paginated_sessions = query.paginate(page=page, per_page=per_page, error_out=False)
        
        sessions_data = [{
            'id': session.id,
            'username': session.username,
            'name': session.name,
            'date': session.date,
            'startTime': session.start_time,
            'fastestLap': session.fastest_lap,
            'slowestLap': session.slowest_lap,
            'averageLap': session.average_lap,
            'consistency': session.consistency,
            'totalTime': session.total_time,
            'location': session.location,
            'dateTime': session.date_time,
            'laps': session.laps,
            'sectors': session.sectors,
            'topSpeed': session.top_speed,
            'averageSpeed': session.average_speed,
            'createdAt': session.created_at.isoformat()
        } for session in paginated_sessions.items]
        
        return jsonify({
            'sessions': sessions_data,
            'total': paginated_sessions.total,
            'pages': paginated_sessions.pages,
            'current_page': paginated_sessions.page
        })
    
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/sessions/<session_id>', methods=['GET', 'DELETE'])
def session_detail(session_id):
    try:
        session_data = Session.query.get_or_404(session_id)
        
        if request.method == 'DELETE':
            # Check authorization
            username = request.headers.get('X-Username')
            if not username or username != session_data.username:
                return jsonify({"error": "Unauthorized"}), 403
            
            db.session.delete(session_data)
            db.session.commit()
            return jsonify({"message": "Session deleted successfully"}), 200
        
        # GET request
        return jsonify({
            'id': session_data.id,
            'username': session_data.username,
            'name': session_data.name,
            'date': session_data.date,
            'startTime': session_data.start_time,
            'fastestLap': session_data.fastest_lap,
            'slowestLap': session_data.slowest_lap,
            'averageLap': session_data.average_lap,
            'consistency': session_data.consistency,
            'totalTime': session_data.total_time,
            'location': session_data.location,
            'dateTime': session_data.date_time,
            'laps': session_data.laps,
            'sectors': session_data.sectors,
            'topSpeed': session_data.top_speed,
            'averageSpeed': session_data.average_speed,
            'createdAt': session_data.created_at.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error with session {session_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
