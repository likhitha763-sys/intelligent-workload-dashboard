import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from config import Config
from models import db, User
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.subject_routes import subject_bp
from routes.task_routes import task_bp
from routes.assignment_routes import assignment_bp
from routes.exam_routes import exam_bp
from routes.placeholder_routes import placeholder_bp
from routes.workload_api import workload_api_bp
from routes.planner_routes import planner_bp
from routes.ai_insights_routes import ai_insights_bp
from routes.calendar_routes import calendar_bp
from routes.attendance_routes import attendance_bp
from routes.profile_routes import profile_bp
from routes.stage4_api import stage4_api_bp
from routes.demo_routes import demo_bp
from routes.error_routes import error_bp

# Load environment variables
load_dotenv()

# Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# Ensure database directory exists for SQLite
db_uri = app.config['SQLALCHEMY_DATABASE_URI']
if db_uri.startswith('sqlite:///'):
    db_file_path = db_uri.replace('sqlite:///', '')
    os.makedirs(os.path.dirname(db_file_path), exist_ok=True)

# Initialize Flask extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    return db.session.get(User, int(user_id))

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(subject_bp)
app.register_blueprint(task_bp)
app.register_blueprint(assignment_bp)
app.register_blueprint(exam_bp)
app.register_blueprint(placeholder_bp)
app.register_blueprint(workload_api_bp)
app.register_blueprint(planner_bp)
app.register_blueprint(ai_insights_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(stage4_api_bp)
app.register_blueprint(demo_bp)
app.register_blueprint(error_bp)

# Automatically create/update database tables within application context
with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if 'subjects' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('subjects')]
            if 'code' not in columns:
                db.session.execute(text("ALTER TABLE subjects ADD COLUMN code VARCHAR(20)"))
            if 'semester' not in columns:
                db.session.execute(text("ALTER TABLE subjects ADD COLUMN semester VARCHAR(20)"))
            db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
