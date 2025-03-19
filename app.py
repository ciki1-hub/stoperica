from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import logging
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
app.logger.info("Starting Flask application...")

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mx_smolevo_user:9ai3RH9QBiCN6l0JbcgQ1EAMMvsJ07DO@dpg-cvd1h81u0jms739j2pig-a/mx_smolevo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 20,
}
app.config['SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

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

with app.app_context():
    db.create_all()
    admin_username = "admin"
    admin_password = "Bitola123!@#1"
    admin_user = Admin.query.filter_by(username=admin_username).first()
    if not admin_user:
        admin_user = Admin(username=admin_username)
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Admin user created successfully.")

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    admin = Admin.query.filter_by(username=username).first()
    if admin and admin.check_password(password):
        login_user(admin)
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/admin/logout', methods=['POST'])
@login_required
def admin_logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

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

@app.route('/sessions', methods=['GET'])
def get_sessions():
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
    except Exception as e:
        app.logger.error(f"Error fetching sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/delete-session/<session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        db.session.delete(session)
        db.session.commit()

        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/edit-session/<session_id>', methods=['PUT'])
@login_required
def edit_session(session_id):
    try:
        data = request.json
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        session.name = data.get('name', session.name)
        session.date = data.get('date', session.date)
        session.startTime = data.get('startTime', session.startTime)
        session.fastestLap = data.get('fastestLap', session.fastestLap)
        session.slowestLap = data.get('slowestLap', session.slowestLap)
        session.averageLap = data.get('averageLap', session.averageLap)
        session.consistency = data.get('consistency', session.consistency)
        session.totalTime = data.get('totalTime', session.totalTime)
        session.location = data.get('location', session.location)
        session.dateTime = data.get('dateTime', session.dateTime)
        session.laps = data.get('laps', session.laps)
        session.sectors = data.get('sectors', session.sectors)

        db.session.commit()

        return jsonify({"message": "Session updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating session: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
