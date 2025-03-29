from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, IntegrityError
import logging
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://mx_smolevo_user:9ai3RH9QBiCN6l0JbcgQ1EAMMvsJ07DO@dpg-cvd1h81u0jms739j2pig-a/mx_smolevo'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 20,
}

db = SQLAlchemy(app)

class Session(db.Model):
    __tablename__ = 'session'
    
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    startTime = db.Column(db.String(20), nullable=False)
    fastestLap = db.Column(db.String(20), nullable=False)
    slowestLap = db.Column(db.String(20), nullable=False)
    averageLap = db.Column(db.String(20), nullable=False)
    consistency = db.Column(db.String(20), nullable=False)
    totalTime = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(80), nullable=False)
    dateTime = db.Column(db.String(30), nullable=False)
    laps = db.Column(db.JSON, nullable=False)
    sectors = db.Column(db.JSON, nullable=False)
    topSpeed = db.Column(db.String(20), nullable=True)
    averageSpeed = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

def initialize_database():
    """Initialize database and handle schema migrations"""
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Check for missing columns and add them
            inspector = inspect(db.engine)
            if 'session' in inspector.get_table_names():
                columns = inspector.get_columns('session')
                existing_columns = {col['name'] for col in columns}
                
                # List of columns that should exist
                required_columns = {
                    'topSpeed', 'averageSpeed', 'created_at'
                }
                
                # Add any missing columns using proper SQLAlchemy 2.0 connection
                with db.engine.connect() as connection:
                    if 'topSpeed' not in existing_columns:
                        connection.execute(text('ALTER TABLE session ADD COLUMN "topSpeed" VARCHAR(20)'))
                        logger.info("Added topSpeed column to session table")
                        connection.commit()
                    
                    if 'averageSpeed' not in existing_columns:
                        connection.execute(text('ALTER TABLE session ADD COLUMN "averageSpeed" VARCHAR(20)'))
                        logger.info("Added averageSpeed column to session table")
                        connection.commit()
                    
                    if 'created_at' not in existing_columns:
                        connection.execute(text('ALTER TABLE session ADD COLUMN created_at TIMESTAMP'))
                        logger.info("Added created_at column to session table")
                        connection.commit()
                        
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}", exc_info=True)
            raise

# Initialize the database when starting the app
initialize_database()

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == os.environ.get('ADMIN_USER', 'admin') and \
           password == os.environ.get('ADMIN_PASSWORD', 'securepassword'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "Invalid credentials", 401
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    sessions = Session.query.order_by(Session.created_at.desc()).all()
    return render_template('admin_dashboard.html', sessions=sessions)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/edit-session/<session_id>', methods=['GET', 'POST'])
def admin_edit_session(session_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    session_to_edit = Session.query.get_or_404(session_id)
    
    if request.method == 'POST':
        try:
            session_to_edit.username = request.form.get('username', session_to_edit.username)
            session_to_edit.name = request.form.get('name', session_to_edit.name)
            session_to_edit.topSpeed = request.form.get('topSpeed', session_to_edit.topSpeed)
            session_to_edit.averageSpeed = request.form.get('averageSpeed', session_to_edit.averageSpeed)
            # Update other fields as needed
            
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating session: {str(e)}")
            return "Error updating session", 500
    
    return render_template('edit_session.html', session=session_to_edit)

@app.route('/admin/delete-session/<session_id>', methods=['DELETE'])
def admin_delete_session(session_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        session_to_delete = Session.query.get_or_404(session_id)
        db.session.delete(session_to_delete)
        db.session.commit()
        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting session: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/delete-session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        username = request.headers.get('Username')
        if not username:
            return jsonify({"error": "Username header is required"}), 400

        session_to_delete = Session.query.get_or_404(session_id)
        
        # Check if the user owns the session or is admin
        if session_to_delete.username != username and not session.get('admin_logged_in'):
            return jsonify({"error": "You are not authorized to delete this session"}), 403

        db.session.delete(session_to_delete)
        db.session.commit()
        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting session: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_session():
    try:
        data = request.get_json()
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

        # Check for existing session
        existing_session = Session.query.get(data['id'])
        if existing_session:
            # Update existing session
            for field in required_fields:
                setattr(existing_session, field, data[field])
            existing_session.topSpeed = data.get('topSpeed')
            existing_session.averageSpeed = data.get('averageSpeed')
        else:
            # Create new session
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
        return jsonify({"message": "Session saved successfully"}), 200
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Integrity error saving session: {str(e)}")
        return jsonify({"error": "Session ID already exists"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving session: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/sessions', methods=['GET'])
def get_sessions():
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
            'totalPages': sessions.pages,
            'currentPage': sessions.page
        })
        
    except OperationalError as e:
        logger.error(f"Database operational error: {str(e)}")
        return jsonify({"error": "Database connection error"}), 500
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
