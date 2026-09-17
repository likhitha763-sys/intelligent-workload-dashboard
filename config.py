import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'database')
os.makedirs(db_dir, exist_ok=True)

# Absolute SQLite database paths
main_db_path = os.path.join(db_dir, 'student_dashboard.db')
test_db_path = os.path.join(db_dir, 'test_student_dashboard.db')

class Config:
    """Base Configuration for Flask Application."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
    
    # Check environment DATABASE_URL first (for cloud production)
    env_db_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
    if env_db_url and not env_db_url.startswith('sqlite:///database/'):
        # Convert legacy postgres:// to postgresql:// for SQLAlchemy
        if env_db_url.startswith("postgres://"):
            env_db_url = env_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = env_db_url
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{main_db_path}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    """Configuration for Automated Testing using separate test database."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{test_db_path}'
