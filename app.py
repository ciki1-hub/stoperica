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
app.secret_key = 'your-secret-key-here'  # Change this for production!

# ===== ADMIN CREDENTIALS (For development only - CHANGE THESE!) =====
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Bitola123!@#1"
# ===================================================

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
            db.create_all()
            
            inspector = inspect(db.engine)
            if 'session' in inspector.get_table_names():
                columns = inspector.get_columns('session')
                existing_columns = {col['name'] for col in columns}
                
                required_columns = {'topSpeed', 'averageSpeed', 'created_at'}
                
                with db.engine.connect() as connection:
                    if 'topSpeed' not in existing_columns:
                        connection.execute(text('ALTER TABLE session ADD COLUMN "topSpeed" VARCHAR(20)'))
                        logger.info("Added topSpeed column")
                        connection.commit()
                    
                    if 'averageSpeed' not in existing_columns:
                        connection.execute(text('ALTER TABLE session ADD COLUMN "averageSpeed" VARCHAR(20)'))
                        logger.info("Added averageSpeed column")
                        connection.commit()
                    
                    if 'created_at' not in existing_columns:
                        connection.execute(text('ALTER TABLE session ADD COLUMN created_at TIMESTAMP'))
                        logger.info("Added created_at column")
                        connection.commit()
                        
        except Exception as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise

initialize_database()

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Error: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

# ===== FRONTEND ROUTES =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

# ===== ADMIN ROUTES =====
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update error: {str(e)}")
            return "Update failed", 500
    
    return render_template('edit_session.html', session=session_to_edit)

# ===== API ROUTES =====
@app.route('/admin/delete-session/<session_id>', methods=['DELETE'])
def admin_delete_session(session_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        session_to_delete = Session.query.get_or_404(session_id)
        db.session.delete(session_to_delete)
        db.session.commit()
        return jsonify({"message": "Admin deleted session"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin delete error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/delete-session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        username = request.headers.get('Username')
        if not username:
            return jsonify({"error": "Username required"}), 400

        session_to_delete = Session.query.get_or_404(session_id)
        
        # Allow deletion if user owns session OR is admin
        if session_to_delete.username != username and not session.get('admin_logged_in'):
            return jsonify({"error": "Unauthorized"}), 403

        db.session.delete(session_to_delete)
        db.session.commit()
        return jsonify({"message": "Session deleted"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_session():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400

        required_fields = [
            "id", "username", "name", "date", "startTime",
            "fastestLap", "slowestLap", "averageLap", "consistency",
            "totalTime", "location", "dateTime", "laps", "sectors"
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing {field}"}), 400

        existing_session = Session.query.get(data['id'])
        if existing_session:
            for field in required_fields:
                setattr(existing_session, field, data[field])
            existing_session.topSpeed = data.get('topSpeed')
            existing_session.averageSpeed = data.get('averageSpeed')
        else:
            new_session = Session(
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
            db.session.add(new_session)
        
        db.session.commit()
        return jsonify({"message": "Session saved"}), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Session exists"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/sessions', methods=['GET'])
def get_sessions():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '', type=str)

        query = Session.query
        if search:
            query = query.filter(Session.username.ilike(f'%{search}%'))

        sessions = query.order_by(Session.created_at.desc()).paginate(
            page=page, 
            per_page=limit, 
            error_out=False
        )

        sessions_list = [{
            "id": s.id,
            "username": s.username,
            "name": s.name,
            "date": s.date,
            "startTime": s.startTime,
            "fastestLap": s.fastestLap,
            "slowestLap": s.slowestLap,
            "averageLap": s.averageLap,
            "consistency": s.consistency,
            "totalTime": s.totalTime,
            "location": s.location,
            "dateTime": s.dateTime,
            "laps": s.laps,
            "sectors": s.sectors,
            "topSpeed": s.topSpeed,
            "averageSpeed": s.averageSpeed,
            "createdAt": s.created_at.isoformat() if s.created_at else None
        } for s in sessions.items]

        return jsonify({
            'sessions': sessions_list,
            'totalPages': sessions.pages,
            'currentPage': sessions.page
        })
        
    except Exception as e:
        logger.error(f"Fetch error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
