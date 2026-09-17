from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# SQLAlchemy database instance
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User Model representing an engineering student with profile attributes."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Student Profile Attributes (Stage 4)
    student_id_no = db.Column(db.String(50), nullable=True)   # Roll No / Student ID
    college = db.Column(db.String(150), nullable=True)         # College / Institute Name
    department = db.Column(db.String(100), nullable=True)      # Department (e.g. Computer Science)
    year = db.Column(db.String(20), nullable=True)             # Year (e.g. 3rd Year)
    semester = db.Column(db.String(20), nullable=True)         # Semester (e.g. Semester 6)

    # Relationships
    subjects = db.relationship('Subject', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    exams = db.relationship('Exam', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    preference = db.relationship('StudyPreference', backref='student', uselist=False, cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashes and stores the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies the hashed password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Subject(db.Model):
    """Subject Model."""
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=True)        # Subject Code (e.g. CS501)
    semester = db.Column(db.String(20), nullable=True)    # Semester (e.g. Semester 5)
    faculty_name = db.Column(db.String(100), nullable=True)
    credits = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tasks = db.relationship('Task', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    exams = db.relationship('Exam', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    attendance = db.relationship('Attendance', backref='subject', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subject {self.name}>'


class Task(db.Model):
    """Task Model for academic workloads."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High
    difficulty = db.Column(db.String(20), default='Medium')  # Easy, Medium, Hard
    estimated_hours = db.Column(db.Float, default=1.0)
    status = db.Column(db.String(20), default='Not Started')  # Not Started, In Progress, Completed, Overdue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Task {self.title}>'


class Assignment(db.Model):
    """Assignment Model."""
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    difficulty = db.Column(db.String(20), default='Medium')  # Easy, Medium, Hard
    estimated_hours = db.Column(db.Float, default=2.0)
    status = db.Column(db.String(20), default='Not Started')  # Not Started, In Progress, Submitted, Late
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Assignment {self.title}>'


class Exam(db.Model):
    """Exam Model."""
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    exam_date = db.Column(db.Date, nullable=False)
    exam_time = db.Column(db.String(20), nullable=True)
    difficulty = db.Column(db.String(20), default='Medium')  # Easy, Medium, Hard
    syllabus = db.Column(db.Text, nullable=True)
    prep_percentage = db.Column(db.Integer, default=0)  # 0 to 100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Exam for Subject ID {self.subject_id} on {self.exam_date}>'


class Attendance(db.Model):
    """Attendance Model tracking course attendance for each subject."""
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    total_classes = db.Column(db.Integer, default=0)
    attended_classes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def percentage(self):
        """Calculates attendance percentage."""
        if not self.total_classes or self.total_classes <= 0:
            return 0.0
        return round((self.attended_classes / self.total_classes) * 100.0, 1)

    @property
    def status(self):
        """Calculates status category: SAFE (>= 75%), WARNING (60-74%), CRITICAL (< 60%)."""
        pct = self.percentage
        if pct >= 75.0:
            return 'SAFE'
        elif pct >= 60.0:
            return 'WARNING'
        else:
            return 'CRITICAL'

    def __repr__(self):
        return f'<Attendance Subject ID {self.subject_id}: {self.percentage}%>'


class StudyPreference(db.Model):
    """StudyPreference Model storing personalized student planner settings."""
    __tablename__ = 'study_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    available_hours_per_day = db.Column(db.Float, default=4.0)
    preferred_start_time = db.Column(db.String(10), default='09:00')
    preferred_end_time = db.Column(db.String(10), default='21:00')
    break_duration_mins = db.Column(db.Integer, default=15)
    theme = db.Column(db.String(20), default='light')  # 'light' or 'dark'
    notifications_enabled = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<StudyPreference User {self.user_id}: {self.available_hours_per_day} hrs/day>'


class StudySession(db.Model):
    """StudySession Model storing generated schedule slots on the calendar."""
    __tablename__ = 'study_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudySession {self.title} on {self.session_date}>'
